// Command server runs the SaaS starter: auth + subscription billing API +
// a static pricing/dashboard page.
//
//	go run ./cmd/server        # http://localhost:8080
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/portfolio/saas/internal/saas"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	store := saas.NewStore(&saas.FakeGateway{}) // swap for a real Stripe gateway
	h := &handlers{store: store}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/plans", h.plans)
	mux.HandleFunc("POST /api/register", h.register)
	mux.HandleFunc("POST /api/login", h.login)
	mux.HandleFunc("GET /api/me", h.auth(h.me))
	mux.HandleFunc("POST /api/subscribe", h.auth(h.subscribe))
	mux.HandleFunc("POST /api/webhook", h.webhook) // provider calls this (verify signature in prod)
	mux.Handle("/", http.FileServer(http.Dir("web")))

	log.Printf("saas starter on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}

type handlers struct{ store *saas.Store }

func (h *handlers) auth(next func(http.ResponseWriter, *http.Request, string)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := ""
		if a := r.Header.Get("Authorization"); len(a) > 7 {
			token = a[7:]
		}
		uid, ok := h.store.UserForToken(token)
		if !ok {
			writeJSON(w, 401, map[string]string{"error": "not authenticated"})
			return
		}
		next(w, r, uid)
	}
}

func (h *handlers) plans(w http.ResponseWriter, _ *http.Request) { writeJSON(w, 200, saas.Plans) }

func (h *handlers) register(w http.ResponseWriter, r *http.Request) {
	c := creds(r)
	u, token, err := h.store.Register(c.Email, c.Password)
	if err != nil {
		writeJSON(w, 409, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 201, map[string]string{"token": token, "id": u.ID, "email": u.Email})
}

func (h *handlers) login(w http.ResponseWriter, r *http.Request) {
	c := creds(r)
	u, token, err := h.store.Login(c.Email, c.Password)
	if err != nil {
		writeJSON(w, 401, map[string]string{"error": "invalid credentials"})
		return
	}
	writeJSON(w, 200, map[string]string{"token": token, "id": u.ID, "email": u.Email})
}

func (h *handlers) me(w http.ResponseWriter, _ *http.Request, uid string) {
	sub := h.store.Subscription(uid)
	plan := saas.Plans[sub.PlanID]
	writeJSON(w, 200, map[string]any{"subscription": sub, "plan": plan, "features": plan.Features})
}

func (h *handlers) subscribe(w http.ResponseWriter, r *http.Request, uid string) {
	var body struct {
		Plan string `json:"plan"`
	}
	_ = json.NewDecoder(r.Body).Decode(&body)
	sub, err := h.store.Subscribe(uid, body.Plan)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, sub)
}

func (h *handlers) webhook(w http.ResponseWriter, r *http.Request) {
	var ev struct {
		Type     string `json:"type"`
		StripeID string `json:"stripe_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&ev); err != nil {
		writeJSON(w, 400, map[string]string{"error": "bad event"})
		return
	}
	if err := h.store.HandleWebhook(ev.Type, ev.StripeID); err != nil {
		writeJSON(w, 404, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]bool{"ok": true})
}

type credentials struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

func creds(r *http.Request) credentials {
	var c credentials
	_ = json.NewDecoder(r.Body).Decode(&c)
	return c
}

func writeJSON(w http.ResponseWriter, code int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(body)
}
