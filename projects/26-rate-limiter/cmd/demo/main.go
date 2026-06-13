// Command demo runs a rate-limited reverse proxy in front of N in-process
// backends, showing the limiter + balancer working together.
//
//	go run ./cmd/demo
//	for i in $(seq 20); do curl -s localhost:8080/ ; echo; done   # watch 429s + round-robin
package main

import (
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"os"

	"github.com/portfolio/ratelimiter/balancer"
	"github.com/portfolio/ratelimiter/limiter"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// Spin up three backends in-process.
	var urls []string
	for i := 1; i <= 3; i++ {
		i := i
		s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			fmt.Fprintf(w, "served by backend %d\n", i)
		}))
		defer s.Close()
		urls = append(urls, s.URL)
	}

	lb := balancer.New(balancer.RoundRobin, urls...)
	rl := limiter.New(5, 2) // burst 5, 2 req/sec per client

	proxy := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		be, release, err := lb.Acquire()
		if err != nil {
			http.Error(w, "no backend", http.StatusServiceUnavailable)
			return
		}
		defer release()
		target, _ := url.Parse(be.URL)
		httputil.NewSingleHostReverseProxy(target).ServeHTTP(w, r)
	})

	handler := rl.Middleware(limiter.ClientIP)(proxy)
	log.Printf("rate-limited proxy on :%s -> %v", port, urls)
	log.Fatal(http.ListenAndServe(":"+port, handler))
}
