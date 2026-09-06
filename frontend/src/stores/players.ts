import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api, ApiError } from '@/lib/api'
import { formatTimeAgo } from '@/utils/timeAgo'
import type { FeedPost } from './feed'

export interface PlayerSummary {
  id: string
  /** Null for a seed Pal with no linked account yet. Present so a browse card can follow a Pal -
   * `follows` keys on `users.id`, not `players.id` (see `stores/feed.ts`'s `toggleFollow`). */
  userId: string | null
  displayName: string
  avatarUrl: string | null
  games: string[]
  rank: string | null
  role: string | null
  pricePerHour: number | null
  languages: string[]
  rating: number | null
  /** Number of reviews behind `rating`, shown as "(250)" / "(9.5k)" on browse cards. */
  reviewCount: number | null
  /** One-line bio shown on browse cards, e.g. "I'm the duo your friends warned about". */
  tagline: string | null
  /** Squad Coin price per game, shown as "500/Game" on browse cards. */
  priceCoins: number | null
  online: boolean
  isNew: boolean
  /** Promo pill on browse cards, e.g. "10% Off", "1st Order Free". */
  promoBadge: string | null
}

/** Sidebar entry on the Player Profile page, e.g. "eMeow Feeding · 0/Game". */
export interface PlayerServiceListing {
  id: string
  name: string
  promoBadge: string | null
  priceCoins: number
  priceUnit: string
  /** Whether buyers can currently book this service, shown as the toggle on My Services (Pal Dashboard). */
  active?: boolean
}

export interface ServiceTypeOption {
  label: string
  priceCoins: number
  priceUnit: string
  promoBadge: string | null
}

/** Detail panel shown on the Services tab for whichever sidebar entry is selected. */
export interface PlayerServiceDetail {
  title: string
  rating: number | null
  servedCount: number
  description: string
  styles: string[]
  platforms: string[]
  serviceTypes: ServiceTypeOption[]
  /** Checklist shown on the Service Detail page, e.g. "Live voice comms the whole session". */
  whatsIncluded: string[]
  avgResponseTime: string
}

export interface PlayerReview {
  id: string
  author: string
  rating: number
  text: string
  timeAgo: string
  sentiment: 'positive' | 'neutral' | 'negative'
}

export interface AlbumItem {
  id: string
  kind: 'clip' | 'screenshot'
  label: string | null
  views: number
  likes: number
  shares: number
  durationSeconds: number | null
}

export interface WishItem {
  id: string
  title: string
  game: string | null
  type: string | null
  priceCoins: number
  saved: boolean
  /** Which of the Pal's `services` entries "Book" on this wish item opens the Service Detail page
   * for - null means the Pal hasn't linked one, per `WishItemOut.service_id`'s nullable column. */
  serviceId: string | null
}

/** Full Player Profile page data (`/players/:id`), backing all 4 tabs. */
export interface PlayerProfile {
  id: string
  /** The Pal's `users.id` - who a "Message"/"Chat" action starts a thread with (`startThread`
   * in `stores/messages.ts`). Absent on mock/seed profiles that don't back a real account. */
  userId?: string | null
  handle: string
  timezone: string
  language: string
  tier: string
  highlightBadge: string | null
  subscribeLabel: string | null
  services: PlayerServiceListing[]
  highlightedServiceId: string
  serviceDetails: Record<string, PlayerServiceDetail>
  reviews: Record<string, PlayerReview[]>
  feed: FeedPost[]
  album: AlbumItem[]
  wish: WishItem[]
  postsCount: number
  followersCount: number
  followingCount: number
  /** Whether the signed-in viewer follows this Pal - always false for a mock profile or an
   * anonymous viewer. Drives the Follow/Following toggle in `ProfileHeader.vue`. */
  following: boolean
}

export interface PlayerFilters {
  game: string | null
  rank: string | null
  role: string | null
  maxPrice: number | null
  language: string | null
}

function emptyFilters(): PlayerFilters {
  return { game: null, rank: null, role: null, maxPrice: null, language: null }
}

/** `GET/POST /players/me` response shape (backend's `PlayerDetailOut`) — the core,
 * non-social slice of a Pal's own profile: header fields plus services. Reviews/feed/album/wish
 * stay mock-backed until 3.6/3.8 land, so this is narrower than `PlayerProfile` above. */
