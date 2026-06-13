package saas

import "testing"

func newStore() *Store { return NewStore(&FakeGateway{}) }

func TestRegisterStartsOnFreePlan(t *testing.T) {
	s := newStore()
	u, token, err := s.Register("a@x.com", "pw")
	if err != nil || token == "" {
		t.Fatalf("register failed: %v", err)
	}
	sub := s.Subscription(u.ID)
	if sub.PlanID != "free" || sub.Status != StatusActive {
		t.Errorf("new user should be active free, got %+v", sub)
	}
}

func TestDuplicateEmailRejected(t *testing.T) {
	s := newStore()
	s.Register("a@x.com", "pw")
	if _, _, err := s.Register("a@x.com", "pw2"); err != ErrUserExists {
		t.Errorf("want ErrUserExists, got %v", err)
	}
}

func TestLoginAuth(t *testing.T) {
	s := newStore()
	s.Register("a@x.com", "pw")
	if _, _, err := s.Login("a@x.com", "pw"); err != nil {
		t.Errorf("valid login failed: %v", err)
	}
	if _, _, err := s.Login("a@x.com", "wrong"); err != ErrBadPassword {
		t.Errorf("bad password should fail, got %v", err)
	}
	if _, _, err := s.Login("missing@x.com", "pw"); err != ErrNoUser {
		t.Errorf("unknown user should fail, got %v", err)
	}
}

func TestSessionLookup(t *testing.T) {
	s := newStore()
	u, token, _ := s.Register("a@x.com", "pw")
	uid, ok := s.UserForToken(token)
	if !ok || uid != u.ID {
		t.Errorf("session should resolve to user")
	}
	if _, ok := s.UserForToken("bogus"); ok {
		t.Error("bogus token should not resolve")
	}
}

func TestSubscribeThenWebhookActivates(t *testing.T) {
	s := newStore()
	u, _, _ := s.Register("a@x.com", "pw")

	sub, err := s.Subscribe(u.ID, "pro")
	if err != nil {
		t.Fatal(err)
	}
	// Before the webhook, the subscription is not yet active.
	if s.Subscription(u.ID).Status != StatusPastDue {
		t.Errorf("pre-payment status should be past_due, got %v", s.Subscription(u.ID).Status)
	}
	// Provider confirms payment.
	if err := s.HandleWebhook("invoice.paid", sub.StripeID); err != nil {
		t.Fatal(err)
	}
	active := s.Subscription(u.ID)
	if active.Status != StatusActive || active.PlanID != "pro" {
		t.Errorf("after webhook should be active pro, got %+v", active)
	}
}

func TestUnknownPlanRejected(t *testing.T) {
	s := newStore()
	u, _, _ := s.Register("a@x.com", "pw")
	if _, err := s.Subscribe(u.ID, "platinum"); err != ErrUnknownPlan {
		t.Errorf("want ErrUnknownPlan, got %v", err)
	}
}

func TestFeatureGating(t *testing.T) {
	s := newStore()
	u, _, _ := s.Register("a@x.com", "pw")

	// Free plan: basic only.
	if s.Subscription(u.ID).HasFeature("api_access") {
		t.Error("free plan must not have api_access")
	}
	if !s.Subscription(u.ID).HasFeature("basic_dashboard") {
		t.Error("free plan should have basic_dashboard")
	}

	// Upgrade to pro and activate.
	sub, _ := s.Subscribe(u.ID, "pro")
	s.HandleWebhook("invoice.paid", sub.StripeID)
	if !s.Subscription(u.ID).HasFeature("api_access") {
		t.Error("active pro should grant api_access")
	}
	if s.Subscription(u.ID).HasFeature("sso") {
		t.Error("pro should not grant enterprise-only sso")
	}
}

func TestCancellationFallsBackToFree(t *testing.T) {
	s := newStore()
	u, _, _ := s.Register("a@x.com", "pw")
	sub, _ := s.Subscribe(u.ID, "pro")
	s.HandleWebhook("invoice.paid", sub.StripeID)
	s.HandleWebhook("customer.subscription.deleted", sub.StripeID)
	after := s.Subscription(u.ID)
	if after.Status != StatusCanceled || after.PlanID != "free" {
		t.Errorf("canceled sub should fall back to free, got %+v", after)
	}
	if after.HasFeature("api_access") {
		t.Error("canceled user should lose pro features")
	}
}
