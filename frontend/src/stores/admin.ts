import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import {
  mockAdminFlaggedPlayers,
  mockAdminDisputes,
  mockAdminPalApplications,
  mockAdminWithdrawals,
  type AdminFlaggedPlayer,
  type FlaggedPlayerStatus,
  type AdminDispute,
  type DisputeStatus,
  type AdminOverviewStats,
  type AdminPalApplication,
  type PalApplicationStatus,
  type AdminWithdrawal,
  type AdminWithdrawalStatus,
} from '@/mocks/admin'

/** Mock-only PIN, known solely to the admin, standing in until real admin auth ships (Phase 2
 * Supabase auth + real admin roles). There is exactly one admin "account" and no signup flow for
 * it, so `/admin` gates on this code instead of the regular `useAuthStore` user (3.19: simpler
 * than 1.15's original email/password gate, same session-only posture). */
const ADMIN_ACCESS_CODE = '1234'

const SESSION_KEY = 'squadup-admin-session'

export const useAdminStore = defineStore('admin', () => {
  const isAuthenticated = ref(sessionStorage.getItem(SESSION_KEY) === '1')
  const error = ref<string | null>(null)

  function login(code: string) {
    const matches = code.trim() === ADMIN_ACCESS_CODE
    if (matches) {
      isAuthenticated.value = true
      error.value = null
      sessionStorage.setItem(SESSION_KEY, '1')
    } else {
      error.value = 'Incorrect access code.'
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

  const withdrawals = ref<AdminWithdrawal[]>([])
  const withdrawalsLoading = ref(false)
  const withdrawalsError = ref<string | null>(null)

  const palApplications = ref<AdminPalApplication[]>([])
  const palApplicationsLoading = ref(false)
  const palApplicationsError = ref<string | null>(null)

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

  /** "Take action" > Send a warning (`POST /admin/flagged-players/{id}/warn`, 4.40). Unlike the
   * status buttons this one reaches the Pal, as a `moderation` notification, and the server
   * marks the flag `actioned` in the same call. */
  async function warnFlaggedPlayer(id: string, message?: string) {
    const updated = await api.post<AdminFlaggedPlayer>(`/admin/flagged-players/${id}/warn`, {
      message: message?.trim() || null,
    })
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
      // No mock fallback here, unlike the lists above: these are money figures, and a fabricated
      // "41,600 earned" standing in for a failed request is worse than the error state (4.41).
      overviewError.value = err instanceof Error ? err.message : 'Failed to load overview'
    } finally {
      overviewLoading.value = false
    }
  }

  /** Ban/Unban toggle in the Flagged Players review modal (`PATCH /admin/players/{id}/ban`,
   * 3.19). Patches the caller's own flag row back into `flaggedPlayers` when the response carries
   * one - a player can be banned with no flag on file, in which case there's nothing to patch. */
  async function banPlayer(playerId: string, isBanned: boolean) {
    const updated = await api.patch<AdminFlaggedPlayer | null>(`/admin/players/${playerId}/ban`, { isBanned })
    if (updated) {
      const index = flaggedPlayers.value.findIndex((flag) => flag.id === updated.id)
      if (index !== -1) flaggedPlayers.value[index] = updated
    }
    return updated
  }

  /** Payouts tab (`GET /admin/withdrawals`, 4.28d). Same fallback convention as the lists
   * above. */
  async function fetchWithdrawals() {
    withdrawalsLoading.value = true
    withdrawalsError.value = null
    try {
      withdrawals.value = await api.get<AdminWithdrawal[]>('/admin/withdrawals')
    } catch (err) {
      withdrawalsError.value = err instanceof Error ? err.message : 'Failed to load withdrawals'
      withdrawals.value = [...mockAdminWithdrawals]
    } finally {
      withdrawalsLoading.value = false
    }
  }

  /** Approve/Reject buttons (`PATCH /admin/withdrawals/{id}/status`). A rejection credits the
   * Pal's coins back server-side, so the row is patched in place and the decision is final -
   * the backend 409s on a second review of the same request. */
  async function updateWithdrawalStatus(id: string, status: AdminWithdrawalStatus) {
    const updated = await api.patch<AdminWithdrawal>(`/admin/withdrawals/${id}/status`, { status })
    const index = withdrawals.value.findIndex((withdrawal) => withdrawal.id === id)
    if (index !== -1) withdrawals.value[index] = updated
    return updated
  }

  /** Pal applications tab (`GET /admin/pal-applications`). Same fallback convention as the two
   * lists above. */
  async function fetchPalApplications() {
    palApplicationsLoading.value = true
    palApplicationsError.value = null
    try {
      palApplications.value = await api.get<AdminPalApplication[]>('/admin/pal-applications')
    } catch (err) {
      palApplicationsError.value = err instanceof Error ? err.message : 'Failed to load pal applications'
      palApplications.value = [...mockAdminPalApplications]
    } finally {
      palApplicationsLoading.value = false
    }
  }

  /** Approve/Reject buttons (`PATCH /admin/pal-applications/{id}/status`). An approved/rejected
   * application no longer shows up in a refetch of this list, so it's simply removed in place
   * rather than patched. */
  async function updatePalApplicationStatus(id: string, status: PalApplicationStatus) {
    const updated = await api.patch<AdminPalApplication>(`/admin/pal-applications/${id}/status`, { status })
    palApplications.value = palApplications.value.filter((application) => application.id !== id)
    return updated
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
    warnFlaggedPlayer,
    banPlayer,
    disputes,
    disputesLoading,
    disputesError,
    fetchDisputes,
    updateDisputeStatus,
    withdrawals,
    withdrawalsLoading,
    withdrawalsError,
    fetchWithdrawals,
    updateWithdrawalStatus,
    overview,
    overviewLoading,
    overviewError,
    fetchOverview,
    palApplications,
    palApplicationsLoading,
    palApplicationsError,
    fetchPalApplications,
    updatePalApplicationStatus,
  }
})