export interface MyPlayerProfile {
  id: string
  /** Null for a seed Pal with no linked account yet - `PlayerDetailOut.user_id` in
   * `backend/src/backend/routers/players.py`. */
  userId: string | null
  handle: string | null
  displayName: string
  avatarUrl: string | null
  tagline: string | null
  timezone: string | null
  language: string | null
  tier: string | null
  highlightBadge: string | null
  subscribeLabel: string | null
  games: string[]
  rank: string | null
  role: string | null
  languages: string[]
  pricePerHour: number | null
  rating: number | null
  reviewCount: number
  online: boolean
  isNew: boolean
  priceCoins: number | null
  promoBadge: string | null
  services: PlayerServiceListing[]
  highlightedServiceId: string
  serviceDetails: Record<string, PlayerServiceDetail>
  postsCount: number
  followersCount: number
  followingCount: number
  /** Always false on `/players/me` (can't follow yourself) - carried on this type only because
   * `GET /players/{id}` reuses the same backend `PlayerDetailOut` shape. */
  following: boolean
}

/** `POST /players/me/services` and `PATCH /players/me/services/{id}` response shape
 * (backend's `ServiceOut`) — a `PlayerServiceListing` and `PlayerServiceDetail` merged into one
 * object, plus `title` (the detail form of `name`). */
export interface MyService extends PlayerServiceListing, Omit<PlayerServiceDetail, 'title'> {
  title: string
}

/** Fields `PATCH /players/me/services/{id}` accepts (backend's `ServiceUpdateIn`). */
export type ServiceUpdate = Partial<
  Pick<
    MyService,
    'name' | 'description' | 'styles' | 'platforms' | 'whatsIncluded' | 'avgResponseTime' | 'active'
  >
>

/** Narrows a `GET /players/{id}` response down to the `PlayerSummary` shape used by browse
 * cards and the Player Profile header. */
export function playerSummaryFromDetail(p: MyPlayerProfile): PlayerSummary {
  return {
    id: p.id,
    userId: p.userId,
    displayName: p.displayName,
    avatarUrl: p.avatarUrl,
    games: p.games,
    rank: p.rank,
    role: p.role,
    pricePerHour: p.pricePerHour,
    languages: p.languages,
    rating: p.rating,
    reviewCount: p.reviewCount,
    tagline: p.tagline,
    priceCoins: p.priceCoins,
    online: p.online,
    isNew: p.isNew,
    promoBadge: p.promoBadge,
  }
}

/** Expands a `GET /players/{id}` response into the full `PlayerProfile` shape the Player
 * Profile page's tabs expect. Reviews/feed/album/wish come back empty here since they're fetched
 * separately (`fetchPlayerReviews`/`fetchPlayerFeed`/`fetchPlayerAlbum`/`fetchPlayerWish`) and
 * merged in by `usePlayerProfileData` (3.8h) - this only covers the core detail response. */
export function playerProfileFromDetail(p: MyPlayerProfile): PlayerProfile {
  return {
    id: p.id,
    userId: p.userId,
    handle: p.handle ?? `@${p.id.slice(0, 10)}`,
    timezone: p.timezone ?? 'GMT+00:00',
    language: p.language ?? p.languages[0] ?? 'English',
    tier: p.tier ?? 'Pal 1',
    highlightBadge: p.highlightBadge,
    subscribeLabel: p.subscribeLabel,
    services: p.services,
    highlightedServiceId: p.highlightedServiceId,
    serviceDetails: p.serviceDetails,
    reviews: {},
    feed: [],
    album: [],
    wish: [],
    postsCount: p.postsCount,
    followersCount: p.followersCount,
    followingCount: p.followingCount,
    following: p.following,
  }
}

/** `GET /players/me/earnings` response shape (backend's `EarningsOut`, 3.7) - everything
 * derivable from the Pal's own completed bookings. Payout method/schedule/history/pending
 * clearance stay on `mocks/dashboardStats.ts` for now since those need a real payout ledger
 * (3.9), not just booking history. */
