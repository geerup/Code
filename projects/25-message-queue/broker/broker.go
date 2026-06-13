// Package broker is an in-memory message queue with SQS-style semantics:
// publish to a topic, consume a message (which becomes "in-flight" with a
// visibility timeout), and ack it. Un-acked messages are redelivered after the
// timeout, giving at-least-once delivery. Time is injected so redelivery is
// tested deterministically.
package broker

import (
	"errors"
	"sync"
	"time"
)

var ErrEmpty = errors.New("broker: no messages available")

// Message is a queued payload.
type Message struct {
	ID      uint64
	Topic   string
	Body    []byte
	Deliveries int // how many times it has been handed to a consumer
}

type inflight struct {
	msg      Message
	deadline time.Time
}

type topic struct {
	ready    []Message            // FIFO queue of deliverable messages
	inflight map[uint64]*inflight // delivered-but-not-acked
}

// Broker holds all topics. Safe for concurrent use.
type Broker struct {
	mu      sync.Mutex
	topics  map[string]*topic
	nextID  uint64
	visTimeout time.Duration
	now     func() time.Time // injectable clock
}

// New returns a broker with the given visibility timeout.
func New(visibilityTimeout time.Duration) *Broker {
	return &Broker{
		topics:     map[string]*topic{},
		visTimeout: visibilityTimeout,
		now:        time.Now,
	}
}

// SetClock overrides the time source (for tests).
func (b *Broker) SetClock(fn func() time.Time) { b.now = fn }

func (b *Broker) topicFor(name string) *topic {
	t := b.topics[name]
	if t == nil {
		t = &topic{inflight: map[uint64]*inflight{}}
		b.topics[name] = t
	}
	return t
}

// Publish enqueues a message and returns its id.
func (b *Broker) Publish(topicName string, body []byte) uint64 {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.nextID++
	id := b.nextID
	t := b.topicFor(topicName)
	t.ready = append(t.ready, Message{ID: id, Topic: topicName, Body: append([]byte(nil), body...)})
	return id
}

// Consume delivers the next ready message and marks it in-flight. Before
// delivering, it requeues any in-flight messages whose visibility timeout has
// elapsed (redelivery).
func (b *Broker) Consume(topicName string) (Message, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	t := b.topicFor(topicName)
	b.requeueExpired(t)

	if len(t.ready) == 0 {
		return Message{}, ErrEmpty
	}
	msg := t.ready[0]
	t.ready = t.ready[1:]
	msg.Deliveries++
	t.inflight[msg.ID] = &inflight{msg: msg, deadline: b.now().Add(b.visTimeout)}
	return msg, nil
}

// Ack confirms processing; the message is removed permanently. Returns true if
// the message was in-flight (a late ack after redelivery returns false).
func (b *Broker) Ack(topicName string, id uint64) bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	t := b.topicFor(topicName)
	if _, ok := t.inflight[id]; ok {
		delete(t.inflight, id)
		return true
	}
	return false
}

// requeueExpired moves timed-out in-flight messages back to ready (FIFO front
// so they're retried promptly). Caller holds the lock.
func (b *Broker) requeueExpired(t *topic) {
	now := b.now()
	for id, f := range t.inflight {
		if !now.Before(f.deadline) {
			delete(t.inflight, id)
			t.ready = append([]Message{f.msg}, t.ready...)
		}
	}
}

// Stats reports queue depth for a topic.
func (b *Broker) Stats(topicName string) (ready, inFlight int) {
	b.mu.Lock()
	defer b.mu.Unlock()
	t := b.topicFor(topicName)
	b.requeueExpired(t)
	return len(t.ready), len(t.inflight)
}
