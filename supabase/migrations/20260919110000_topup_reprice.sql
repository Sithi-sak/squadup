-- 4.28a: reprice the four top-up tiers to a flat 90 SC per dollar (was 99 at the $10 base rate),
-- with much smaller flat bonuses on the two larger tiers. Updates in place rather than
-- delete+insert so the `topup_packages.id` values already referenced by any open Stripe
-- PaymentIntent metadata / KHQR session still resolve.

update public.topup_packages set coins = 450,  bonus_coins = 0,   is_base_rate = false where price_usd = 5;
update public.topup_packages set coins = 900,  bonus_coins = 0,   is_base_rate = true  where price_usd = 10;
update public.topup_packages set coins = 2250, bonus_coins = 100, is_base_rate = false where price_usd = 25;
update public.topup_packages set coins = 4500, bonus_coins = 200, is_base_rate = false where price_usd = 50;
