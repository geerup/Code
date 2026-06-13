package vec

import (
	"math"
	"testing"
)

func TestCosineBasics(t *testing.T) {
	a := []float32{1, 0}
	if got := Cosine(a, []float32{1, 0}); math.Abs(float64(got)-1) > 1e-6 {
		t.Errorf("identical vectors cosine = %v, want 1", got)
	}
	if got := Cosine(a, []float32{0, 1}); math.Abs(float64(got)) > 1e-6 {
		t.Errorf("orthogonal cosine = %v, want 0", got)
	}
	if got := Cosine(a, []float32{0, 0}); got != 0 {
		t.Errorf("zero vector cosine = %v, want 0", got)
	}
}

func TestFlatExactSearch(t *testing.T) {
	idx := NewFlat()
	idx.Add("x", []float32{1, 0, 0})
	idx.Add("y", []float32{0, 1, 0})
	idx.Add("z", []float32{0.9, 0.1, 0})
	res := idx.Search([]float32{1, 0, 0}, 2)
	if len(res) != 2 {
		t.Fatalf("want 2 results, got %d", len(res))
	}
	if res[0].ID != "x" {
		t.Errorf("nearest should be x, got %s", res[0].ID)
	}
	if res[1].ID != "z" {
		t.Errorf("second nearest should be z, got %s", res[1].ID)
	}
}

func TestSearchKLimit(t *testing.T) {
	idx := NewFlat()
	for _, id := range []string{"a", "b", "c", "d"} {
		idx.Add(id, []float32{float32(len(id)), 1, 0})
	}
	if got := len(idx.Search([]float32{1, 1, 1}, 2)); got != 2 {
		t.Errorf("k=2 should cap results, got %d", got)
	}
}

// LSH should agree with the exact index most of the time (high recall@10).
// Uses clustered data — the realistic case for embeddings, where true neighbors
// are genuinely closer than random points (uniform-random data has no
// meaningful nearest neighbor and defeats any ANN method).
func TestLSHRecallAgainstFlat(t *testing.T) {
	const dim, clusters, perCluster = 32, 20, 100
	const n = clusters * perCluster
	flat := NewFlat()
	lsh := NewLSH(dim, 16, 10, 42)
	r := newRand(7)

	// Build cluster centers, then scatter points around them.
	centers := make([][]float32, clusters)
	for c := 0; c < clusters; c++ {
		center := make([]float32, dim)
		for d := 0; d < dim; d++ {
			center[d] = float32(r.normal())
		}
		centers[c] = center
	}

	vectors := make([][]float32, 0, n)
	i := 0
	for c := 0; c < clusters; c++ {
		for p := 0; p < perCluster; p++ {
			v := make([]float32, dim)
			for d := 0; d < dim; d++ {
				v[d] = centers[c][d] + float32(r.normal())*0.15
			}
			vectors = append(vectors, v)
			id := itoa(i)
			flat.Add(id, v)
			lsh.Add(id, v)
			i++
		}
	}

	const queries, k = 50, 10
	hits, total := 0, 0
	for q := 0; q < queries; q++ {
		query := vectors[q*7%n]
		truth := idSet(flat.Search(query, k))
		for _, res := range lsh.Search(query, k) {
			if _, ok := truth[res.ID]; ok {
				hits++
			}
			total++
		}
	}
	recall := float64(hits) / float64(total)
	if recall < 0.7 {
		t.Errorf("LSH recall@%d = %.2f, want >= 0.70", k, recall)
	}
}

func TestLSHFindsExactDuplicate(t *testing.T) {
	idx := NewLSH(4, 6, 10, 1)
	idx.Add("target", []float32{0.2, -0.5, 0.7, 0.1})
	for i := 0; i < 50; i++ {
		idx.Add(itoa(i), []float32{float32(i), 1, -1, 0})
	}
	res := idx.Search([]float32{0.2, -0.5, 0.7, 0.1}, 1)
	if len(res) == 0 || res[0].ID != "target" {
		t.Errorf("LSH failed to retrieve exact match, got %+v", res)
	}
}

func idSet(rs []Result) map[string]struct{} {
	m := make(map[string]struct{}, len(rs))
	for _, r := range rs {
		m[r.ID] = struct{}{}
	}
	return m
}

func itoa(i int) string {
	if i == 0 {
		return "0"
	}
	var b []byte
	for i > 0 {
		b = append([]byte{byte('0' + i%10)}, b...)
		i /= 10
	}
	return string(b)
}
