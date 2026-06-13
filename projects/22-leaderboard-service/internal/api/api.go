package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/portfolio/leaderboard/internal/store"
)

// Server wires HTTP handlers to a Store. Secret enables HMAC verification when
// non-empty (set to "" to disable, e.g. for local play).
type Server struct {
	Store  store.Store
	Secret string
}

func New(s store.Store, secret string) *Server { return &Server{Store: s, Secret: secret} }

// Routes returns the configured mux.
func (s *Server) Routes() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.health)
	mux.HandleFunc("POST /scores", s.submit)
	mux.HandleFunc("GET /leaderboard/{game}", s.leaderboard)
	mux.HandleFunc("POST /achievements", s.unlock)
	mux.HandleFunc("GET /achievements/{player}", s.listAchievements)
	return mux
}

type submitReq struct {
	Player    string `json:"player"`
	Game      string `json:"game"`
	Points    int64  `json:"points"`
	Signature string `json:"signature"`
}

func (s *Server) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

func (s *Server) submit(w http.ResponseWriter, r *http.Request) {
	var req submitReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errBody("invalid json"))
		return
	}
	if s.Secret != "" && !Verify(s.Secret, req.Player, req.Game, req.Points, req.Signature) {
		writeJSON(w, http.StatusUnauthorized, errBody("invalid signature"))
		return
	}
	if err := s.Store.Submit(store.Score{Player: req.Player, Game: req.Game, Points: req.Points}); err != nil {
		writeJSON(w, http.StatusBadRequest, errBody(err.Error()))
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{"ok": true})
}

func (s *Server) leaderboard(w http.ResponseWriter, r *http.Request) {
	game := r.PathValue("game")
	limit := 10
	if l := r.URL.Query().Get("limit"); l != "" {
		if n, err := strconv.Atoi(l); err == nil && n > 0 {
			limit = n
		}
	}
	scores, err := s.Store.Top(game, limit)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errBody(err.Error()))
		return
	}
	if scores == nil {
		scores = []store.Score{}
	}
	writeJSON(w, http.StatusOK, map[string]any{"game": game, "scores": scores})
}

type unlockReq struct {
	Player string `json:"player"`
	Key    string `json:"key"`
}

func (s *Server) unlock(w http.ResponseWriter, r *http.Request) {
	var req unlockReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errBody("invalid json"))
		return
	}
	isNew, err := s.Store.Unlock(store.Achievement{Player: req.Player, Key: req.Key})
	if err != nil {
		writeJSON(w, http.StatusBadRequest, errBody(err.Error()))
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"unlocked": isNew})
}

func (s *Server) listAchievements(w http.ResponseWriter, r *http.Request) {
	list, err := s.Store.Achievements(r.PathValue("player"))
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errBody(err.Error()))
		return
	}
	if list == nil {
		list = []store.Achievement{}
	}
	writeJSON(w, http.StatusOK, map[string]any{"achievements": list})
}

func writeJSON(w http.ResponseWriter, code int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(body)
}

func errBody(msg string) map[string]any { return map[string]any{"error": msg} }
