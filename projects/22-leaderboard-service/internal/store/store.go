// Package store holds leaderboard entries and unlocked achievements. It defines
// a Store interface with an in-memory implementation, so the API is testable
// without a database; a Postgres implementation can be dropped in later.
package store

import (
	"errors"
	"sort"
	"sync"
	"time"
)

var ErrNotFound = errors.New("not found")

// Score is a single submitted result.
type Score struct {
	Player    string    `json:"player"`
	Game      string    `json:"game"`
	Points    int64     `json:"points"`
	CreatedAt time.Time `json:"created_at"`
}

// Achievement is a badge a player has unlocked.
type Achievement struct {
	Player     string    `json:"player"`
	Key        string    `json:"key"`
	UnlockedAt time.Time `json:"unlocked_at"`
}

// Store is the persistence boundary.
type Store interface {
	Submit(s Score) error
	Top(game string, n int) ([]Score, error)
	Best(game, player string) (Score, error)
	Unlock(a Achievement) (bool, error) // bool = newly unlocked
	Achievements(player string) ([]Achievement, error)
}

// Memory is a concurrency-safe in-memory Store.
type Memory struct {
	mu           sync.RWMutex
	best         map[string]Score          // key: game|player -> best score
	achievements map[string]map[string]Achievement // player -> key -> ach
}

func NewMemory() *Memory {
	return &Memory{
		best:         make(map[string]Score),
		achievements: make(map[string]map[string]Achievement),
	}
}

func key(game, player string) string { return game + "|" + player }

// Submit records a score, keeping only the player's best per game.
func (m *Memory) Submit(s Score) error {
	if s.Player == "" || s.Game == "" {
		return errors.New("player and game are required")
	}
	if s.CreatedAt.IsZero() {
		s.CreatedAt = time.Now().UTC()
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	k := key(s.Game, s.Player)
	if cur, ok := m.best[k]; !ok || s.Points > cur.Points {
		m.best[k] = s
	}
	return nil
}

// Top returns the n highest scores for a game, descending.
func (m *Memory) Top(game string, n int) ([]Score, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	var scores []Score
	for k, s := range m.best {
		if s.Game == game {
			_ = k
			scores = append(scores, s)
		}
	}
	sort.Slice(scores, func(i, j int) bool {
		if scores[i].Points != scores[j].Points {
			return scores[i].Points > scores[j].Points
		}
		return scores[i].CreatedAt.Before(scores[j].CreatedAt) // earlier wins ties
	})
	if n > 0 && len(scores) > n {
		scores = scores[:n]
	}
	return scores, nil
}

// Best returns a player's best score in a game.
func (m *Memory) Best(game, player string) (Score, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if s, ok := m.best[key(game, player)]; ok {
		return s, nil
	}
	return Score{}, ErrNotFound
}

// Unlock records an achievement; returns true if it was newly unlocked.
func (m *Memory) Unlock(a Achievement) (bool, error) {
	if a.Player == "" || a.Key == "" {
		return false, errors.New("player and key are required")
	}
	if a.UnlockedAt.IsZero() {
		a.UnlockedAt = time.Now().UTC()
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.achievements[a.Player] == nil {
		m.achievements[a.Player] = make(map[string]Achievement)
	}
	if _, exists := m.achievements[a.Player][a.Key]; exists {
		return false, nil
	}
	m.achievements[a.Player][a.Key] = a
	return true, nil
}

// Achievements lists a player's unlocked badges.
func (m *Memory) Achievements(player string) ([]Achievement, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	var out []Achievement
	for _, a := range m.achievements[player] {
		out = append(out, a)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Key < out[j].Key })
	return out, nil
}
