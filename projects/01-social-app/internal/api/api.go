// Package api exposes the social store over HTTP with token sessions and a
// Server-Sent Events stream so the feed updates in real time.
package api

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"sync"

	"github.com/portfolio/social/internal/social"
)

type Server struct {
	store    *social.Store
	mu       sync.RWMutex
	sessions map[string]string // token -> userID
	subs     map[chan []byte]bool
	subMu    sync.Mutex
}

func New(store *social.Store) *Server {
	return &Server{store: store, sessions: map[string]string{}, subs: map[chan []byte]bool{}}
}

func (s *Server) Routes() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/health", func(w http.ResponseWriter, _ *http.Request) { writeJSON(w, 200, map[string]bool{"ok": true}) })
	mux.HandleFunc("POST /api/register", s.register)
	mux.HandleFunc("POST /api/login", s.login)
	mux.HandleFunc("GET /api/me", s.auth(s.me))
	mux.HandleFunc("POST /api/posts", s.auth(s.createPost))
	mux.HandleFunc("POST /api/posts/{id}/like", s.auth(s.like))
	mux.HandleFunc("POST /api/follow/{id}", s.auth(s.follow))
	mux.HandleFunc("GET /api/feed", s.auth(s.feed))
	mux.HandleFunc("GET /api/explore", s.auth(s.explore))
	mux.HandleFunc("GET /api/events", s.auth(s.events))
	return mux
}

// --- auth middleware ----------------------------------------------------------

type ctxKey string

const userKey ctxKey = "uid"

func (s *Server) auth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := bearer(r)
		s.mu.RLock()
		uid, ok := s.sessions[token]
		s.mu.RUnlock()
		if !ok {
			writeJSON(w, http.StatusUnauthorized, errBody("not authenticated"))
			return
		}
		r = r.WithContext(contextWithUser(r, uid))
		next(w, r)
	}
}

func (s *Server) newSession(uid string) string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	token := hex.EncodeToString(b)
	s.mu.Lock()
	s.sessions[token] = uid
	s.mu.Unlock()
	return token
}

// --- handlers -----------------------------------------------------------------

type credentials struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func (s *Server) register(w http.ResponseWriter, r *http.Request) {
	var c credentials
	if err := json.NewDecoder(r.Body).Decode(&c); err != nil || c.Username == "" || c.Password == "" {
		writeJSON(w, http.StatusBadRequest, errBody("username and password required"))
		return
	}
	u, err := s.store.Register(c.Username, c.Password)
	if err != nil {
		writeJSON(w, http.StatusConflict, errBody(err.Error()))
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{"token": s.newSession(u.ID), "id": u.ID, "username": u.Username})
}

func (s *Server) login(w http.ResponseWriter, r *http.Request) {
	var c credentials
	if err := json.NewDecoder(r.Body).Decode(&c); err != nil {
		writeJSON(w, http.StatusBadRequest, errBody("invalid body"))
		return
	}
	u, err := s.store.Authenticate(c.Username, c.Password)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, errBody("invalid credentials"))
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"token": s.newSession(u.ID), "id": u.ID, "username": u.Username})
}

func (s *Server) me(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"id":        userID(r),
		"following": s.store.Following(userID(r)),
	})
}

func (s *Server) createPost(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Text string `json:"text"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, errBody("invalid body"))
		return
	}
	p, err := s.store.CreatePost(userID(r), body.Text)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, errBody(err.Error()))
		return
	}
	s.broadcast(p)
	writeJSON(w, http.StatusCreated, p)
}

func (s *Server) like(w http.ResponseWriter, r *http.Request) {
	liked, err := s.store.Like(userID(r), r.PathValue("id"))
	if err != nil {
		writeJSON(w, http.StatusNotFound, errBody(err.Error()))
		return
	}
	writeJSON(w, http.StatusOK, map[string]bool{"liked": liked})
}

func (s *Server) follow(w http.ResponseWriter, r *http.Request) {
	if err := s.store.Follow(userID(r), r.PathValue("id")); err != nil {
		writeJSON(w, http.StatusBadRequest, errBody(err.Error()))
		return
	}
	writeJSON(w, http.StatusOK, map[string]bool{"ok": true})
}

func (s *Server) feed(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"posts": s.store.Feed(userID(r), 50)})
}

func (s *Server) explore(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"posts": s.store.Explore(userID(r), 50)})
}

// events streams new posts via Server-Sent Events.
func (s *Server) events(w http.ResponseWriter, r *http.Request) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	ch := make(chan []byte, 8)
	s.subMu.Lock()
	s.subs[ch] = true
	s.subMu.Unlock()
	defer func() {
		s.subMu.Lock()
		delete(s.subs, ch)
		s.subMu.Unlock()
	}()

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	flusher.Flush()
	for {
		select {
		case <-r.Context().Done():
			return
		case msg := <-ch:
			w.Write([]byte("data: "))
			w.Write(msg)
			w.Write([]byte("\n\n"))
			flusher.Flush()
		}
	}
}

func (s *Server) broadcast(p *social.Post) {
	msg, _ := json.Marshal(p)
	s.subMu.Lock()
	defer s.subMu.Unlock()
	for ch := range s.subs {
		select {
		case ch <- msg:
		default:
		}
	}
}

// --- helpers ------------------------------------------------------------------

func bearer(r *http.Request) string {
	h := r.Header.Get("Authorization")
	if len(h) > 7 && h[:7] == "Bearer " {
		return h[7:]
	}
	return r.URL.Query().Get("token") // SSE can't set headers easily
}

func writeJSON(w http.ResponseWriter, code int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(body)
}

func errBody(msg string) map[string]string { return map[string]string{"error": msg} }
