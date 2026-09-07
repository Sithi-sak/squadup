<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PhArrowRight, PhArrowLeft, PhMagnifyingGlass } from '@phosphor-icons/vue'
import gamesTileImage from '@/assets/game.jpg'
import chillingTileImage from '@/assets/chilling.jpg'
import hobbiesImage from '@/assets/hobbies.jpg'
import echatImage from '@/assets/echat.jpg'
import watchTogetherImage from '@/assets/watch_together.jpg'
import { gameCoverUrl, useCoverManifest } from '@/lib/covers'
import { games, type Game } from '@/data/games'

type CategoryTab = 'games' | 'chilling'

const categoryTiles: { label: string; tab: CategoryTab; image: string }[] = [
  { label: 'Games', tab: 'games', image: gamesTileImage },
  { label: 'Chilling', tab: 'chilling', image: chillingTileImage },
]

const serviceCards: { label: string; to: string | { path: string; query: Record<string, string> }; image?: string; gameSlug?: string }[] = [
  { label: 'Hobbies Talk', to: '/players', image: hobbiesImage },
  { label: 'E-Chat', to: '/players', image: echatImage },
  { label: 'Watch Together', to: '/players', image: watchTogetherImage },
  { label: 'Valorant', to: { path: '/players', query: { game: 'Valorant' } }, gameSlug: 'valorant' },
]

const coverFilenames = useCoverManifest()

function coverSrc(slug: string): string | undefined {
  const filename = coverFilenames.value.get(slug)
  return filename ? gameCoverUrl(slug, filename) : undefined
}

function serviceCardImage(card: (typeof serviceCards)[number]): string | undefined {
  return card.image ?? (card.gameSlug ? coverSrc(card.gameSlug) : undefined)
}

const drawerOpen = ref(false)
const activeTab = ref<CategoryTab>('games')
const search = ref('')

type GameFilter = 'all' | 'multiplayer'
const gameFilter = ref<GameFilter>('all')

const tabItems = [
  { label: 'Games', value: 'games' },
  { label: 'Chilling', value: 'chilling' },
]

function openDrawer(tab: CategoryTab) {
  activeTab.value = tab
  search.value = ''
  gameFilter.value = 'all'
  drawerOpen.value = true
}

const route = useRoute()

onMounted(() => {
  const tab = route.query.tab
  if (tab === 'games' || tab === 'chilling') {
    openDrawer(tab)
  }
})

const gameGroups = computed(() => {
  const query = search.value.trim().toLowerCase()
  const filtered = games
    .filter((game) => game.name.toLowerCase().includes(query))
    .filter((game) => gameFilter.value === 'all' || (game.ranks && game.ranks.length > 0))
    .sort((a, b) => a.name.localeCompare(b.name))

  const groups = new Map<string, Game[]>()
  for (const game of filtered) {
    const letter = game.name[0]!.toUpperCase()
    if (!groups.has(letter)) groups.set(letter, [])
    groups.get(letter)!.push(game)
  }
  return Array.from(groups.entries()).map(([letter, items]) => ({ letter, items }))
})

const chillingSections = [
  {
    title: 'Popular',
    items: [
      { label: 'Just Chatting', caption: 'Talk about anything' },
      { label: 'Watch Together', caption: 'Movies & streaming' },
      { label: 'Hobbies Talk', caption: 'Share what you love' },
      { label: 'E-Chat', caption: 'Voice call & chilling' },
    ],
  },
  {
    title: 'More ways to chill',
    items: [
      { label: 'Vent & Support', caption: 'A kind listener' },
      { label: 'Truth or Dare', caption: 'Break the ice' },
      { label: 'Study Together', caption: 'Focus co-working' },
      { label: 'Movie Night', caption: 'Watch together' },
      { label: 'Listen Together', caption: 'Share your playlist' },
    ],
  },
]

const filteredChillingSections = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return chillingSections
  return chillingSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => item.label.toLowerCase().includes(query)),
    }))
    .filter((section) => section.items.length > 0)
})
</script>

