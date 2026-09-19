/**
 * Squad Coin <-> USD display rate.
 *
 * This is the base top-up tier's rate (900 SC for $10, `20260919110000_topup_reprice.sql`), and it
 * lived as a copy-pasted `const COINS_PER_USD` in five views until 4.33. Repricing in 4.28a only
 * updated one of them, so `/wallet` went on showing a 900 SC balance as "$9.09" at the old 99 rate.
 * One definition means the next reprice cannot half-land the same way.
 *
 * Display only: nothing is charged or paid out at this rate. Real money amounts come from
 * `topup_packages.price_usd`, and payouts move no money at all (4.31).
 */
export const COINS_PER_USD = 90

/** The "≈ $X.XX" figure shown next to a coin amount. */
export function coinsToUsd(coins: number) {
  return (coins / COINS_PER_USD).toFixed(2)
}
