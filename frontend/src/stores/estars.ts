import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'
import { mockEstarsLeaderboard } from '@/mocks/estars'

export type EstarPeriod = 'week' | 'month' | 'all_time'

/** Mirrors `EstarEntryOut` (`routers/estars.py`, 3.12a). `category`/`rating` are nullable here
 * (a player can lack a highlighted service, or have no reviews yet) even though
 * `mockEstarsLeaderboard`'s entries always set both. */
export interface EstarEntry {
  id: string
  rank: number
  displayName: string
  avatarUrl: string | null
  category: string | null
  rating: number | null
  coins: number
  trend: 'up' | 'down' | 'flat'
}

export const useEstarsStore = defineStore('estars', () => {
  const leaderboard = ref<EstarEntry[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /** Estars Leaderboard (`GET /estars/leaderboard`, public). Falls back to
   * `mockEstarsLeaderboard` if the request fails, same mock-fallback resilience convention as
   * every other Phase 3 store (`stores/bookings.ts`'s `fetchList`/`fetchIncoming`, etc). */
  async function fetchLeaderboard(period: EstarPeriod, category?: string | null) {
    if (loading.value) return
    loading.value = true
    error.value = null
    try {
      const query = new URLSearchParams({ period })
      if (category) query.set('category', category)
      leaderboard.value = await api.get<EstarEntry[]>(`/estars/leaderboard?${query.toString()}`)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load leaderboard'
      leaderboard.value = [...mockEstarsLeaderboard]
    } finally {
      loading.value = false
    }
  }

  return { leaderboard, loading, error, fetchLeaderboard }
})
