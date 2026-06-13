package game

import (
	"math"
	"testing"
)

func TestJoinPlacesPlayerInBounds(t *testing.T) {
	w := NewWorld(800, 600, 5, 1)
	p := w.Join("p1", "ann")
	if p.Pos.X < 0 || p.Pos.X > w.Width || p.Pos.Y < 0 || p.Pos.Y > w.Height {
		t.Fatalf("player spawned out of bounds: %+v", p.Pos)
	}
	if len(w.Players) != 1 {
		t.Fatalf("want 1 player, got %d", len(w.Players))
	}
}

func TestInputIsNormalized(t *testing.T) {
	w := NewWorld(800, 600, 0, 1)
	w.Join("p1", "ann")
	w.Players["p1"].Pos = Vec{X: 400, Y: 300}
	w.Input("p1", 1, 1) // diagonal
	w.Step(1.0)
	moved := math.Hypot(w.Players["p1"].Pos.X-400, w.Players["p1"].Pos.Y-300)
	if math.Abs(moved-Speed) > 1e-6 {
		t.Errorf("diagonal speed should equal Speed (%v), moved %v", Speed, moved)
	}
}

func TestStepClampsToBounds(t *testing.T) {
	w := NewWorld(100, 100, 0, 1)
	w.Join("p1", "ann")
	w.Players["p1"].Pos = Vec{X: 90, Y: 90}
	w.Input("p1", 1, 1)
	w.Step(10) // way past the wall
	p := w.Players["p1"]
	if p.Pos.X != 100 || p.Pos.Y != 100 {
		t.Errorf("expected clamp to (100,100), got %+v", p.Pos)
	}
}

func TestCoinPickupScoresAndRespawns(t *testing.T) {
	w := NewWorld(800, 600, 1, 1)
	w.Join("p1", "ann")
	// Place player exactly on the coin.
	w.Players["p1"].Pos = w.Coins[0].Pos
	oldID := w.Coins[0].ID
	w.Step(0.016)
	if w.Players["p1"].Score != 1 {
		t.Errorf("want score 1, got %d", w.Players["p1"].Score)
	}
	if len(w.Coins) != 1 {
		t.Errorf("coin count should stay 1, got %d", len(w.Coins))
	}
	if w.Coins[0].ID == oldID {
		t.Error("collected coin should respawn with a new id")
	}
}

func TestDeterministicFromSeed(t *testing.T) {
	a := NewWorld(800, 600, 10, 42)
	b := NewWorld(800, 600, 10, 42)
	for i := range a.Coins {
		if a.Coins[i].Pos != b.Coins[i].Pos {
			t.Fatalf("coin %d differs between same-seed worlds", i)
		}
	}
}

func TestLeaveRemovesPlayer(t *testing.T) {
	w := NewWorld(800, 600, 0, 1)
	w.Join("p1", "ann")
	w.Leave("p1")
	if _, ok := w.Players["p1"]; ok {
		t.Error("player should be removed")
	}
}
