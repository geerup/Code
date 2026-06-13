// Package vec is a from-scratch vector search engine: exact (brute-force) and
// approximate (LSH) nearest-neighbor search over dense float vectors — the core
// machinery underneath a RAG system or semantic search.
package vec

import "math"

// Dot is the dot product of two equal-length vectors.
func Dot(a, b []float32) float32 {
	var s float32
	for i := range a {
		s += a[i] * b[i]
	}
	return s
}

// Norm is the Euclidean (L2) norm.
func Norm(a []float32) float32 {
	return float32(math.Sqrt(float64(Dot(a, a))))
}

// Cosine similarity in [-1, 1]. Returns 0 if either vector is zero.
func Cosine(a, b []float32) float32 {
	na, nb := Norm(a), Norm(b)
	if na == 0 || nb == 0 {
		return 0
	}
	return Dot(a, b) / (na * nb)
}

// Normalize returns a unit-length copy (so cosine == dot product).
func Normalize(a []float32) []float32 {
	n := Norm(a)
	out := make([]float32, len(a))
	if n == 0 {
		return out
	}
	for i := range a {
		out[i] = a[i] / n
	}
	return out
}

// Result is a scored match.
type Result struct {
	ID    string
	Score float32
}
