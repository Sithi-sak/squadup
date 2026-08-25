import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import { mockSubscriptions, type Subscription as MockSubscription } from '@/mocks/subscriptions'

export type SubscriptionBillingCycle = 'monthly' | 'quarterly'
export type SubscriptionStatus = 'active' | 'cancelled'

/** Mirrors `SubscriptionOut` (`routers/subscriptions.py`). */
export interface Subscription {
  id: string
  playerId: string
  playerDisplayName: string
  rating: number | null
  billingCycle: SubscriptionBillingCycle
  serviceId: string | null
  serviceLabel: string
  /** Next renewal date while active, or the date access ends once cancelled. */
  renewsOn: string
  priceCoins: number
  status: SubscriptionStatus
}

/** `mocks/subscriptions.ts` predates this store: no `playerId`/`serviceId` (there's nothing
 * real to cancel/resubscribe for these) and a capitalized `billingCycle` - adapted at the store
 * boundary on fetch failure only, same convention as `stores/wallet.ts`'s `walletActivityFromMock`. */
function subscriptionFromMock(sub: MockSubscription): Subscription {
  return {
    id: sub.id,
    playerId: '',
    playerDisplayName: sub.palName,
    rating: Number(sub.rating),
    billingCycle: sub.billingCycle === 'Quarterly' ? 'quarterly' : 'monthly',
    serviceId: null,
    serviceLabel: sub.serviceLabel,
    renewsOn: sub.renewsOn,
    priceCoins: sub.priceCoins,
    status: sub.status,
  }
}

export const useSubscriptionsStore = defineStore('subscriptions', () => {
  const list = ref<Subscription[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /** `/subscriptions` page (`GET /subscriptions/mine`). Falls back to `mockSubscriptions`, same
   * mock-fallback resilience convention as `stores/wallet.ts`/`stores/notifications.ts`
   * (3.9d/3.10e). */
  async function fetchSubscriptions() {
    loading.value = true
    error.value = null
    try {
      list.value = await api.get<Subscription[]>('/subscriptions/mine')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load subscriptions'
      list.value = mockSubscriptions.map(subscriptionFromMock)
    } finally {
      loading.value = false
    }
  }

  /** `SubscriptionModal`'s confirm action (`POST /subscriptions`). Real mutation only, no mock
   * fallback, same convention as `walletStore.topUp`. */
  async function subscribe(
    playerId: string,
    serviceId?: string,
    billingCycle: SubscriptionBillingCycle = 'monthly',
  ) {
    const subscription = await api.post<Subscription>('/subscriptions', {
      playerId,
      serviceId,
      billingCycle,
    })
    list.value.unshift(subscription)
    return subscription
  }

  /** `CancelSubscriptionModal`'s confirm action (`POST /subscriptions/{id}/cancel`). Real
   * mutation only, patches the row back into `list`. */
  async function cancelSubscription(id: string) {
    const subscription = await api.post<Subscription>(`/subscriptions/${id}/cancel`)
    const index = list.value.findIndex((s) => s.id === id)
    if (index !== -1) list.value[index] = subscription
    return subscription
  }

  /** `SubscriptionsView`'s "Resubscribe" action (`POST /subscriptions/{id}/resubscribe`). Real
   * mutation only, patches the row back into `list`. */
  async function resubscribe(id: string) {
    const subscription = await api.post<Subscription>(`/subscriptions/${id}/resubscribe`)
    const index = list.value.findIndex((s) => s.id === id)
    if (index !== -1) list.value[index] = subscription
    return subscription
  }

  return {
    list,
    loading,
    error,
    fetchSubscriptions,
    subscribe,
    cancelSubscription,
    resubscribe,
  }
})
