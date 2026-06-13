# 🚀 SaaS Starter — Auth + Billing (#29)

A reusable skeleton for a subscription SaaS: email/password **auth** with
sessions, **plans**, **subscriptions**, a **webhook-driven billing lifecycle**,
and **feature gating by plan**. The payment provider is abstracted behind a
`Gateway` interface, so it runs with a fake gateway in tests and wires to Stripe
test mode in production.

## The billing lifecycle (the important part)
Subscribing doesn't trust the client to say "I paid." Instead:
1. `POST /api/subscribe` calls the gateway and records the sub as **`past_due`**.
2. The provider later calls **`POST /api/webhook`** with `invoice.paid` →
   the subscription flips to **`active`** and features unlock.
3. `customer.subscription.deleted` → **`canceled`**, falling back to the free plan.

This mirrors exactly how Stripe webhooks keep your DB in sync with billing — the
#1 thing people get wrong in homegrown SaaS billing.

## Feature gating
`Subscription.HasFeature("api_access")` reads the plan's feature list and the
subscription status, so handlers gate functionality with one call.

## Tested (`internal/saas/saas_test.go`)
free-plan defaults · duplicate-email rejection · login auth · session lookup ·
**subscribe→webhook activation** · unknown-plan rejection · **feature gating per
plan/status** · **cancellation reverts to free**.

## Run
```bash
go test ./...
go run ./cmd/server        # http://localhost:8080 — sign up, pick a plan
```

## What I learned / next
- Webhook-driven billing state, abstracting the payment provider for testability,
  password hashing, and plan-based feature flags.
- Next: real Stripe Checkout + signature verification, Postgres, seats/team
  invites, and a customer portal.
