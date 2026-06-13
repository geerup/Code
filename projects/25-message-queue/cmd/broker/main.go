// Command broker exposes the message queue over HTTP.
//
//	POST /publish/{topic}    body = message  -> {"id":N}
//	POST /consume/{topic}                     -> message (404 if empty)
//	POST /ack/{topic}/{id}
//	GET  /stats/{topic}
package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/portfolio/mq/broker"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	b := broker.New(30 * time.Second)
	mux := http.NewServeMux()

	mux.HandleFunc("POST /publish/{topic}", func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		id := b.Publish(r.PathValue("topic"), body)
		writeJSON(w, 201, map[string]uint64{"id": id})
	})
	mux.HandleFunc("POST /consume/{topic}", func(w http.ResponseWriter, r *http.Request) {
		msg, err := b.Consume(r.PathValue("topic"))
		if err != nil {
			http.Error(w, "no messages", http.StatusNotFound)
			return
		}
		writeJSON(w, 200, map[string]any{"id": msg.ID, "body": string(msg.Body), "deliveries": msg.Deliveries})
	})
	mux.HandleFunc("POST /ack/{topic}/{id}", func(w http.ResponseWriter, r *http.Request) {
		id, _ := strconv.ParseUint(r.PathValue("id"), 10, 64)
		writeJSON(w, 200, map[string]bool{"acked": b.Ack(r.PathValue("topic"), id)})
	})
	mux.HandleFunc("GET /stats/{topic}", func(w http.ResponseWriter, r *http.Request) {
		ready, inflight := b.Stats(r.PathValue("topic"))
		writeJSON(w, 200, map[string]int{"ready": ready, "in_flight": inflight})
	})

	log.Printf("broker on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
