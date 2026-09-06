<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import { usePlayersStore, type PlayerSummary } from '@/stores/players'
import PlayerCard from '@/components/players/PlayerCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const playersStore = usePlayersStore()

const allPlayers = computed<PlayerSummary[]>(() => playersStore.list)

interface FilterChip {
  key: string
  label: string
  predicate: ((player: PlayerSummary) => boolean) | null
}

const route = useRoute()
const router = useRouter()

const query = computed(() => (typeof route.query.q === 'string' ? route.query.q : ''))
const gameFilter = computed(() => (typeof route.query.game === 'string' ? route.query.game : ''))
const isGameMode = computed(() => gameFilter.value.length > 0)

/** `game` drives the backend's match-score default order (3.3: game 40 / rank 30 / role 20 /
 * availability 10) — refetch whenever it changes so the ranking stays relevant to the page
 * being viewed, not just whatever game was active on first mount. */
onMounted(() => playersStore.fetchList({ game: gameFilter.value || undefined }))
watch(gameFilter, (game) => playersStore.fetchList({ game: game || undefined }))

const searchInput = ref(query.value)
watch(query, (value) => (searchInput.value = value))

function executeSearch() {
  router.push({ path: '/players', query: searchInput.value ? { q: searchInput.value } : {} })
}

function clearSearch() {
  searchInput.value = ''
  router.push({ path: '/players', query: {} })
}

const searchChips: FilterChip[] = [
  { key: 'new', label: 'New Pals', predicate: (p) => p.isNew },
  { key: 'free', label: '1st Order Free', predicate: (p) => p.promoBadge === '1st Order Free' },
  { key: 'discount', label: 'Discount', predicate: (p) => !!p.promoBadge },
  { key: 'online', label: 'Online now', predicate: (p) => p.online },
  { key: 'verified', label: 'Verified', predicate: (p) => p.rating != null },
]

const gameChips: FilterChip[] = [
  { key: 'estar', label: 'eStar', predicate: (p) => (p.rating ?? 0) >= 4.8 },
  { key: 'new', label: 'New Pals', predicate: (p) => p.isNew },
  { key: 'free', label: '1st Order Free', predicate: (p) => p.promoBadge === '1st Order Free' },
  {
    key: 'first-discount',
    label: '1st Order Discount',
    predicate: (p) => !!p.promoBadge && p.promoBadge.startsWith('1st Order') && p.promoBadge !== '1st Order Free',
  },
  { key: 'discount', label: 'Discount', predicate: (p) => p.promoBadge === '10% Off' },
  { key: 'more', label: 'More filters', predicate: null },
]

const chips = computed(() => (isGameMode.value ? gameChips : searchChips))
const activeChips = ref<Set<string>>(new Set())
watch(isGameMode, () => (activeChips.value = new Set()))

function toggleChip(chip: FilterChip) {
  if (!chip.predicate) return
  const next = new Set(activeChips.value)
  if (next.has(chip.key)) next.delete(chip.key)
  else next.add(chip.key)
  activeChips.value = next
}

const sortOptions = computed(() =>
  isGameMode.value
    ? ['General', 'Highest rated', 'Price: Low to High', 'Price: High to Low']
    : ['Relevance', 'Highest rated', 'Price: Low to High', 'Price: High to Low'],
)
const sortBy = ref(sortOptions.value[0])
watch(sortOptions, (options) => (sortBy.value = options[0]!))

const matchedPlayers = computed(() => {
  if (isGameMode.value) {
    const game = gameFilter.value.toLowerCase()
    return allPlayers.value.filter((p) => p.games.some((g) => g.toLowerCase() === game))
  }
  if (!query.value) return allPlayers.value
  const q = query.value.toLowerCase()
  return allPlayers.value.filter(
    (p) =>
      p.displayName.toLowerCase().includes(q) ||
      p.games.some((g) => g.toLowerCase().includes(q)) ||
      p.tagline?.toLowerCase().includes(q),
  )
})

