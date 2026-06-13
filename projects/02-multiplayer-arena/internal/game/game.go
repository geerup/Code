// Package game is the authoritative, transport-free simulation for a real-time
// multiplayer coin-collection arena. The server owns one World, applies player
// inputs, and ticks at a fixed rate. Keeping it pure makes the netcode-critical
// logic deterministic and unit-testable.
package game

import "math"

const (
	PlayerRadius = 12.0
	CoinRadius   = 8.0
	Speed        = 180.0 // units per second
)

// Vec is a 2D vector.
type Vec struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

// Player is one connected participant.
type Player struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Pos   Vec    `json:"pos"`
	dir   Vec    // desired movement direction (unit-ish), from input
	Score int    `json:"score"`
}

// Coin is a pickup.
type Coin struct {
	ID  int `json:"id"`
	Pos Vec `json:"pos"`
}

// World is the whole game state.
type World struct {
	Width   float64            `json:"width"`
	Height  float64            `json:"height"`
	Players map[string]*Player `json:"players"`
	Coins   []Coin             `json:"coins"`
	nextCID int
	rng     *rng
}

// NewWorld builds an empty arena with `coins` pickups from a seed.
func NewWorld(width, height float64, coins int, seed uint64) *World {
	w := &World{Width: width, Height: height, Players: map[string]*Player{}, rng: newRNG(seed)}
	for i := 0; i < coins; i++ {
		w.spawnCoin()
	}
	return w
}

func (w *World) spawnCoin() {
	w.Coins = append(w.Coins, Coin{
		ID:  w.nextCID,
		Pos: Vec{X: w.rng.float() * w.Width, Y: w.rng.float() * w.Height},
	})
	w.nextCID++
}

// Join adds a player at a pseudo-random position and returns it.
func (w *World) Join(id, name string) *Player {
	p := &Player{ID: id, Name: name, Pos: Vec{X: w.rng.float() * w.Width, Y: w.rng.float() * w.Height}}
	w.Players[id] = p
	return p
}

// Leave removes a player.
func (w *World) Leave(id string) { delete(w.Players, id) }

// Input sets a player's desired direction; it's normalized so diagonal movement
// isn't faster than orthogonal.
func (w *World) Input(id string, dx, dy float64) {
	p, ok := w.Players[id]
	if !ok {
		return
	}
	mag := math.Hypot(dx, dy)
	if mag == 0 {
		p.dir = Vec{}
		return
	}
	p.dir = Vec{X: dx / mag, Y: dy / mag}
}

// Step advances the simulation by dt seconds: move players, clamp to bounds,
// resolve coin pickups (respawning collected coins so the arena stays full).
func (w *World) Step(dt float64) {
	for _, p := range w.Players {
		p.Pos.X = clamp(p.Pos.X+p.dir.X*Speed*dt, 0, w.Width)
		p.Pos.Y = clamp(p.Pos.Y+p.dir.Y*Speed*dt, 0, w.Height)
	}
	for i := 0; i < len(w.Coins); i++ {
		for _, p := range w.Players {
			if dist(p.Pos, w.Coins[i].Pos) <= PlayerRadius+CoinRadius {
				p.Score++
				// Respawn this coin at a new spot.
				w.Coins[i].Pos = Vec{X: w.rng.float() * w.Width, Y: w.rng.float() * w.Height}
				w.Coins[i].ID = w.nextCID
				w.nextCID++
				break
			}
		}
	}
}

func clamp(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func dist(a, b Vec) float64 { return math.Hypot(a.X-b.X, a.Y-b.Y) }

// rng is a small deterministic PRNG (xorshift64) so seeds reproduce.
type rng struct{ s uint64 }

func newRNG(seed uint64) *rng {
	if seed == 0 {
		seed = 0x9E3779B97F4A7C15
	}
	return &rng{s: seed}
}

func (r *rng) next() uint64 {
	r.s ^= r.s << 13
	r.s ^= r.s >> 7
	r.s ^= r.s << 17
	return r.s
}

// float returns a value in [0, 1).
func (r *rng) float() float64 { return float64(r.next()>>11) / float64(1<<53) }
