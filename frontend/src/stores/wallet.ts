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

/** Mirrors `WithdrawalOut` - `withdrawal_status` is `'paid' | 'in_progress'`, not the mock era's
 * hyphenated `'in-progress'`. */
export interface Withdrawal {
  id: string
  coins: number
  feeCoins: number
  status: 'paid' | 'in_progress'
  createdAt: string
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
    status: entry.status === 'paid' ? 'paid' : 'in_progress',
    createdAt: entry.date,
    payoutMethodId: null,
  }
}

export const useWalletStore = defineStore('wallet', () => {
  const balance = ref(0)
  const pendingClearanceCoins = ref(0)
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
   * convention as `stores/players.ts`/`bookings.ts`/`feed.ts`. */
  async function fetchWallet() {
    loading.value = true
    error.value = null
    try {
      const result = await api.get<{
        balanceCoins: number
        pendingClearanceCoins: number
        activity: WalletActivity[]
      }>('/wallet/me')
      balance.value = result.balanceCoins
      pendingClearanceCoins.value = result.pendingClearanceCoins
      activity.value = result.activity
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load wallet'
      balance.value = mockCurrentUser.coinBalance
      pendingClearanceCoins.value = mockPendingCoins
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

  /** Wallet's "Confirm Top-Up" - mock payment (real processor is Phase 4). No mock fallback,
   * a real mutation only, same convention as `feedStore.createPost`. */
  async function topUp(packageId: string, paymentLabel?: string) {
    const result = await api.post<{
      balanceCoins: number
      pendingClearanceCoins: number
      activity: WalletActivity[]
    }>('/wallet/topup', { packageId, paymentLabel })
    balance.value = result.balanceCoins
    pendingClearanceCoins.value = result.pendingClearanceCoins
    activity.value = result.activity
    return result
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
    topUp,
    fetchPayoutMethods,
    fetchWithdrawals,
    requestWithdrawal,
  }
})
