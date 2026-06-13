package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/portfolio/leaderboard/internal/store"
)

func newServer(secret string) *Server { return New(store.NewMemory(), secret) }

func postJSON(t *testing.T, h http.Handler, path string, body any) *httptest.ResponseRecorder {
	t.Helper()
	b, _ := json.Marshal(body)
	req := httptest.NewRequest(http.MethodPost, path, bytes.NewReader(b))
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func TestSignRoundTrip(t *testing.T) {
	sig := Sign("secret", "ann", "snake", 100)
	if !Verify("secret", "ann", "snake", 100, sig) {
		t.Error("valid signature should verify")
	}
	if Verify("secret", "ann", "snake", 101, sig) {
		t.Error("tampered points must not verify")
	}
	if Verify("wrong", "ann", "snake", 100, sig) {
		t.Error("wrong secret must not verify")
	}
}

func TestSubmitRejectsBadSignature(t *testing.T) {
	srv := newServer("topsecret")
	rec := postJSON(t, srv.Routes(), "/scores", submitReq{Player: "ann", Game: "g", Points: 999, Signature: "deadbeef"})
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", rec.Code)
	}
}

func TestSubmitAcceptsSignedScore(t *testing.T) {
	srv := newServer("topsecret")
	sig := Sign("topsecret", "ann", "g", 999)
	rec := postJSON(t, srv.Routes(), "/scores", submitReq{Player: "ann", Game: "g", Points: 999, Signature: sig})
	if rec.Code != http.StatusCreated {
		t.Fatalf("want 201, got %d (%s)", rec.Code, rec.Body)
	}
}

func TestLeaderboardEndpoint(t *testing.T) {
	srv := newServer("") // HMAC disabled
	for _, p := range []struct {
		player string
		pts    int64
	}{{"a", 10}, {"b", 30}, {"c", 20}} {
		postJSON(t, srv.Routes(), "/scores", submitReq{Player: p.player, Game: "arena", Points: p.pts})
	}
	req := httptest.NewRequest(http.MethodGet, "/leaderboard/arena?limit=2", nil)
	rec := httptest.NewRecorder()
	srv.Routes().ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("want 200, got %d", rec.Code)
	}
	var out struct {
		Scores []store.Score `json:"scores"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &out)
	if len(out.Scores) != 2 || out.Scores[0].Player != "b" {
		t.Errorf("unexpected leaderboard: %+v", out.Scores)
	}
}

func TestAchievementEndpoint(t *testing.T) {
	srv := newServer("")
	rec := postJSON(t, srv.Routes(), "/achievements", unlockReq{Player: "ann", Key: "win"})
	var out struct {
		Unlocked bool `json:"unlocked"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &out)
	if !out.Unlocked {
		t.Error("first unlock should report unlocked=true")
	}
}
