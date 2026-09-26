import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import { mockCurrentUser } from '@/mocks/users'
import type { WalletActivity as MockWalletActivity, WalletActivityIcon } from '@/mocks/wallet'
import {
  mockPayoutMethods,
  mockPendingCoins,
  mockTopUpPackages,
  mockWalletActivity,
  mockWithdrawalHistory,
  mockWithdrawalPlatformFeePct,
  type PayoutMethod as MockPayoutMethod,
  type TopUpPackage as MockTopUpPackage,
  type WithdrawalHistoryEntry as MockWithdrawalHistoryEntry,
} from '@/mocks/wallet'

/** Mirrors `WalletActivityOut` (`routers/wallet.py`) - `wallet_transaction_kind`/
 * `wallet_transaction_status` enum values. */
export interface WalletActivity {
  id: string
  kind: 'topup' | 'order' | 'refund' | 'payout'
  status: 'completed' | 'pending' | 'blocked'
  label: string
  detail: string | null
  coins: number
  createdAt: string
}

/** Mirrors `TopupPackageOut`. */
export interface TopupPackage {
  id: string
  coins: number
  priceUsd: number
  bonusCoins: number
  isBaseRate: boolean
}

/** Mirrors `PayoutMethodOut`. */
export interface PayoutMethod {
  id: string
  brand: string
  label: string
  detail: string | null
  isDefault: boolean
}

/** Mirrors `WithdrawalOut` - `withdrawal_status` is the underscored enum, not the mock era's
 * hyphenated `'in-progress'`. `requested` is 4.28b's new default: a payout waiting on an admin. */
export interface Withdrawal {
  id: string
  reference: string | null
  coins: number
  feeCoins: number
  status: 'requested' | 'in_progress' | 'paid' | 'rejected'
  createdAt: string
  reviewedAt: string | null
  payoutMethodId: string | null
}

/** Fallback fixtures (`mocks/wallet.ts`) predate this store and use a display-only `icon`
 * field instead of `kind`/`status` - adapted at the store boundary same as `stores/feed.ts`'s
 * `feedPostFromMock`, rather than reshaping the mock file itself. */
const KIND_BY_ICON: Record<WalletActivityIcon, WalletActivity['kind']> = {
  topup: 'topup',
  pending: 'order',
  refund: 'refund',
  blocked: 'order',
}
const STATUS_BY_ICON: Record<WalletActivityIcon, WalletActivity['status']> = {
  topup: 'completed',
  pending: 'pending',
  refund: 'completed',
  blocked: 'blocked',
}

function walletActivityFromMock(activity: MockWalletActivity): WalletActivity {
  return {
    id: activity.id,
    kind: KIND_BY_ICON[activity.icon],
    status: STATUS_BY_ICON[activity.icon],
    label: activity.label,
    detail: activity.detail,
    coins: activity.coins,
    createdAt: activity.date,
  }
}

function topupPackageFromMock(pkg: MockTopUpPackage): TopupPackage {
  return {
    id: pkg.id,
    coins: pkg.coins,
    priceUsd: pkg.priceUsd,
    bonusCoins: pkg.bonusCoins,
    isBaseRate: pkg.isBaseRate ?? false,
  }
}

function payoutMethodFromMock(method: MockPayoutMethod): PayoutMethod {
  return {
    id: method.id,
    brand: method.brand,
    label: method.label,
    detail: method.detail,
    isDefault: method.isDefault,
  }
}

function withdrawalFromMock(entry: MockWithdrawalHistoryEntry): Withdrawal {
  return {
    id: entry.id,
    coins: entry.coins,
    feeCoins: Math.round((entry.coins * mockWithdrawalPlatformFeePct) / 100),
    reference: `PO-${entry.id.slice(-8).toUpperCase()}`,
    status: entry.status === 'paid' ? 'paid' : 'requested',
    createdAt: entry.date,
    reviewedAt: null,
    payoutMethodId: null,
  }
}

