package store

import "testing"

func TestSubmitKeepsBestPerPlayer(t *testing.T) {
	m := NewMemory()
	_ = m.Submit(Score{Player: "ann", Game: "snake", Points: 100})
	_ = m.Submit(Score{Player: "ann", Game: "snake", Points: 50}) // lower, ignored
	_ = m.Submit(Score{Player: "ann", Game: "snake", Points: 250})
	best, err := m.Best("snake", "ann")
	if err != nil {
		t.Fatal(err)
	}
	if best.Points != 250 {
		t.Errorf("want best 250, got %d", best.Points)
	}
}

func TestTopOrdersDescendingAndLimits(t *testing.T) {
	m := NewMemory()
	_ = m.Submit(Score{Player: "a", Game: "g", Points: 10})
	_ = m.Submit(Score{Player: "b", Game: "g", Points: 30})
	_ = m.Submit(Score{Player: "c", Game: "g", Points: 20})
	_ = m.Submit(Score{Player: "d", Game: "other", Points: 99}) // different game
	top, _ := m.Top("g", 2)
	if len(top) != 2 {
		t.Fatalf("want 2, got %d", len(top))
	}
	if top[0].Player != "b" || top[1].Player != "c" {
		t.Errorf("wrong order: %v", top)
	}
}

func TestSubmitValidation(t *testing.T) {
	m := NewMemory()
	if err := m.Submit(Score{Game: "g", Points: 1}); err == nil {
		t.Error("expected error for missing player")
	}
}

func TestUnlockIsIdempotent(t *testing.T) {
	m := NewMemory()
	first, _ := m.Unlock(Achievement{Player: "ann", Key: "first-win"})
	second, _ := m.Unlock(Achievement{Player: "ann", Key: "first-win"})
	if !first {
		t.Error("first unlock should be new")
	}
	if second {
		t.Error("second unlock should not be new")
	}
	list, _ := m.Achievements("ann")
	if len(list) != 1 {
		t.Errorf("want 1 achievement, got %d", len(list))
	}
}

func TestBestNotFound(t *testing.T) {
	if _, err := NewMemory().Best("g", "nobody"); err != ErrNotFound {
		t.Errorf("want ErrNotFound, got %v", err)
	}
}
