package api

import (
	"context"
	"net/http"
)

// contextWithUser stores the authenticated user id on the request context.
func contextWithUser(r *http.Request, uid string) context.Context {
	return context.WithValue(r.Context(), userKey, uid)
}

// userID reads the authenticated user id set by the auth middleware.
func userID(r *http.Request) string {
	if v, ok := r.Context().Value(userKey).(string); ok {
		return v
	}
	return ""
}