const visiblePlayers = computed(() => {
  const activeChipList = chips.value.filter((c) => activeChips.value.has(c.key))
  const filtered = matchedPlayers.value.filter((p) =>
    activeChipList.every((chip) => chip.predicate?.(p)),
  )

  const sorted = [...filtered]
  if (sortBy.value === 'Highest rated') {
    sorted.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))
  } else if (sortBy.value === 'Price: Low to High') {
    sorted.sort((a, b) => (a.priceCoins ?? 0) - (b.priceCoins ?? 0))
  } else if (sortBy.value === 'Price: High to Low') {
    sorted.sort((a, b) => (b.priceCoins ?? 0) - (a.priceCoins ?? 0))
  }
  return sorted
})

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] pb-14">
    <div v-if="isGameMode" class="border-b border-white/10 bg-white/3 px-4 py-12 md:px-6 md:py-16">
      <div class="mx-auto max-w-4/5">
        <h1 class="text-4xl font-bold text-white md:text-5xl">{{ gameFilter }}</h1>
        <p class="mt-2 text-slate-400">{{ formatCount(matchedPlayers.length) }} Pals</p>
      </div>
    </div>

    <div v-else class="px-4 pt-8 md:px-6">
      <div class="mx-auto max-w-4/5">
        <div class="flex items-center gap-3">
          <UInput
            v-model="searchInput"
            placeholder="Search"
            size="xl"
            variant="subtle"
            class="flex-1 rounded-full"
            :ui="{ base: 'rounded-full' }"
            @keyup.enter="executeSearch"
          >
            <template #leading>
              <PhMagnifyingGlass :size="18" weight="bold" />
            </template>
          </UInput>
          <UButton color="primary" size="xl" class="rounded-full px-6" @click="executeSearch">
            Search
          </UButton>
        </div>

        <div class="mt-5 flex flex-wrap items-center justify-between gap-3">
          <p class="text-sm text-slate-400">
            <span class="font-semibold text-white">{{ visiblePlayers.length.toLocaleString() }} Pals</span>
            <template v-if="query"> match "{{ query }}"</template>
          </p>
          <div class="flex items-center gap-2">
            <UButton color="primary" variant="solid" size="sm" class="rounded-full">Pals</UButton>
            <span class="rounded-full bg-white/5 px-3.5 py-1.5 text-sm text-slate-400">Games</span>
            <span class="rounded-full bg-white/5 px-3.5 py-1.5 text-sm text-slate-400">eStars</span>
          </div>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-4/5 px-4 pt-6 md:px-6">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div class="flex flex-wrap items-center gap-2">
          <template v-for="chip in chips" :key="chip.key">
            <UButton
              v-if="chip.predicate"
              :color="activeChips.has(chip.key) ? 'primary' : 'neutral'"
              :variant="activeChips.has(chip.key) ? 'solid' : 'soft'"
              size="sm"
              class="rounded-full"
              @click="toggleChip(chip)"
            >
              {{ chip.label }}
            </UButton>
            <span v-else class="rounded-full bg-white/5 px-3.5 py-1.5 text-sm text-slate-400">
              {{ chip.label }}
            </span>
          </template>
        </div>
        <div class="flex items-center gap-2 text-sm text-slate-400">
          <span class="hidden sm:inline">Sort by</span>
          <USelect
            v-model="sortBy"
            :items="sortOptions"
            size="sm"
            variant="subtle"
            class="w-44"
            :ui="{ base: 'rounded-full' }"
          />
        </div>
      </div>

      <div v-if="visiblePlayers.length === 0 && query" class="py-6">
        <EmptyState
          :icon="PhMagnifyingGlass"
          badge="No results"
          :title="`No results for “${query}”`"
          description="Check your spelling, or try a different game, service, or Pal name."
        >
          <template #actions>
            <UButton color="primary" class="rounded-full px-6" @click="clearSearch">Browse all Pals</UButton>
            <UButton color="neutral" variant="soft" class="rounded-full px-6" @click="clearSearch">
              Clear search
            </UButton>
          </template>
        </EmptyState>
      </div>
      <div v-else-if="visiblePlayers.length === 0" class="py-16">
        <UEmpty title="No Pals match your filters" class="text-white" />
      </div>
      <div v-else class="grid grid-cols-1 gap-4 py-6 sm:grid-cols-2 lg:grid-cols-4">
        <PlayerCard v-for="player in visiblePlayers" :key="player.id" :player="player" />
      </div>
    </div>
  </div>
</template>