<template>
  <div class="min-h-[calc(100vh-65px)] px-4 pt-14 pb-8 md:px-6 md:pt-16">
    <div class="mx-auto max-w-5xl">
      <div class="mx-auto max-w-8xl">
        <h1 class="mb-6 text-3xl font-bold text-white">All Services</h1>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <button
            v-for="tile in categoryTiles"
            :key="tile.label"
            type="button"
            class="relative flex h-28 items-center justify-between overflow-hidden rounded-xl bg-cover bg-center px-6 py-4 text-left md:h-36"
            :style="{ backgroundImage: `url(${tile.image})` }"
            @click="openDrawer(tile.tab)"
          >
            <div class="absolute inset-0 bg-squadup-dark/60 transition-colors hover:bg-squadup-dark/20" />
            <span class="relative text-lg font-semibold text-white">{{ tile.label }}</span>
            <PhArrowRight :size="20" class="relative text-white" weight="bold" />
          </button>
        </div>

        <div class="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <router-link
            v-for="card in serviceCards"
            :key="card.label"
            :to="card.to"
            class="relative flex aspect-10/16 flex-col justify-end overflow-hidden rounded-xl bg-gray-800/70"
          >
            <template v-if="serviceCardImage(card)">
              <img
                :src="serviceCardImage(card)"
                :alt="card.label"
                class="absolute inset-0 h-full w-full object-cover"
              />
              <div
                class="absolute inset-0 bg-linear-to-t from-squadup-dark via-squadup-dark/15 to-transparent"
              />
            </template>
            <span class="relative px-4 pb-4 font-semibold text-white">{{ card.label }}</span>
          </router-link>
        </div>
      </div>
    </div>

    <UDrawer
      v-model:open="drawerOpen"
      direction="right"
      :handle="false"
      :ui="{ content: 'w-full sm:max-w-3xl', container: 'p-0 gap-0' }"
    >
      <template #body>
        <div class="sticky top-0 z-10 bg-default p-4 pb-3">
          <div class="flex items-center gap-3">
            <UButton
              color="neutral"
              variant="ghost"
              square
              :ui="{ base: 'rounded-full' }"
              aria-label="Close"
              @click="drawerOpen = false"
            >
              <PhArrowLeft :size="18" weight="bold" />
            </UButton>
            <h2 class="text-xl font-bold text-white">All Services</h2>
          </div>

          <UTabs
            v-model="activeTab"
            variant="link"
            :items="tabItems"
            :content="false"
            class="mt-4 w-fit"
            :ui="{ label: 'text-white' }"
          />

          <div class="mt-4 flex items-center justify-between gap-3">
            <div v-if="activeTab === 'games'" class="flex items-center gap-2">
              <UButton
                :color="gameFilter === 'all' ? 'primary' : 'neutral'"
                :variant="gameFilter === 'all' ? 'solid' : 'soft'"
                size="sm"
                class="rounded-full"
                @click="gameFilter = 'all'"
              >
                Regular
              </UButton>
              <UButton
                :color="gameFilter === 'multiplayer' ? 'primary' : 'neutral'"
                :variant="gameFilter === 'multiplayer' ? 'solid' : 'soft'"
                size="sm"
                class="rounded-full"
                @click="gameFilter = 'multiplayer'"
              >
                Multiplayer games
              </UButton>
            </div>
            <UBadge v-else color="primary" variant="solid" size="lg" class="rounded-full text-sm">
              Popular
            </UBadge>
            <UInput
              v-model="search"
              placeholder="Search"
              variant="subtle"
              class="w-48 rounded-full sm:w-64"
              :ui="{ base: 'rounded-full' }"
            >
              <template #leading>
                <PhMagnifyingGlass :size="16" weight="bold" />
              </template>
            </UInput>
          </div>
        </div>

        <div class="px-4 pt-2 pb-6">
          <template v-if="activeTab === 'games'">
            <div v-if="gameGroups.length === 0" class="py-10 text-center text-sm text-slate-400">
              No games match "{{ search }}".
            </div>
            <div v-for="group in gameGroups" :key="group.letter" class="mb-6">
              <h3 class="mb-3 text-sm font-semibold text-slate-400">{{ group.letter }}</h3>
              <div class="grid grid-cols-3 gap-3 sm:grid-cols-4">
                <router-link
                  v-for="game in group.items"
                  :key="game.id"
                  :to="{ path: '/players', query: { game: game.name } }"
                  class="relative flex aspect-2/3 items-end overflow-hidden rounded-xl p-3 transition-all hover:scale-105"
                  @click="drawerOpen = false"
                >
                  <template v-if="coverSrc(game.id)">
                    <img
                      :src="coverSrc(game.id)"
                      :alt="game.name"
                      class="absolute inset-0 h-full w-full object-cover"
                    />
                    <div
                      class="absolute inset-0 bg-linear-to-t from-squadup-dark via-squadup-dark/15 to-transparent"
                    />
                  </template>
                  <span class="relative text-sm font-medium text-white">{{ game.name }}</span>
                </router-link>
              </div>
            </div>
          </template>

          <template v-else>
            <div v-if="filteredChillingSections.length === 0" class="py-10 text-center text-sm text-slate-400">
              No results match "{{ search }}".
            </div>
            <div v-for="section in filteredChillingSections" :key="section.title" class="mb-6">
              <h3 class="mb-3 text-sm font-medium text-slate-400">{{ section.title }}</h3>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <router-link
                  v-for="item in section.items"
                  :key="item.label"
                  to="/players"
                  class="relative flex aspect-3/2 flex-col justify-end overflow-hidden rounded-xl bg-white/5 p-4 ring-1 ring-white/10 transition-colors hover:bg-white/10"
                  @click="drawerOpen = false"
                >
                  <span class="font-semibold text-white">{{ item.label }}</span>
                  <span class="text-sm text-slate-400">{{ item.caption }}</span>
                </router-link>
              </div>
            </div>
          </template>
        </div>
      </template>
    </UDrawer>
  </div>
</template>
