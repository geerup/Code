// Command server runs the leaderboard HTTP API.
//
//	LEADERBOARD_SECRET=dev PORT=8080 go run ./cmd/server
package main

import (
	"log"
	"net/http"
	"os"

	"github.com/portfolio/leaderboard/internal/api"
	"github.com/portfolio/leaderboard/internal/store"
)

func main() {
	secret := os.Getenv("LEADERBOARD_SECRET") // empty disables HMAC checks
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	srv := api.New(store.NewMemory(), secret)
	log.Printf("leaderboard listening on :%s (hmac=%v)", port, secret != "")
	if err := http.ListenAndServe(":"+port, srv.Routes()); err != nil {
		log.Fatal(err)
	}
}
