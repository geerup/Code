package limiter

import (
	"testing"
	"time"
)

func TestBurstThenBlock(t *testing.T) {
	now := time.Unix(0, 0)
	l := New(3, 1) // burst 3, 1 token/sec
	l.SetClock(func() time.Time { return now })

	for i := 0; i < 3; i++ {
		if !l.Allow("ip1") {
			t.Fatalf("request %d within burst should be allowed", i)
		}
	}
	if l.Allow("ip1") {
		t.Error("4th request should be blocked (burst exhausted)")
	}
}

func TestRefillOverTime(t *testing.T) {
	now := time.Unix(0, 0)
	l := New(2, 1) // 1 token/sec
	l.SetClock(func() time.Time { return now })

	l.Allow("ip"); l.Allow("ip") // drain
	if l.Allow("ip") {
		t.Fatal("should be blocked when empty")
	}
	now = now.Add(1 * time.Second) // +1 token
	if !l.Allow("ip") {
		t.Error("should be allowed after 1s refill")
	}
	if l.Allow("ip") {
		t.Error("only one token should have refilled")
	}
}

func TestRefillCapsAtBurst(t *testing.T) {
	now := time.Unix(0, 0)
	l := New(5, 10)
	l.SetClock(func() time.Time { return now })
	now = now.Add(100 * time.Second) // huge elapsed time
	if got := l.Tokens("ip"); got != 5 {
		t.Errorf("tokens should cap at burst 5, got %v", got)
	}
}

func TestKeysAreIndependent(t *testing.T) {
	now := time.Unix(0, 0)
	l := New(1, 1)
	l.SetClock(func() time.Time { return now })
	if !l.Allow("a") {
		t.Fatal("a first request allowed")
	}
	if !l.Allow("b") {
		t.Error("b should have its own bucket")
	}
	if l.Allow("a") {
		t.Error("a should now be blocked")
	}
}
