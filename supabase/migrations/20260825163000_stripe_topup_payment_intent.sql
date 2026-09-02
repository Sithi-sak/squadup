-- 4.1 (revised): switched Wallet Top-up from a hosted Checkout Session + webhook to a
-- client-confirmed PaymentIntent verified synchronously on `POST /wallet/topup`, matching
-- PawMart's `orders.py` pattern - no webhook needed, the backend verifies the PaymentIntent
-- directly against the Stripe API in the same request that credits the wallet. Renaming rather
-- than dropping/re-adding since the column's role (idempotency key on `wallet_transactions`) is
-- unchanged, only what kind of Stripe id it stores.

alter table public.wallet_transactions
  rename column stripe_session_id to stripe_payment_intent_id;
