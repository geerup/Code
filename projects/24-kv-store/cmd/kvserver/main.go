// Command kvserver exposes the kv store over HTTP.
//
//	go run ./cmd/kvserver --dir ./data
//	curl -X PUT localhost:8080/kv/foo -d 'bar'
//	curl localhost:8080/kv/foo
//	curl -X DELETE localhost:8080/kv/foo
package main

import (
	"errors"
	"flag"
	"io"
	"log"
	"net/http"

	"github.com/portfolio/kvstore/kv"
)

func main() {
	dir := flag.String("dir", "./data", "data directory")
	addr := flag.String("addr", ":8080", "listen address")
	flag.Parse()

	store, err := kv.Open(*dir)
	if err != nil {
		log.Fatal(err)
	}
	defer store.Close()

	mux := http.NewServeMux()
	mux.HandleFunc("GET /kv/{key}", func(w http.ResponseWriter, r *http.Request) {
		v, err := store.Get(r.PathValue("key"))
		if errors.Is(err, kv.ErrNotFound) {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		w.Write(v)
	})
	mux.HandleFunc("PUT /kv/{key}", func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		if err := store.Put(r.PathValue("key"), body); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("DELETE /kv/{key}", func(w http.ResponseWriter, r *http.Request) {
		if errors.Is(store.Delete(r.PathValue("key")), kv.ErrNotFound) {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("POST /compact", func(w http.ResponseWriter, _ *http.Request) {
		if err := store.Compact(); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})

	log.Printf("kvserver on %s (dir=%s, %d keys)", *addr, *dir, store.Len())
	log.Fatal(http.ListenAndServe(*addr, mux))
}
