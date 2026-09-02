-- 4.1b: real Stripe-backed Wallet Top-up replaces the old direct-credit mock `POST /wallet/topup`.
-- `stripe_session_id` is the webhook's idempotency key - a Stripe Checkout Session id, unique so
-- a retried/duplicate `checkout.session.completed` event can't double-credit the same top-up.

alter table public.wallet_transactions
  add column stripe_session_id text unique;
