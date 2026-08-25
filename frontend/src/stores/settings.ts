import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import { formatTimeAgo } from '@/utils/timeAgo'
import { mockActiveSessions, mockPaymentCards } from '@/mocks/settings'

/** Mirrors `PaymentCardOut` (`routers/settings.py`). Structurally compatible with
 * `mocks/settings.ts`'s `PaymentCard` already, so the mock fallback below spread-copies it
 * directly rather than needing a converter. */
export interface PaymentCard {
  id: string
  brand: string
  label: string
  detail: string | null
  isDefault: boolean
}

/** Settings tab's session shape - keeps `mocks/settings.ts`'s pre-existing friendly
 * `lastActive`/`current` display fields rather than adopting the backend's raw-timestamp,
 * nullable-device `SessionOut`. Adapted at the store boundary via `sessionFromApi`, same
 * convention as `stores/wallet.ts`'s `walletActivityFromMock` - not worth reshaping the mock
 * file over. */
export interface ActiveSession {
  id: string
  device: string
  location: string
  lastActive: string
  current: boolean
}

interface SessionApiOut {
  id: string
  device: string | null
  location: string | null
  lastActiveAt: string
  isCurrent: boolean
}

function sessionFromApi(s: SessionApiOut): ActiveSession {
  return {
    id: s.id,
    device: s.device ?? 'Unknown device',
    location: s.location ?? '',
    lastActive: s.isCurrent ? 'active now' : formatTimeAgo(s.lastActiveAt),
    current: s.isCurrent,
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const paymentCards = ref<PaymentCard[]>([])
  const paymentCardsLoading = ref(false)
  const paymentCardsError = ref<string | null>(null)

  const sessions = ref<ActiveSession[]>([])
  const sessionsLoading = ref(false)
  const sessionsError = ref<string | null>(null)

  /** Payments tab's card list (`GET /settings/payment-cards`). Falls back to `mockPaymentCards`
   * on failure, same resilience convention as every other Phase 3 store. */
  async function fetchPaymentCards() {
    paymentCardsLoading.value = true
    paymentCardsError.value = null
    try {
      paymentCards.value = await api.get<PaymentCard[]>('/settings/payment-cards')
    } catch (err) {
      paymentCardsError.value = err instanceof Error ? err.message : 'Failed to load payment cards'
      paymentCards.value = mockPaymentCards.map((card) => ({ ...card }))
    } finally {
      paymentCardsLoading.value = false
    }
  }

  async function setDefaultPaymentCard(cardId: string) {
    const card = await api.patch<PaymentCard>(`/settings/payment-cards/${cardId}/default`)
    paymentCards.value = paymentCards.value.map((c) => ({ ...c, isDefault: c.id === card.id }))
  }

  async function removePaymentCard(cardId: string) {
    await api.delete(`/settings/payment-cards/${cardId}`)
    paymentCards.value = paymentCards.value.filter((c) => c.id !== cardId)
  }

  /** Security tab's session list (`GET /settings/sessions`). Falls back to `mockActiveSessions`
   * on failure. */
  async function fetchSessions() {
    sessionsLoading.value = true
    sessionsError.value = null
    try {
      sessions.value = (await api.get<SessionApiOut[]>('/settings/sessions')).map(sessionFromApi)
    } catch (err) {
      sessionsError.value = err instanceof Error ? err.message : 'Failed to load sessions'
      sessions.value = mockActiveSessions.map((session) => ({ ...session }))
    } finally {
      sessionsLoading.value = false
    }
  }

  /** Upserts the caller's own device row (`POST /settings/sessions`, keyed server-side off the
   * `User-Agent` header) - meant to be called once on auth init (3.13g) so the session list
   * reflects real logins instead of staying empty forever. Swallows failures: best-effort
   * bookkeeping, not worth surfacing an error for. */
  async function touchSession() {
    try {
      await api.post('/settings/sessions')
    } catch {
      // best-effort, see docstring
    }
  }

  async function signOutSession(sessionId: string) {
    await api.delete(`/settings/sessions/${sessionId}`)
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
  }

  async function signOutOtherSessions() {
    sessions.value = (
      await api.post<SessionApiOut[]>('/settings/sessions/sign-out-others')
    ).map(sessionFromApi)
  }

  return {
    paymentCards,
    paymentCardsLoading,
    paymentCardsError,
    fetchPaymentCards,
    setDefaultPaymentCard,
    removePaymentCard,
    sessions,
    sessionsLoading,
    sessionsError,
    fetchSessions,
    touchSession,
    signOutSession,
    signOutOtherSessions,
  }
})
