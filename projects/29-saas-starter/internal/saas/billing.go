// Package saas is a reusable auth + billing skeleton for a subscription SaaS:
// users, sessions, plans, subscriptions, a (simulated) Stripe-style webhook, and
// feature gating by plan. The payment provider is abstracted so it runs with a
// fake gateway in tests and could be wired to Stripe test mode in production.
package saas

import "errors"

// Plan describes a subscription tier.
type Plan struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	PriceUSD int      `json:"price_usd"` // monthly, in dollars
	Features []string `json:"features"`
	Seats    int      `json:"seats"`
}

// Plans available in this SaaS. Feature gating reads from here.
var Plans = map[string]Plan{
	"free": {ID: "free", Name: "Free", PriceUSD: 0, Seats: 1,
		Features: []string{"basic_dashboard"}},
	"pro": {ID: "pro", Name: "Pro", PriceUSD: 19, Seats: 5,
		Features: []string{"basic_dashboard", "api_access", "export"}},
	"enterprise": {ID: "enterprise", Name: "Enterprise", PriceUSD: 99, Seats: 50,
		Features: []string{"basic_dashboard", "api_access", "export", "sso", "audit_log"}},
}

var ErrUnknownPlan = errors.New("unknown plan")

// SubStatus is a subscription lifecycle state (mirrors Stripe's).
type SubStatus string

const (
	StatusNone     SubStatus = "none"
	StatusActive   SubStatus = "active"
	StatusPastDue  SubStatus = "past_due"
	StatusCanceled SubStatus = "canceled"
)

// Subscription ties a user to a plan with a status.
type Subscription struct {
	UserID  string    `json:"user_id"`
	PlanID  string    `json:"plan_id"`
	Status  SubStatus `json:"status"`
	StripeID string   `json:"stripe_id,omitempty"`
}

// HasFeature reports whether an active subscription's plan grants a feature.
func (s Subscription) HasFeature(feature string) bool {
	if s.Status != StatusActive {
		// Inactive subs fall back to the free plan's features.
		for _, f := range Plans["free"].Features {
			if f == feature {
				return true
			}
		}
		return false
	}
	plan, ok := Plans[s.PlanID]
	if !ok {
		return false
	}
	for _, f := range plan.Features {
		if f == feature {
			return true
		}
	}
	return false
}

// Gateway abstracts the payment provider (Stripe in prod, fake in tests).
type Gateway interface {
	// CreateCheckout starts a subscription and returns a provider subscription id.
	CreateCheckout(userID, planID string) (stripeID string, err error)
}

// FakeGateway is an in-memory provider for tests/local dev.
type FakeGateway struct{ counter int }

func (g *FakeGateway) CreateCheckout(userID, planID string) (string, error) {
	if _, ok := Plans[planID]; !ok {
		return "", ErrUnknownPlan
	}
	g.counter++
	return "sub_fake_" + planID, nil
}