export interface PlayerEarnings {
  lifetimeEarnedCoins: number
  lifetimeEarnedChangePct: number | null
  coinsThisMonth: number
  coinsThisMonthChangePct: number | null
  ordersCompleted: number
  ordersCompletedThisWeek: number
  responseRatePct: number
  earningsThisWeek: { label: string; coins: number }[]
  earningsOverview: { label: string; coins: number }[]
}

/** `GET /reviews/player/{id}` response shape (backend's `ReviewOut`, grouped by `serviceId`). */
interface ReviewApiOut {
  id: string
  author: string
  rating: number
  text: string | null
  sentiment: 'positive' | 'neutral' | 'negative'
  createdAt: string
}

function reviewsFromApi(grouped: Record<string, ReviewApiOut[]>): Record<string, PlayerReview[]> {
  return Object.fromEntries(
    Object.entries(grouped).map(([serviceId, reviews]) => [
      serviceId,
      reviews.map((r) => ({
        id: r.id,
        author: r.author,
        rating: r.rating,
        text: r.text ?? '',
        timeAgo: formatTimeAgo(r.createdAt),
        sentiment: r.sentiment,
      })),
    ]),
  )
}

export const usePlayersStore = defineStore('players', () => {
  const list = ref<PlayerSummary[]>([])
  const filters = ref<PlayerFilters>(emptyFilters())
  const selected = ref<PlayerSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const suggested = ref<PlayerSummary[]>([])
  const suggestedLoading = ref(false)

  const gameCounts = ref<Record<string, number>>({})

  const mine = ref<MyPlayerProfile | null>(null)
  const mineLoading = ref(false)
  const mineError = ref<string | null>(null)

  const earnings = ref<PlayerEarnings | null>(null)
  const earningsLoading = ref(false)
  const earningsError = ref<string | null>(null)

  function resetFilters() {
    filters.value = emptyFilters()
  }

  /** Loads the real Browse Players catalog (`GET /players`) into `list`. `limit` takes a fast
   * top-rated-only path on the backend (see `list_players`) for callers like Home/Landing that
   * only need a small rail, not the full catalog to filter/search over. */
  async function fetchList(params: { q?: string; game?: string; limit?: number } = {}) {
    loading.value = true
    error.value = null
    try {
      const query = new URLSearchParams()
      if (params.q) query.set('q', params.q)
      if (params.game) query.set('game', params.game)
      if (params.limit) query.set('limit', String(params.limit))
      const qs = query.toString()
      list.value = await api.get<PlayerSummary[]>(`/players${qs ? `?${qs}` : ''}`)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load players'
      list.value = []
    } finally {
      loading.value = false
    }
  }

  /** Feed's right rail "Suggested Pals" (`GET /players/suggested`). No mock fallback - a Pal
   * with nothing to suggest yet is a normal empty state, same convention as the profile tabs
   * below, so `FeedRightRail.vue` just hides the section rather than showing fake names. */
  async function fetchSuggested() {
    suggestedLoading.value = true
    try {
      suggested.value = await api.get<PlayerSummary[]>('/players/suggested')
    } catch {
      suggested.value = []
    } finally {
      suggestedLoading.value = false
    }
  }

  /** "Browse by game" rails' real Pal-per-game counts (`GET /players/game-counts`), keyed by the
   * same slug `data/games.ts`'s `slugify()` derives a game's `id` from. Empty on failure - same
   * "empty is a normal state" convention as `fetchSuggested`, since a 0 count reads the same as
   * a missing one on the card. */
  async function fetchGameCounts() {
    try {
      gameCounts.value = await api.get<Record<string, number>>('/players/game-counts')
    } catch {
      gameCounts.value = {}
    }
  }

  /** Loads the signed-in user's own Pal profile + services (`GET /players/me`). A 404 means
   * they haven't completed Become a Player yet, so it clears `mine` rather than setting
   * `mineError` — callers use `mine === null` to decide whether to show that flow. */
  async function fetchMine() {
    mineLoading.value = true
    mineError.value = null
    try {
      mine.value = await api.get<MyPlayerProfile>('/players/me')
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        mine.value = null
      } else {
        mineError.value = err instanceof Error ? err.message : 'Failed to load player profile'
      }
    } finally {
      mineLoading.value = false
    }
  }

  /** Become a Player submission (`POST /players/me`, multipart — see `lib/api.ts`'s `FormData`
   * handling). */
  async function createMine(formData: FormData) {
    mine.value = await api.post<MyPlayerProfile>('/players/me', formData)
    return mine.value
  }

  /** Create Service submission (`POST /players/me/services`, multipart). Refetches `mine` so
   * derived fields (e.g. `highlightedServiceId`, the profile-level `priceCoins`) stay correct
   * rather than re-deriving them client-side. */
  async function createService(formData: FormData) {
    const service = await api.post<MyService>('/players/me/services', formData)
    await fetchMine()
    return service
  }

  async function updateService(serviceId: string, patch: ServiceUpdate) {
    const service = await api.patch<MyService>(`/players/me/services/${serviceId}`, patch)
    await fetchMine()
    return service
  }

  async function deleteService(serviceId: string) {
    await api.delete(`/players/me/services/${serviceId}`)
    await fetchMine()
  }

  /** Player Dashboard / Earnings (3.7): `GET /players/me/earnings`. A 404 (no Pal profile yet)
   * just clears `earnings` rather than setting `earningsError`, same convention as `fetchMine`. */
  async function fetchEarnings() {
    earningsLoading.value = true
    earningsError.value = null
    try {
      earnings.value = await api.get<PlayerEarnings>('/players/me/earnings')
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        earnings.value = null
      } else {
        earningsError.value = err instanceof Error ? err.message : 'Failed to load earnings'
      }
    } finally {
      earningsLoading.value = false
    }
  }

  /** Loads any Pal's public profile (`GET /players/{id}`). Throws (404, or a Postgres error for
   * an id that isn't a valid uuid — e.g. the seed mock ids) when there's no DB-backed profile for
   * `id`; callers fall back to mock data in that case. */
  async function fetchPlayer(id: string) {
    return api.get<MyPlayerProfile>(`/players/${id}`)
  }

  /** Player Profile's Services tab reviews (`GET /reviews/player/{id}`, public). Returns an
   * empty record on failure rather than throwing, since a Pal with no reviews yet is a normal
   * empty state, not an error. */
  async function fetchPlayerReviews(id: string): Promise<Record<string, PlayerReview[]>> {
    try {
      return reviewsFromApi(await api.get<Record<string, ReviewApiOut[]>>(`/reviews/player/${id}`))
    } catch {
      return {}
    }
  }

  /** Player Profile's Feeds tab (`GET /players/{id}/feed`, public, 3.8h). Same empty-on-failure
   * convention as `fetchPlayerReviews` - a Pal with no posts yet is a normal empty state. */
  async function fetchPlayerFeed(id: string): Promise<FeedPost[]> {
    try {
      return await api.get<FeedPost[]>(`/players/${id}/feed`)
    } catch {
      return []
    }
  }

  /** Player Profile's Album tab (`GET /players/{id}/album`, public, 3.8h). */
  async function fetchPlayerAlbum(id: string): Promise<AlbumItem[]> {
    try {
      return await api.get<AlbumItem[]>(`/players/${id}/album`)
    } catch {
      return []
    }
  }

  /** Player Profile's Wish tab (`GET /players/{id}/wish`, public, 3.8h). Already filtered to
   * `saved = true` server-side (3.8b), so every item here is "still wished for". */
  async function fetchPlayerWish(id: string): Promise<WishItem[]> {
    try {
      return await api.get<WishItem[]>(`/players/${id}/wish`)
    } catch {
      return []
    }
  }

  return {
    list,
    filters,
    selected,
    loading,
    error,
    resetFilters,
    fetchList,
    suggested,
    suggestedLoading,
    fetchSuggested,
    gameCounts,
    fetchGameCounts,
    mine,
    mineLoading,
    mineError,
    fetchMine,
    createMine,
    createService,
    updateService,
    deleteService,
    fetchPlayer,
    fetchPlayerReviews,
    fetchPlayerFeed,
    fetchPlayerAlbum,
    fetchPlayerWish,
    earnings,
    earningsLoading,
    earningsError,
    fetchEarnings,
  }
})
