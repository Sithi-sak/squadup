/** Wallet page fixtures (1.1x) built per `squadup_ui/s1/WALLET/TOPUP.jpg` and `squadup_ui/s1/WITHDRAW.jpg`. */

export interface TopUpPackage {
  id: string
  coins: number
  priceUsd: number
  bonusCoins: number
  isBaseRate?: boolean
}

/** Flat 90 SC per dollar with small flat bonuses on the two larger tiers (4.28a) - mirrors
 * `20260919110000_topup_reprice.sql`, which is what a live `/wallet` actually reads. */
export const mockTopUpPackages: TopUpPackage[] = [
  { id: 'topup-5', coins: 450, priceUsd: 5, bonusCoins: 0 },
  { id: 'topup-10', coins: 900, priceUsd: 10, bonusCoins: 0, isBaseRate: true },
  { id: 'topup-25', coins: 2250, priceUsd: 25, bonusCoins: 100 },
  { id: 'topup-50', coins: 4500, priceUsd: 50, bonusCoins: 200 },
]

export type WalletActivityIcon = 'topup' | 'pending' | 'refund' | 'blocked'

export interface WalletActivity {
  id: string
  icon: WalletActivityIcon
  label: string
  detail: string
  date: string
  coins: number
}

export const mockWalletActivity: WalletActivity[] = [
  { id: 'activity-1', icon: 'topup', label: 'Top-up', detail: 'Visa •••• 4242', date: '2026-07-05T14:30:00', coins: 900 },
  { id: 'activity-2', icon: 'pending', label: 'Order', detail: 'eMeow Feeding', date: '2026-07-05T14:32:00', coins: -837 },
  { id: 'activity-3', icon: 'refund', label: 'Refund', detail: 'cancelled order', date: '2026-07-03T19:10:00', coins: 200 },
  { id: 'activity-4', icon: 'topup', label: 'Top-up', detail: 'Apple Pay', date: '2026-07-01T08:44:00', coins: 500 },
  { id: 'activity-5', icon: 'blocked', label: 'Order', detail: 'Valorant duo', date: '2026-06-28T21:02:00', coins: -340 },
]

/** Coins tied up in the pending `eMeow Feeding` order above, unavailable to withdraw yet. */
export const mockPendingCoins = 837

export interface PayoutMethod {
  id: string
  brand: 'visa' | 'mastercard' | 'card' | 'bank'
  label: string
  detail: string
  isDefault: boolean
}

export const mockPayoutMethods: PayoutMethod[] = [
  { id: 'card-1', brand: 'visa', label: 'Visa', detail: '•••• 4242', isDefault: true },
  { id: 'bank-1', brand: 'bank', label: 'ABA Bank', detail: '•••• 3356', isDefault: false },
]

/** SquadUp's cut of a payout (4.28c): the Pal keeps the other 80%. */
export const mockWithdrawalPlatformFeePct = 20

export interface WithdrawalHistoryEntry {
  id: string
  coins: number
  date: string
  method: string
  status: 'paid' | 'in-progress'
}

export const mockWithdrawalHistory: WithdrawalHistoryEntry[] = [
  { id: 'withdrawal-1', coins: 2000, date: '2026-07-01', method: 'Card', status: 'paid' },
  { id: 'withdrawal-2', coins: 1500, date: '2026-06-20', method: 'ABA Bank', status: 'paid' },
  { id: 'withdrawal-3', coins: 3000, date: '2026-06-08', method: 'ABA Bank', status: 'paid' },
  { id: 'withdrawal-4', coins: 1200, date: '2026-05-28', method: 'Card', status: 'in-progress' },
]
