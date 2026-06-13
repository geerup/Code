package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/portfolio/social/internal/social"
)

func newTestServer() *Server { return New(social.NewStore()) }

func do(t *testing.T, h http.Handler, method, path, token string, body any) *httptest.ResponseRecorder {
	t.Helper()
	var buf bytes.Buffer
	if body != nil {
		_ = json.NewEncoder(&buf).Encode(body)
	}
	req := httptest.NewRequest(method, path, &buf)
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func register(t *testing.T, h http.Handler, name string) string {
	t.Helper()
	rec := do(t, h, "POST", "/api/register", "", map[string]string{"username": name, "password": "secret123"})
	if rec.Code != http.StatusCreated {
		t.Fatalf("register %s failed: %d %s", name, rec.Code, rec.Body)
	}
	var out struct{ Token string }
	_ = json.Unmarshal(rec.Body.Bytes(), &out)
	return out.Token
}

func TestProtectedRoutesRequireAuth(t *testing.T) {
	h := newTestServer().Routes()
	rec := do(t, h, "GET", "/api/feed", "", nil)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("feed without token should be 401, got %d", rec.Code)
	}
}

func TestRegisterLoginFlow(t *testing.T) {
	s := newTestServer()
	h := s.Routes()
	register(t, h, "ann")
	// Duplicate registration conflicts.
	rec := do(t, h, "POST", "/api/register", "", map[string]string{"username": "ann", "password": "x"})
	if rec.Code != http.StatusConflict {
		t.Errorf("duplicate register should be 409, got %d", rec.Code)
	}
	// Login with correct creds.
	rec = do(t, h, "POST", "/api/login", "", map[string]string{"username": "ann", "password": "secret123"})
	if rec.Code != http.StatusOK {
		t.Errorf("login should succeed, got %d", rec.Code)
	}
	// Wrong password.
	rec = do(t, h, "POST", "/api/login", "", map[string]string{"username": "ann", "password": "nope"})
	if rec.Code != http.StatusUnauthorized {
		t.Errorf("bad login should be 401, got %d", rec.Code)
	}
}

func TestPostAppearsInFeed(t *testing.T) {
	s := newTestServer()
	h := s.Routes()
	token := register(t, h, "ann")
	rec := do(t, h, "POST", "/api/posts", token, map[string]string{"text": "hello world"})
	if rec.Code != http.StatusCreated {
		t.Fatalf("create post failed: %d %s", rec.Code, rec.Body)
	}
	rec = do(t, h, "GET", "/api/feed", token, nil)
	var out struct {
		Posts []social.Post `json:"posts"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &out)
	if len(out.Posts) != 1 || out.Posts[0].Text != "hello world" {
		t.Fatalf("post not in feed: %+v", out.Posts)
	}
}

func TestFollowMakesPostsVisible(t *testing.T) {
	s := newTestServer()
	h := s.Routes()
	annToken := register(t, h, "ann")

	// Create bob and grab his id by registering then reading /api/me.
	bobToken := register(t, h, "bob")
	meRec := do(t, h, "GET", "/api/me", bobToken, nil)
	var bob struct {
		ID string `json:"id"`
	}
	_ = json.Unmarshal(meRec.Body.Bytes(), &bob)

	do(t, h, "POST", "/api/posts", bobToken, map[string]string{"text": "bob's post"})

	// Before following, ann's feed is empty.
	rec := do(t, h, "GET", "/api/feed", annToken, nil)
	var before struct {
		Posts []social.Post `json:"posts"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &before)
	if len(before.Posts) != 0 {
		t.Fatalf("ann should see nothing before following, got %d", len(before.Posts))
	}

	// Follow bob, then his post shows up.
	do(t, h, "POST", "/api/follow/"+bob.ID, annToken, nil)
	rec = do(t, h, "GET", "/api/feed", annToken, nil)
	var after struct {
		Posts []social.Post `json:"posts"`
	}
	_ = json.Unmarshal(rec.Body.Bytes(), &after)
	if len(after.Posts) != 1 || after.Posts[0].Text != "bob's post" {
		t.Fatalf("after following, ann should see bob's post, got %+v", after.Posts)
	}
}
