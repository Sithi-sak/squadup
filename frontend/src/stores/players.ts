import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface PlayerSummary {
  id: string
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

export interface FeedPost {
  id: string
  timeAgo: string
  text: string
  hasImage: boolean
  likes: number
  comments: number
}

export interface AlbumItem {
  id: string
  kind: 'clip' | 'screenshot'
  label: string
  views: number
  likes: number
  shares: number
  durationSeconds: number | null
}

export interface WishItem {
  id: string
  title: string
  game: string
  type: string
  priceCoins: number
  saved: boolean
  /** Which of the Pal's `services` entries "Book" on this wish item opens the Service Detail page for. */
  serviceId: string
}

/** Full Player Profile page data (`/players/:id`), backing all 4 tabs. */
export interface PlayerProfile {
  id: string
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

export const usePlayersStore = defineStore('players', () => {
  const list = ref<PlayerSummary[]>([])
  const filters = ref<PlayerFilters>(emptyFilters())
  const selected = ref<PlayerSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function resetFilters() {
    filters.value = emptyFilters()
  }

  return { list, filters, selected, loading, error, resetFilters }
})
