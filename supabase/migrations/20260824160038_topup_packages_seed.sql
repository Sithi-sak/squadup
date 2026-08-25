-- Seed the 4 top-up tiers `mocks/wallet.ts`'s `mockTopUpPackages` already authors (3.9b).
-- The 2.3 migration created `topup_packages` with no rows, so `GET /wallet/topup-packages`
-- has nothing to read without this.

insert into public.topup_packages (coins, price_usd, bonus_coins, is_base_rate)
values
  (495, 5, 0, false),
  (990, 10, 0, true),
  (2750, 25, 275, false),
  (6000, 50, 1050, false);
