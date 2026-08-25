import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import {
  mockAdminFlaggedPlayers,
  mockAdminDisputes,
  mockAdminOverviewStats,
  type AdminFlaggedPlayer,
  type FlaggedPlayerStatus,
  type AdminDispute,
  type DisputeStatus,
  type AdminOverviewStats,
} from '@/mocks/admin'

/** Mock-only credential, known solely to the admin, standing in until real admin auth ships
 * (Phase 2 Supabase auth + the 3.8 admin endpoints). There is exactly one admin account and no
 * signup flow for it, so `/admin` gates on this instead of the regular `useAuthStore` user. */
const ADMIN_EMAIL = 'admin@squadup.gg'
const ADMIN_PASSWORD = 'SquadUp-Admin-26'

const SESSION_KEY = 'squadup-admin-session'

export const useAdminStore = defineStore('admin', () => {
  const isAuthenticated = ref(sessionStorage.getItem(SESSION_KEY) === '1')
  const error = ref<string | null>(null)

  function login(email: string, password: string) {
    const matches = email.trim().toLowerCase() === ADMIN_EMAIL && password === ADMIN_PASSWORD
    if (matches) {
      isAuthenticated.value = true
      error.value = null
      sessionStorage.setItem(SESSION_KEY, '1')
    } else {
      error.value = 'Incorrect email or password.'
    }
    return matches
  }

  function logout() {
    isAuthenticated.value = false
    sessionStorage.removeItem(SESSION_KEY)
  }

  const flaggedPlayers = ref<AdminFlaggedPlayer[]>([])
  const flaggedPlayersLoading = ref(false)
  const flaggedPlayersError = ref<string | null>(null)

  const disputes = ref<AdminDispute[]>([])
  const disputesLoading = ref(false)
  const disputesError = ref<string | null>(null)

  const overview = ref<AdminOverviewStats | null>(null)
  const overviewLoading = ref(false)
  const overviewError = ref<string | null>(null)

  /** Flagged Players tab (`GET /admin/flagged-players`). Falls back to `mockAdminFlaggedPlayers`
   * on failure, same convention as every other Phase 3 store's list fetch. */
  async function fetchFlaggedPlayers() {
    flaggedPlayersLoading.value = true
    flaggedPlayersError.value = null
    try {
      flaggedPlayers.value = await api.get<AdminFlaggedPlayer[]>('/admin/flagged-players')
    } catch (err) {
      flaggedPlayersError.value = err instanceof Error ? err.message : 'Failed to load flagged players'
      flaggedPlayers.value = [...mockAdminFlaggedPlayers]
    } finally {
      flaggedPlayersLoading.value = false
    }
  }

  /** Dismiss/Reviewing/Take action buttons (`PATCH /admin/flagged-players/{id}/status`). Patches
   * the row back into `flaggedPlayers` in place rather than refetching the whole list. */
  async function updateFlaggedPlayerStatus(id: string, status: FlaggedPlayerStatus) {
    const updated = await api.patch<AdminFlaggedPlayer>(`/admin/flagged-players/${id}/status`, { status })
    const index = flaggedPlayers.value.findIndex((flag) => flag.id === id)
    if (index !== -1) flaggedPlayers.value[index] = updated
    return updated
  }

  /** Disputes tab (`GET /admin/disputes`). Same fallback convention as `fetchFlaggedPlayers`. */
  async function fetchDisputes() {
    disputesLoading.value = true
    disputesError.value = null
    try {
      disputes.value = await api.get<AdminDispute[]>('/admin/disputes')
    } catch (err) {
      disputesError.value = err instanceof Error ? err.message : 'Failed to load disputes'
      disputes.value = [...mockAdminDisputes]
    } finally {
      disputesLoading.value = false
    }
  }

  /** Investigate/Resolve/Refund buyer buttons (`PATCH /admin/disputes/{id}/status`). */
  async function updateDisputeStatus(id: string, status: DisputeStatus) {
    const updated = await api.patch<AdminDispute>(`/admin/disputes/${id}/status`, { status })
    const index = disputes.value.findIndex((dispute) => dispute.id === id)
    if (index !== -1) disputes.value[index] = updated
    return updated
  }

  /** Overview tab (`GET /admin/overview`). Same fallback convention as the two lists above. */
  async function fetchOverview() {
    overviewLoading.value = true
    overviewError.value = null
    try {
      overview.value = await api.get<AdminOverviewStats>('/admin/overview')
    } catch (err) {
      overviewError.value = err instanceof Error ? err.message : 'Failed to load overview'
      overview.value = mockAdminOverviewStats
    } finally {
      overviewLoading.value = false
    }
  }

  return {
    isAuthenticated,
    error,
    login,
    logout,
    flaggedPlayers,
    flaggedPlayersLoading,
    flaggedPlayersError,
    fetchFlaggedPlayers,
    updateFlaggedPlayerStatus,
    disputes,
    disputesLoading,
    disputesError,
    fetchDisputes,
    updateDisputeStatus,
    overview,
    overviewLoading,
    overviewError,
    fetchOverview,
  }
})
