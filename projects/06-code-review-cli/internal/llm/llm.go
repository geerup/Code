// Package llm wraps a chat model behind a tiny interface so the reviewer is
// testable without a network. The default implementation targets Ollama's
// HTTP API (local, free), but any Client can be injected.
package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client produces a completion for a prompt.
type Client interface {
	Complete(ctx context.Context, system, user string) (string, error)
}

// Ollama talks to a local Ollama server (https://ollama.com).
type Ollama struct {
	BaseURL string
	Model   string
	HTTP    *http.Client
}

// NewOllama returns a client with sensible defaults.
func NewOllama(baseURL, model string) *Ollama {
	if baseURL == "" {
		baseURL = "http://localhost:11434"
	}
	if model == "" {
		model = "llama3.1"
	}
	return &Ollama{BaseURL: baseURL, Model: model, HTTP: &http.Client{Timeout: 120 * time.Second}}
}

type chatReq struct {
	Model    string    `json:"model"`
	Messages []message `json:"messages"`
	Stream   bool      `json:"stream"`
}
type message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}
type chatResp struct {
	Message message `json:"message"`
}

// Complete sends a system+user prompt and returns the assistant reply.
func (o *Ollama) Complete(ctx context.Context, system, user string) (string, error) {
	body, _ := json.Marshal(chatReq{
		Model:  o.Model,
		Stream: false,
		Messages: []message{
			{Role: "system", Content: system},
			{Role: "user", Content: user},
		},
	})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, o.BaseURL+"/api/chat", bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := o.HTTP.Do(req)
	if err != nil {
		return "", fmt.Errorf("ollama request: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("ollama status %d: %s", resp.StatusCode, b)
	}
	var out chatResp
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", err
	}
	return out.Message.Content, nil
}

// Static is a deterministic client for tests and offline demos.
type Static struct{ Reply string }

// Complete ignores the prompt and returns the canned reply.
func (s Static) Complete(_ context.Context, _, _ string) (string, error) {
	return s.Reply, nil
}
