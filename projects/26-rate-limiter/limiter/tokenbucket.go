// Package limiter implements token-bucket rate limiting. A bucket refills at a
// steady rate up to a burst capacity; each request takes one token. The clock
// is injectable so refill behavior is tested deterministically (no sleeps).
package limiter

import (
	"sync"
	"time"
)

// Bucket is a single token bucket.
type Bucket struct {
	capacity   float64
	refillRate float64 // tokens per second
	tokens     float64
	last       time.Time
}

// TokenBucket is a keyed set of buckets (e.g. one per client/IP).
type TokenBucket struct {
	mu         sync.Mutex
	capacity   float64
	refillRate float64
	buckets    map[string]*Bucket
	now        func() time.Time
}

// New creates a limiter allowing `burst` tokens with `ratePerSec` refill.
func New(burst, ratePerSec float64) *TokenBucket {
	return &TokenBucket{
		capacity:   burst,
		refillRate: ratePerSec,
		buckets:    map[string]*Bucket{},
		now:        time.Now,
	}
}

// SetClock overrides the time source (for tests).
func (t *TokenBucket) SetClock(fn func() time.Time) { t.now = fn }

// Allow reports whether a request for `key` may proceed, consuming a token if so.
func (t *TokenBucket) Allow(key string) bool {
	return t.AllowN(key, 1)
}

// AllowN attempts to consume n tokens for key.
func (t *TokenBucket) AllowN(key string, n float64) bool {
	t.mu.Lock()
	defer t.mu.Unlock()
	now := t.now()
	b := t.buckets[key]
	if b == nil {
		b = &Bucket{capacity: t.capacity, refillRate: t.refillRate, tokens: t.capacity, last: now}
		t.buckets[key] = b
	}
	// Refill based on elapsed time.
	elapsed := now.Sub(b.last).Seconds()
	if elapsed > 0 {
		b.tokens = minF(b.capacity, b.tokens+elapsed*b.refillRate)
		b.last = now
	}
	if b.tokens >= n {
		b.tokens -= n
		return true
	}
	return false
}

// Tokens returns the current token count for a key (for introspection/tests).
func (t *TokenBucket) Tokens(key string) float64 {
	t.mu.Lock()
	defer t.mu.Unlock()
	if b := t.buckets[key]; b != nil {
		return b.tokens
	}
	return t.capacity
}

func minF(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
