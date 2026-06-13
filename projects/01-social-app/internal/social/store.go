// Package social is the domain core of a small social app: users, follows,
// posts, likes, and a home feed. It's an in-memory, concurrency-safe store
// behind an interface so the HTTP layer is testable and a Postgres impl can be
// added later. This is a "niche" microblog — short posts, follow graph, feed.
package social

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"sort"
	"sync"
	"time"
)

var (
	ErrUserExists   = errors.New("username taken")
	ErrNoUser       = errors.New("no such user")
	ErrBadPassword  = errors.New("invalid credentials")
	ErrPostTooLong  = errors.New("post exceeds 280 characters")
	ErrEmptyPost    = errors.New("post is empty")
)

const MaxPostLen = 280

type User struct {
	ID       string `json:"id"`
	Username string `json:"username"`
	salt     string
	hash     string
}

type Post struct {
	ID        string    `json:"id"`
	AuthorID  string    `json:"author_id"`
	Author    string    `json:"author"`
	Text      string    `json:"text"`
	CreatedAt time.Time `json:"created_at"`
	Likes     int       `json:"likes"`
	LikedByMe bool      `json:"liked_by_me"`
}

// Store is the persistence boundary.
type Store struct {
	mu       sync.RWMutex
	users    map[string]*User            // id -> user
	byName   map[string]*User            // username -> user
	posts    map[string]*Post            // id -> post
	order    []string                    // post ids, append order
	follows  map[string]map[string]bool  // follower -> set(followee)
	likes    map[string]map[string]bool  // postID -> set(userID)
	seq      int
}

func NewStore() *Store {
	return &Store{
		users:   map[string]*User{},
		byName:  map[string]*User{},
		posts:   map[string]*Post{},
		follows: map[string]map[string]bool{},
		likes:   map[string]map[string]bool{},
	}
}

func (s *Store) id(prefix string) string {
	s.seq++
	return prefix + "_" + hex.EncodeToString([]byte{byte(s.seq >> 8), byte(s.seq)}) + "_" + randHex(4)
}

// Register creates a new user with a salted password hash.
func (s *Store) Register(username, password string) (*User, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.byName[username]; ok {
		return nil, ErrUserExists
	}
	salt := randHex(8)
	u := &User{ID: s.id("u"), Username: username, salt: salt, hash: hashPassword(password, salt)}
	s.users[u.ID] = u
	s.byName[username] = u
	return u, nil
}

// Authenticate verifies credentials and returns the user.
func (s *Store) Authenticate(username, password string) (*User, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	u, ok := s.byName[username]
	if !ok {
		return nil, ErrNoUser
	}
	if hashPassword(password, u.salt) != u.hash {
		return nil, ErrBadPassword
	}
	return u, nil
}

// Follow makes follower follow followee (idempotent; can't follow yourself).
func (s *Store) Follow(followerID, followeeID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if followerID == followeeID {
		return errors.New("cannot follow yourself")
	}
	if _, ok := s.users[followeeID]; !ok {
		return ErrNoUser
	}
	if s.follows[followerID] == nil {
		s.follows[followerID] = map[string]bool{}
	}
	s.follows[followerID][followeeID] = true
	return nil
}

func (s *Store) Unfollow(followerID, followeeID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if set := s.follows[followerID]; set != nil {
		delete(set, followeeID)
	}
}

// CreatePost adds a post by a user.
func (s *Store) CreatePost(authorID, text string) (*Post, error) {
	if len(text) == 0 {
		return nil, ErrEmptyPost
	}
	if len(text) > MaxPostLen {
		return nil, ErrPostTooLong
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	author, ok := s.users[authorID]
	if !ok {
		return nil, ErrNoUser
	}
	p := &Post{ID: s.id("p"), AuthorID: authorID, Author: author.Username, Text: text, CreatedAt: time.Now().UTC()}
	s.posts[p.ID] = p
	s.order = append(s.order, p.ID)
	return p, nil
}

// Like toggles a like; returns the new like state.
func (s *Store) Like(userID, postID string) (bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	p, ok := s.posts[postID]
	if !ok {
		return false, errors.New("no such post")
	}
	if s.likes[postID] == nil {
		s.likes[postID] = map[string]bool{}
	}
	liked := s.likes[postID][userID]
	if liked {
		delete(s.likes[postID], userID)
		p.Likes--
		return false, nil
	}
	s.likes[postID][userID] = true
	p.Likes++
	return true, nil
}

// Feed returns posts from the users `viewerID` follows (plus their own), newest
// first. This is the home timeline.
func (s *Store) Feed(viewerID string, limit int) []Post {
	s.mu.RLock()
	defer s.mu.RUnlock()
	visible := map[string]bool{viewerID: true}
	for followee := range s.follows[viewerID] {
		visible[followee] = true
	}
	var feed []Post
	for i := len(s.order) - 1; i >= 0; i-- {
		p := s.posts[s.order[i]]
		if visible[p.AuthorID] {
			copy := *p
			copy.LikedByMe = s.likes[p.ID][viewerID]
			feed = append(feed, copy)
			if limit > 0 && len(feed) >= limit {
				break
			}
		}
	}
	return feed
}

// Explore returns the most recent posts from everyone (discovery).
func (s *Store) Explore(viewerID string, limit int) []Post {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var out []Post
	for i := len(s.order) - 1; i >= 0 && (limit <= 0 || len(out) < limit); i-- {
		p := *s.posts[s.order[i]]
		p.LikedByMe = s.likes[p.ID][viewerID]
		out = append(out, p)
	}
	return out
}

// Followers/Following counts for a profile.
func (s *Store) Following(userID string) []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var out []string
	for f := range s.follows[userID] {
		out = append(out, f)
	}
	sort.Strings(out)
	return out
}

// --- helpers -----------------------------------------------------------------

func hashPassword(password, salt string) string {
	// NOTE: salted SHA-256 with stretching for the demo. Use bcrypt/argon2 in prod.
	h := []byte(salt + password)
	for i := 0; i < 50_000; i++ {
		sum := sha256.Sum256(h)
		h = sum[:]
	}
	return hex.EncodeToString(h)
}

func randHex(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
