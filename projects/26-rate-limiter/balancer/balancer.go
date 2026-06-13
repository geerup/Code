// Package balancer is a tiny load balancer: it picks healthy backends using
// round-robin or least-connections, and tracks health so dead backends are
// skipped. Backend selection is pure logic, unit-tested without real servers.
package balancer

import (
	"errors"
	"sync"
	"sync/atomic"
)

var ErrNoBackend = errors.New("balancer: no healthy backend")

// Backend is one upstream target.
type Backend struct {
	URL     string
	healthy atomic.Bool
	conns   atomic.Int64
}

func (b *Backend) SetHealthy(ok bool) { b.healthy.Store(ok) }
func (b *Backend) Healthy() bool       { return b.healthy.Load() }
func (b *Backend) Conns() int64        { return b.conns.Load() }

// Strategy selects among healthy backends.
type Strategy int

const (
	RoundRobin Strategy = iota
	LeastConn
)

// Balancer holds backends and a selection strategy.
type Balancer struct {
	mu       sync.Mutex
	backends []*Backend
	strategy Strategy
	rr       uint64
}

func New(strategy Strategy, urls ...string) *Balancer {
	b := &Balancer{strategy: strategy}
	for _, u := range urls {
		be := &Backend{URL: u}
		be.SetHealthy(true)
		b.backends = append(b.backends, be)
	}
	return b
}

// Backends returns the underlying backend list (for health updates/tests).
func (b *Balancer) Backends() []*Backend { return b.backends }

// Next returns a healthy backend per the strategy, or ErrNoBackend.
func (b *Balancer) Next() (*Backend, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	healthy := make([]*Backend, 0, len(b.backends))
	for _, be := range b.backends {
		if be.Healthy() {
			healthy = append(healthy, be)
		}
	}
	if len(healthy) == 0 {
		return nil, ErrNoBackend
	}

	switch b.strategy {
	case LeastConn:
		best := healthy[0]
		for _, be := range healthy[1:] {
			if be.Conns() < best.Conns() {
				best = be
			}
		}
		return best, nil
	default: // RoundRobin
		b.rr++
		return healthy[b.rr%uint64(len(healthy))], nil
	}
}

// Acquire selects a backend and increments its connection count; call Release
// (via the returned func) when the request completes.
func (b *Balancer) Acquire() (*Backend, func(), error) {
	be, err := b.Next()
	if err != nil {
		return nil, nil, err
	}
	be.conns.Add(1)
	return be, func() { be.conns.Add(-1) }, nil
}
