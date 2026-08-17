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
