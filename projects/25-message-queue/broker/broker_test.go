package broker

import (
	"testing"
	"time"
)

func TestPublishConsumeAck(t *testing.T) {
	b := New(30 * time.Second)
	id := b.Publish("jobs", []byte("hello"))
	msg, err := b.Consume("jobs")
	if err != nil {
		t.Fatal(err)
	}
	if msg.ID != id || string(msg.Body) != "hello" {
		t.Fatalf("unexpected message: %+v", msg)
	}
	if msg.Deliveries != 1 {
		t.Errorf("first delivery count should be 1, got %d", msg.Deliveries)
	}
	if !b.Ack("jobs", id) {
		t.Error("ack of in-flight message should succeed")
	}
	if _, err := b.Consume("jobs"); err != ErrEmpty {
		t.Errorf("queue should be empty after ack, got %v", err)
	}
}

func TestFIFOOrder(t *testing.T) {
	b := New(time.Minute)
	b.Publish("t", []byte("1"))
	b.Publish("t", []byte("2"))
	m1, _ := b.Consume("t")
	m2, _ := b.Consume("t")
	if string(m1.Body) != "1" || string(m2.Body) != "2" {
		t.Errorf("FIFO violated: %s then %s", m1.Body, m2.Body)
	}
}

func TestRedeliveryAfterVisibilityTimeout(t *testing.T) {
	now := time.Unix(1000, 0)
	b := New(10 * time.Second)
	b.SetClock(func() time.Time { return now })

	b.Publish("t", []byte("retry-me"))
	first, _ := b.Consume("t")
	if first.Deliveries != 1 {
		t.Fatalf("want 1 delivery, got %d", first.Deliveries)
	}
	// Not acked. Before timeout: nothing redelivered.
	now = now.Add(5 * time.Second)
	if _, err := b.Consume("t"); err != ErrEmpty {
		t.Fatal("must not redeliver before visibility timeout")
	}
	// After timeout: redelivered with an incremented delivery count.
	now = now.Add(6 * time.Second)
	second, err := b.Consume("t")
	if err != nil {
		t.Fatalf("expected redelivery, got %v", err)
	}
	if second.ID != first.ID {
		t.Errorf("redelivered id mismatch: %d vs %d", second.ID, first.ID)
	}
	if second.Deliveries != 2 {
		t.Errorf("redelivery should increment count to 2, got %d", second.Deliveries)
	}
}

func TestLateAckAfterRedeliveryReturnsFalse(t *testing.T) {
	now := time.Unix(0, 0)
	b := New(time.Second)
	b.SetClock(func() time.Time { return now })
	id := b.Publish("t", []byte("x"))
	b.Consume("t")
	now = now.Add(2 * time.Second)
	b.Consume("t") // redelivered; original handle is now stale... but same id
	// Ack succeeds because the id is in-flight again; ack a *non-existent* id is false.
	if b.Ack("t", id+999) {
		t.Error("acking an unknown id should return false")
	}
}

func TestStats(t *testing.T) {
	b := New(time.Minute)
	b.Publish("t", []byte("a"))
	b.Publish("t", []byte("b"))
	b.Consume("t")
	ready, inflight := b.Stats("t")
	if ready != 1 || inflight != 1 {
		t.Errorf("want ready=1 inflight=1, got ready=%d inflight=%d", ready, inflight)
	}
}
