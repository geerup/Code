// Command server runs the social app: JSON API + SSE feed + static client.
//
//	go run ./cmd/server        # http://localhost:8080
package main

import (
	"log"
	"net/http"
	"os"

	"github.com/portfolio/social/internal/api"
	"github.com/portfolio/social/internal/social"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	srv := api.New(social.NewStore())

	mux := srv.Routes()
	mux.Handle("/", http.FileServer(http.Dir("web")))

	log.Printf("social app on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
