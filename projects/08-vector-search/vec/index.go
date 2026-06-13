package vec

import "sort"

// Index is a nearest-neighbor index over cosine similarity.
type Index interface {
	Add(id string, vec []float32)
	Search(query []float32, k int) []Result
	Len() int
}

type entry struct {
	id  string
	vec []float32 // stored normalized so dot == cosine
}

// FlatIndex is an exact brute-force index: it scores every vector. O(n) per
// query, but always correct — the ground truth other indexes are measured against.
type FlatIndex struct {
	entries []entry
}

func NewFlat() *FlatIndex { return &FlatIndex{} }

func (f *FlatIndex) Add(id string, v []float32) {
	f.entries = append(f.entries, entry{id: id, vec: Normalize(v)})
}

func (f *FlatIndex) Len() int { return len(f.entries) }

func (f *FlatIndex) Search(query []float32, k int) []Result {
	q := Normalize(query)
	results := make([]Result, 0, len(f.entries))
	for _, e := range f.entries {
		results = append(results, Result{ID: e.id, Score: Dot(q, e.vec)})
	}
	return topK(results, k)
}

func topK(results []Result, k int) []Result {
	sort.Slice(results, func(i, j int) bool { return results[i].Score > results[j].Score })
	if k > 0 && len(results) > k {
		results = results[:k]
	}
	return results
}
