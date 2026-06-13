package hub

import (
	"encoding/json"
	"sync"
	"testing"

	"github.com/portfolio/arena/internal/game"
)

// fakeClient records the last message it received.
type fakeClient struct {
	id, name string
	mu       sync.Mutex
	last     []byte
	count    int
}

func (f *fakeClient) ID() string   { return f.id }
func (f *fakeClient) Name() string { return f.name }
func (f *fakeClient) Send(b []byte) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.last = b
	f.count++
}

func TestRegisterJoinsWorldAndCountsClients(t *testing.T) {
	h := New(game.NewWorld(800, 600, 3, 1))
	c := &fakeClient{id: "p1", name: "ann"}
	h.Register(c)
	if h.ClientCount() != 1 {
		t.Fatalf("want 1 client, got %d", h.ClientCount())
	}
}

func TestTickBroadcastsStateToClients(t *testing.T) {
	h := New(game.NewWorld(800, 600, 1, 1))
	c := &fakeClient{id: "p1", name: "ann"}
	h.Register(c)
	h.Tick(0.016)
	if c.count == 0 || c.last == nil {
		t.Fatal("client should have received a state broadcast")
	}
	var msg struct {
		Type  string `json:"type"`
		World struct {
			Players map[string]game.Player `json:"players"`
		} `json:"world"`
	}
	if err := json.Unmarshal(c.last, &msg); err != nil {
		t.Fatal(err)
	}
	if msg.Type != "state" {
		t.Errorf("want type 'state', got %q", msg.Type)
	}
	if _, ok := msg.World.Players["p1"]; !ok {
		t.Error("broadcast should include the registered player")
	}
}

func TestUnregisterStopsBroadcasts(t *testing.T) {
	h := New(game.NewWorld(800, 600, 1, 1))
	c := &fakeClient{id: "p1", name: "ann"}
	h.Register(c)
	h.Unregister("p1")
	h.Tick(0.016)
	if c.count != 0 {
		t.Error("unregistered client should not receive broadcasts")
	}
	if h.ClientCount() != 0 {
		t.Error("client count should be 0 after unregister")
	}
}

func TestInputMovesPlayerOverTicks(t *testing.T) {
	h := New(game.NewWorld(800, 600, 0, 1))
	c := &fakeClient{id: "p1", name: "ann"}
	h.Register(c)
	h.Input("p1", 1, 0) // move right
	for i := 0; i < 5; i++ {
		h.Tick(0.1)
	}
	var msg struct {
		World struct {
			Players map[string]game.Player `json:"players"`
		} `json:"world"`
	}
	_ = json.Unmarshal(c.last, &msg)
	if msg.World.Players["p1"].Pos.X == 0 {
		t.Error("player should have moved right over several ticks")
	}
}
