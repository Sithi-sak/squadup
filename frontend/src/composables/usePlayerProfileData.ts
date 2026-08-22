import { computed, ref, watch, type Ref } from 'vue'
import { mockPlayers } from '@/mocks/players'
import { getPlayerProfile } from '@/mocks/playerProfiles'
import {
  playerProfileFromDetail,
  playerSummaryFromDetail,
  usePlayersStore,
  type PlayerProfile,
  type PlayerSummary,
} from '@/stores/players'

/** Backs both the Player Profile page and Service Detail page: loads a Pal's profile from
 * `GET /players/{id}` and falls back to the authored `mocks/playerProfiles.ts` data when there's
 * no DB-backed profile for `id` yet (the seed Pals `p1`..`p8`, per 3.1j). */
export function usePlayerProfileData(id: Ref<string>) {
  const playersStore = usePlayersStore()

  const loading = ref(true)
  const fetchedDetail = ref<Awaited<ReturnType<typeof playersStore.fetchPlayer>> | null>(null)

  watch(
    id,
    async (playerId) => {
      loading.value = true
      fetchedDetail.value = null
      try {
        fetchedDetail.value = await playersStore.fetchPlayer(playerId)
      } catch {
        fetchedDetail.value = null
      } finally {
        loading.value = false
      }
    },
    { immediate: true },
  )

  const mockPlayer = computed(() => mockPlayers.find((p) => p.id === id.value) ?? mockPlayers[0]!)

  const player = computed<PlayerSummary>(() =>
    fetchedDetail.value ? playerSummaryFromDetail(fetchedDetail.value) : mockPlayer.value,
  )
  const profile = computed<PlayerProfile>(() =>
    fetchedDetail.value
      ? playerProfileFromDetail(fetchedDetail.value)
      : getPlayerProfile(mockPlayer.value),
  )

  return { loading, player, profile }
}
