package vec

import "math"

// LSHIndex is an approximate index using random-hyperplane locality-sensitive
// hashing. Each of L tables hashes a vector to a K-bit signature (the sign of
// its dot product with K random hyperplanes); similar vectors are likely to
// share a bucket. Queries only score candidates that collide in some table —
// sub-linear on average, trading a little recall for speed.
type LSHIndex struct {
	dim    int
	k      int // bits per signature
	planes [][][]float32 // [L][k][dim] random hyperplane normals
	tables []map[uint64][]int
	store  []entry
}

// NewLSH builds an index over `dim`-dimensional vectors with L tables of k bits.
// `seed` makes the random planes reproducible.
func NewLSH(dim, l, k int, seed uint64) *LSHIndex {
	idx := &LSHIndex{dim: dim, k: k}
	r := newRand(seed)
	for t := 0; t < l; t++ {
		planes := make([][]float32, k)
		for i := 0; i < k; i++ {
			p := make([]float32, dim)
			for d := 0; d < dim; d++ {
				p[d] = float32(r.normal())
			}
			planes[i] = p
		}
		idx.planes = append(idx.planes, planes)
		idx.tables = append(idx.tables, make(map[uint64][]int))
	}
	return idx
}

func (idx *LSHIndex) signature(table int, v []float32) uint64 {
	var sig uint64
	for i, plane := range idx.planes[table] {
		if Dot(v, plane) >= 0 {
			sig |= 1 << uint(i)
		}
	}
	return sig
}

func (idx *LSHIndex) Add(id string, v []float32) {
	nv := Normalize(v)
	pos := len(idx.store)
	idx.store = append(idx.store, entry{id: id, vec: nv})
	for t := range idx.tables {
		sig := idx.signature(t, nv)
		idx.tables[t][sig] = append(idx.tables[t][sig], pos)
	}
}

func (idx *LSHIndex) Len() int { return len(idx.store) }

// Search gathers candidates from every table bucket the query falls into, then
// exactly ranks just those candidates. Falls back to a full scan if no bucket
// yields candidates (keeps recall sane on tiny datasets).
func (idx *LSHIndex) Search(query []float32, k int) []Result {
	q := Normalize(query)
	seen := make(map[int]struct{})
	for t := range idx.tables {
		sig := idx.signature(t, q)
		for _, pos := range idx.tables[t][sig] {
			seen[pos] = struct{}{}
		}
	}
	if len(seen) == 0 {
		for i := range idx.store {
			seen[i] = struct{}{}
		}
	}
	results := make([]Result, 0, len(seen))
	for pos := range seen {
		results = append(results, Result{ID: idx.store[pos].id, Score: Dot(q, idx.store[pos].vec)})
	}
	return topK(results, k)
}

// --- tiny deterministic RNG with a normal() sampler (Box-Muller) -------------

type rng struct{ s uint64 }

func newRand(seed uint64) *rng {
	if seed == 0 {
		seed = 0x2545F4914F6CDD1D
	}
	return &rng{s: seed}
}

func (r *rng) next() uint64 {
	r.s ^= r.s << 13
	r.s ^= r.s >> 7
	r.s ^= r.s << 17
	return r.s
}

func (r *rng) float() float64 { return float64(r.next()>>11) / float64(1<<53) }

func (r *rng) normal() float64 {
	u1 := r.float()
	if u1 < 1e-12 {
		u1 = 1e-12
	}
	u2 := r.float()
	return math.Sqrt(-2*math.Log(u1)) * math.Cos(2*math.Pi*u2)
}
