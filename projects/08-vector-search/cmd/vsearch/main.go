// Command vsearch is a tiny demo of the vector engine: it embeds a few toy
// "documents" with a bag-of-words hashing embedder and answers a query, showing
// exact (flat) vs approximate (LSH) results.
//
//	go run ./cmd/vsearch "fast cars"
package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/portfolio/vectorsearch/vec"
)

const dim = 64

var docs = map[string]string{
	"cars":    "fast sports cars race engines speed driving",
	"cooking": "recipes food cooking kitchen chef bake oven",
	"space":   "rockets planets orbit space stars galaxy nasa",
	"music":   "guitar songs melody band concert music sound",
	"finance": "stocks money market invest trading finance bank",
}

// hashEmbed: deterministic bag-of-words feature hashing into `dim` dims.
func hashEmbed(text string) []float32 {
	v := make([]float32, dim)
	for _, tok := range strings.Fields(strings.ToLower(text)) {
		h := uint32(2166136261)
		for _, c := range []byte(tok) {
			h ^= uint32(c)
			h *= 16777619
		}
		v[h%dim] += 1
	}
	return v
}

func main() {
	query := "fast cars racing"
	if len(os.Args) > 1 {
		query = strings.Join(os.Args[1:], " ")
	}

	flat := vec.NewFlat()
	lsh := vec.NewLSH(dim, 6, 10, 42)
	for id, text := range docs {
		e := hashEmbed(text)
		flat.Add(id, e)
		lsh.Add(id, e)
	}

	q := hashEmbed(query)
	fmt.Printf("query: %q\n\nexact (flat):\n", query)
	for _, r := range flat.Search(q, 3) {
		fmt.Printf("  %-8s %.3f\n", r.ID, r.Score)
	}
	fmt.Println("\napproximate (LSH):")
	for _, r := range lsh.Search(q, 3) {
		fmt.Printf("  %-8s %.3f\n", r.ID, r.Score)
	}
}
