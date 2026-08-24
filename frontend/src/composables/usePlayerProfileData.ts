import { computed, ref, watch, type Ref } from 'vue'
import { mockPlayers } from '@/mocks/players'
import { getPlayerProfile } from '@/mocks/playerProfiles'
import type { FeedPost } from '@/stores/feed'
import {
  playerProfileFromDetail,
  playerSummaryFromDetail,
  usePlayersStore,
  type AlbumItem,
  type PlayerProfile,
  type PlayerReview,
  type PlayerSummary,
  type WishItem,
} from '@/stores/players'

/** Backs both the Player Profile page and Service Detail page: loads a Pal's profile from
 * `GET /players/{id}` and falls back to the authored `mocks/playerProfiles.ts` data when there's
 * no DB-backed profile for `id` yet (the seed Pals `p1`..`p8`, per 3.1j). */
export function usePlayerProfileData(id: Ref<string>) {
  const playersStore = usePlayersStore()

  const loading = ref(true)
  const fetchedDetail = ref<Awaited<ReturnType<typeof playersStore.fetchPlayer>> | null>(null)
  const fetchedReviews = ref<Record<string, PlayerReview[]>>({})
  const fetchedFeed = ref<FeedPost[]>([])
  const fetchedAlbum = ref<AlbumItem[]>([])
  const fetchedWish = ref<WishItem[]>([])

  watch(
    id,
    async (playerId) => {
      loading.value = true
      fetchedDetail.value = null
      fetchedReviews.value = {}
      fetchedFeed.value = []
      fetchedAlbum.value = []
      fetchedWish.value = []
      try {
        fetchedDetail.value = await playersStore.fetchPlayer(playerId)
        ;[fetchedReviews.value, fetchedFeed.value, fetchedAlbum.value, fetchedWish.value] = await Promise.all([
          playersStore.fetchPlayerReviews(playerId),
          playersStore.fetchPlayerFeed(playerId),
          playersStore.fetchPlayerAlbum(playerId),
          playersStore.fetchPlayerWish(playerId),
        ])
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
      ? {
          ...playerProfileFromDetail(fetchedDetail.value),
          reviews: fetchedReviews.value,
          feed: fetchedFeed.value,
          album: fetchedAlbum.value,
          wish: fetchedWish.value,
        }
      : getPlayerProfile(mockPlayer.value),
  )
  /** Whether `profile` came from a real (DB-backed) row vs. the authored mock fixtures - callers
   * use this to gate features that only make sense against real data, e.g. `ProfileWishTab.vue`'s
   * save toggle (3.8b's `wish_items.saved` decision). */
  const isMockProfile = computed(() => !fetchedDetail.value)

  return { loading, player, profile, isMockProfile }
}
