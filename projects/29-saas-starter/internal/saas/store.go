package saas

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"sync"
)

var (
	ErrUserExists  = errors.New("email already registered")
	ErrNoUser      = errors.New("no such user")
	ErrBadPassword = errors.New("invalid credentials")
)

type User struct {
	ID    string `json:"id"`
	Email string `json:"email"`
	salt  string
	hash  string
}

// Store holds users, sessions, and subscriptions in memory (swap for Postgres).
type Store struct {
	mu       sync.RWMutex
	users    map[string]*User         // id -> user
	byEmail  map[string]*User         // email -> user
	sessions map[string]string        // token -> userID
	subs     map[string]*Subscription // userID -> subscription
	gateway  Gateway
	seq      int
}

func NewStore(gw Gateway) *Store {
	return &Store{
		users:    map[string]*User{},
		byEmail:  map[string]*User{},
		sessions: map[string]string{},
		subs:     map[string]*Subscription{},
		gateway:  gw,
	}
}

func (s *Store) Register(email, password string) (*User, string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.byEmail[email]; ok {
		return nil, "", ErrUserExists
	}
	s.seq++
	salt := randHex(8)
	u := &User{ID: "u_" + randHex(6), Email: email, salt: salt, hash: hashPW(password, salt)}
	s.users[u.ID] = u
	s.byEmail[email] = u
	// New users start on the free plan.
	s.subs[u.ID] = &Subscription{UserID: u.ID, PlanID: "free", Status: StatusActive}
	return u, s.newSession(u.ID), nil
}

func (s *Store) Login(email, password string) (*User, string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	u, ok := s.byEmail[email]
	if !ok {
		return nil, "", ErrNoUser
	}
	if hashPW(password, u.salt) != u.hash {
		return nil, "", ErrBadPassword
	}
	return u, s.newSession(u.ID), nil
}

func (s *Store) UserForToken(token string) (string, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	uid, ok := s.sessions[token]
	return uid, ok
}

func (s *Store) newSession(uid string) string {
	token := randHex(16)
	s.sessions[token] = uid
	return token
}

// Subscribe starts checkout via the gateway and records a pending subscription.
// It becomes active when the provider webhook confirms payment.
func (s *Store) Subscribe(userID, planID string) (*Subscription, error) {
	if _, ok := Plans[planID]; !ok {
		return nil, ErrUnknownPlan
	}
	stripeID, err := s.gateway.CreateCheckout(userID, planID)
	if err != nil {
		return nil, err
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	sub := &Subscription{UserID: userID, PlanID: planID, Status: StatusPastDue, StripeID: stripeID}
	s.subs[userID] = sub
	return sub, nil
}

// HandleWebhook applies a provider event (e.g. invoice.paid -> active,
// customer.subscription.deleted -> canceled). This is how billing state stays
// in sync with the payment provider.
func (s *Store) HandleWebhook(eventType, stripeID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, sub := range s.subs {
		if sub.StripeID != stripeID {
			continue
		}
		switch eventType {
		case "invoice.paid":
			sub.Status = StatusActive
		case "invoice.payment_failed":
			sub.Status = StatusPastDue
		case "customer.subscription.deleted":
			sub.Status = StatusCanceled
			sub.PlanID = "free"
		}
		return nil
	}
	return errors.New("no subscription for event")
}

func (s *Store) Subscription(userID string) Subscription {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if sub, ok := s.subs[userID]; ok {
		return *sub
	}
	return Subscription{UserID: userID, PlanID: "free", Status: StatusActive}
}

func hashPW(password, salt string) string {
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
