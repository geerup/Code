// Package hub coordinates connected clients and the authoritative game loop.
// It's transport-agnostic: a Client is anything that can receive bytes, so the
// hub is unit-tested with fake clients (no WebSocket needed).
package hub

import (
	"encoding/json"
	"sync"
	"time"

	"github.com/portfolio/arena/internal/game"
)

// Client is one connected participant's outbound channel.
type Client interface {
	ID() string
	Name() string
	Send(b []byte)
}

// Hub owns the world and the set of clients.
type Hub struct {
	mu      sync.Mutex
	world   *game.World
	clients map[string]Client
}

func New(world *game.World) *Hub {
	return &Hub{world: world, clients: map[string]Client{}}
}

// Register adds a client and joins them to the world.
func (h *Hub) Register(c Client) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.clients[c.ID()] = c
	h.world.Join(c.ID(), c.Name())
}

// Unregister removes a client from the world.
func (h *Hub) Unregister(id string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	delete(h.clients, id)
	h.world.Leave(id)
}

// Input forwards a movement command to the world.
func (h *Hub) Input(id string, dx, dy float64) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.world.Input(id, dx, dy)
}

// ClientCount reports the number of connected clients.
func (h *Hub) ClientCount() int {
	h.mu.Lock()
	defer h.mu.Unlock()
	return len(h.clients)
}

// snapshot serializes the current world for clients.
func (h *Hub) snapshot() []byte {
	b, _ := json.Marshal(map[string]any{"type": "state", "world": h.world})
	return b
}

// Tick advances the simulation by dt and broadcasts the new state. Exposed so
// tests can drive the loop deterministically.
func (h *Hub) Tick(dt float64) {
	h.mu.Lock()
	h.world.Step(dt)
	b := h.snapshot()
	clients := make([]Client, 0, len(h.clients))
	for _, c := range h.clients {
		clients = append(clients, c)
	}
	h.mu.Unlock()
	for _, c := range clients {
		c.Send(b)
	}
}

// Run drives the game loop at `hz` ticks per second until stop is closed.
func (h *Hub) Run(hz int, stop <-chan struct{}) {
	if hz <= 0 {
		hz = 30
	}
	dt := 1.0 / float64(hz)
	ticker := time.NewTicker(time.Second / time.Duration(hz))
	defer ticker.Stop()
	for {
		select {
		case <-stop:
			return
		case <-ticker.C:
			h.Tick(dt)
		}
	}
}
