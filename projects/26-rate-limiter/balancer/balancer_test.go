package balancer

import "testing"

func TestRoundRobinCycles(t *testing.T) {
	b := New(RoundRobin, "a", "b", "c")
	seen := []string{}
	for i := 0; i < 6; i++ {
		be, err := b.Next()
		if err != nil {
			t.Fatal(err)
		}
		seen = append(seen, be.URL)
	}
	// Each backend should be hit exactly twice over 6 picks.
	counts := map[string]int{}
	for _, u := range seen {
		counts[u]++
	}
	for _, u := range []string{"a", "b", "c"} {
		if counts[u] != 2 {
			t.Errorf("round-robin uneven: %s hit %d times (%v)", u, counts[u], seen)
		}
	}
}

func TestSkipsUnhealthy(t *testing.T) {
	b := New(RoundRobin, "a", "b", "c")
	b.Backends()[1].SetHealthy(false) // b is down
	for i := 0; i < 10; i++ {
		be, _ := b.Next()
		if be.URL == "b" {
			t.Fatal("must not route to an unhealthy backend")
		}
	}
}

func TestNoHealthyBackendErrors(t *testing.T) {
	b := New(RoundRobin, "a")
	b.Backends()[0].SetHealthy(false)
	if _, err := b.Next(); err != ErrNoBackend {
		t.Errorf("want ErrNoBackend, got %v", err)
	}
}

func TestLeastConnPicksLowest(t *testing.T) {
	b := New(LeastConn, "a", "b")
	// Acquire two connections on "a" (the first pick).
	be1, rel1, _ := b.Acquire()
	if be1.URL != "a" {
		t.Fatalf("first acquire should be a, got %s", be1.URL)
	}
	// Now "a" has 1 conn; least-conn should choose "b".
	be2, _, _ := b.Acquire()
	if be2.URL != "b" {
		t.Errorf("least-conn should pick idle backend b, got %s", be2.URL)
	}
	rel1()
	if be1.Conns() != 0 {
		t.Errorf("release should decrement conns, got %d", be1.Conns())
	}
}