export const useWalletStore = defineStore('wallet', () => {
  const balance = ref(0)
  const pendingClearanceCoins = ref(0)
  /** Coins spoken for by payout requests an admin has not decided yet (4.31). They are still in
   * the balance - the debit only lands on approval - but cannot be withdrawn again. */
  const lockedPayoutCoins = ref(0)
  const activity = ref<WalletActivity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const topupPackages = ref<TopupPackage[]>([])
  const topupPackagesLoading = ref(false)
  const topupPackagesError = ref<string | null>(null)

  const payoutMethods = ref<PayoutMethod[]>([])
  const payoutMethodsLoading = ref(false)
  const payoutMethodsError = ref<string | null>(null)

  const withdrawals = ref<Withdrawal[]>([])
  const withdrawalsLoading = ref(false)
  const withdrawalsError = ref<string | null>(null)

  /** Balance + pending clearance + recent activity (`/wallet`). Falls back to
   * `mockCurrentUser.coinBalance`/`mockPendingCoins`/`mockWalletActivity`, same resilience
   * convention as `stores/players.ts`/`bookings.ts`/`feed.ts`. Pass `silent` for a refresh after a
   * payment, so the page stays mounted. */
  async function fetchWallet(options: { silent?: boolean } = {}) {
    // `silent` refreshes in place without flipping `loading`, which `WalletView.vue` swaps the
    // whole page (and any open modal) out for a skeleton on.
    if (!options.silent) loading.value = true
    error.value = null
    try {
      const result = await api.get<{
        balanceCoins: number
        pendingClearanceCoins: number
        lockedPayoutCoins: number
        activity: WalletActivity[]
      }>('/wallet/me')
      balance.value = result.balanceCoins
      pendingClearanceCoins.value = result.pendingClearanceCoins
      lockedPayoutCoins.value = result.lockedPayoutCoins
      activity.value = result.activity
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load wallet'
      balance.value = mockCurrentUser.coinBalance
      pendingClearanceCoins.value = mockPendingCoins
      lockedPayoutCoins.value = 0
      activity.value = mockWalletActivity.map(walletActivityFromMock)
    } finally {
      loading.value = false
    }
  }

  /** Top-up tiers (`/wallet/topup-packages`), public. Falls back to `mockTopUpPackages`. */
  async function fetchTopupPackages() {
    topupPackagesLoading.value = true
    topupPackagesError.value = null
    try {
      topupPackages.value = await api.get<TopupPackage[]>('/wallet/topup-packages')
    } catch (err) {
      topupPackagesError.value = err instanceof Error ? err.message : 'Failed to load top-up packages'
      topupPackages.value = mockTopUpPackages.map(topupPackageFromMock)
    } finally {
      topupPackagesLoading.value = false
    }
  }

  /** Step 1 of a card top-up (4.57) - records a pending top-up and returns the signed fields for
   * ABA PayWay's card popup (`lib/payway.ts`). Nothing is credited yet. No mock fallback, same
   * convention as `feedStore.createPost`. */
  async function createCardCheckout(packageId: string) {
    return api.post<{ tranId: string; amountUsd: number; form: Record<string, string> }>('/wallet/topup/card', {
      packageId,
    })
  }

  /** Step 2 - polled while the popup is up. The backend confirms the payment with PayWay's Check
   * Transaction API and credits it the first time it comes back approved, so `paid` means the
   * coins are already in the balance (`fetchWallet` picks them up). */
  async function getCardTopupStatus(tranId: string) {
    return api.get<{ status: 'pending' | 'paid' | 'failed' }>(`/wallet/topup/card/${tranId}`)
  }

  /** 4.58: starts a KHQR top-up - PayWay generates a real KHQR for the chosen package, payable
   * from ABA Mobile or any Bakong member bank app. No mock fallback, same convention as
   * `createCardCheckout`. */
  async function createKhqrCheckout(packageId: string) {
    return api.post<{ tranId: string; amountUsd: number; coins: number; qrString: string; expiresAt: string }>(
      '/wallet/topup/khqr',
      { packageId },
    )
  }

  /** Polled while the KHQR modal is open. `paid` means the coins are already credited, by a real
   * payment or the backend's demo auto-confirm timer. */
  async function getKhqrTopupStatus(tranId: string) {
    return api.get<{ status: 'pending' | 'paid' | 'failed' | 'expired' }>(`/wallet/topup/khqr/${tranId}`)
  }

  /** Payout methods (`/wallet/payout-methods`, Pal only). Falls back to `mockPayoutMethods`. */
  async function fetchPayoutMethods() {
    payoutMethodsLoading.value = true
    payoutMethodsError.value = null
    try {
      payoutMethods.value = await api.get<PayoutMethod[]>('/wallet/payout-methods')
    } catch (err) {
      payoutMethodsError.value = err instanceof Error ? err.message : 'Failed to load payout methods'
      payoutMethods.value = mockPayoutMethods.map(payoutMethodFromMock)
    } finally {
      payoutMethodsLoading.value = false
    }
  }

  /** "+ Add payout method" on the Withdraw page and Settings > Payments (4.29). The backend
   * masks the account itself and forces the first method to be the default, so the created row
   * comes back ready to render. No mock fallback - a real mutation only. */
  async function addPayoutMethod(payload: {
    brand: 'card' | 'bank'
    account: string
    isDefault?: boolean
  }) {
    const method = await api.post<PayoutMethod>('/wallet/payout-methods', payload)
    // A new default demotes the others server-side; mirror that locally instead of refetching.
    if (method.isDefault) payoutMethods.value = payoutMethods.value.map((m) => ({ ...m, isDefault: false }))
    payoutMethods.value.push(method)
    return method
  }

  async function setDefaultPayoutMethod(methodId: string) {
    const method = await api.patch<PayoutMethod>(`/wallet/payout-methods/${methodId}/default`)
    payoutMethods.value = payoutMethods.value.map((m) => ({ ...m, isDefault: m.id === method.id }))
    return method
  }

  /** Deleting the default promotes the oldest remaining method server-side, so this refetches
   * rather than guessing which row took over. */
  async function removePayoutMethod(methodId: string) {
    await api.delete(`/wallet/payout-methods/${methodId}`)
    await fetchPayoutMethods()
  }

  /** Withdrawal history (`/wallet/withdrawals`, Pal only). Falls back to `mockWithdrawalHistory`. */
  async function fetchWithdrawals() {
    withdrawalsLoading.value = true
    withdrawalsError.value = null
    try {
      withdrawals.value = await api.get<Withdrawal[]>('/wallet/withdrawals')
    } catch (err) {
      withdrawalsError.value = err instanceof Error ? err.message : 'Failed to load withdrawal history'
      withdrawals.value = mockWithdrawalHistory.map(withdrawalFromMock)
    } finally {
      withdrawalsLoading.value = false
    }
  }

  /** Withdraw page's "Withdraw" button. No mock fallback, a real mutation only. Refetches the
   * wallet afterward so balance/activity reflect the debit, same convention as `stores/players.ts`'s
   * service mutations refetching `mine`. */
  async function requestWithdrawal(coins: number, payoutMethodId?: string) {
    const withdrawal = await api.post<Withdrawal>('/wallet/withdrawals', { coins, payoutMethodId })
    withdrawals.value.unshift(withdrawal)
    await fetchWallet()
    return withdrawal
  }

  return {
    balance,
    pendingClearanceCoins,
    lockedPayoutCoins,
    activity,
    loading,
    error,
    topupPackages,
    topupPackagesLoading,
    topupPackagesError,
    payoutMethods,
    payoutMethodsLoading,
    payoutMethodsError,
    withdrawals,
    withdrawalsLoading,
    withdrawalsError,
    fetchWallet,
    fetchTopupPackages,
    createCardCheckout,
    getCardTopupStatus,
    createKhqrCheckout,
    getKhqrTopupStatus,
    fetchPayoutMethods,
    addPayoutMethod,
    setDefaultPayoutMethod,
    removePayoutMethod,
    fetchWithdrawals,
    requestWithdrawal,
  }
})
