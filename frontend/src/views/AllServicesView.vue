<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhArrowRight, PhArrowLeft, PhMagnifyingGlass } from '@phosphor-icons/vue'
import gamesTileImage from '@/assets/game.jpg'
import chillingTileImage from '@/assets/chilling.jpg'
import hobbiesImage from '@/assets/hobbies.jpg'
import echatImage from '@/assets/echat.jpg'
import watchTogetherImage from '@/assets/watch_together.jpg'
import valorantCover from '@/assets/game_cover/valorant.png'

type CategoryTab = 'games' | 'chilling'

const categoryTiles: { label: string; tab: CategoryTab; image: string }[] = [
  { label: 'Games', tab: 'games', image: gamesTileImage },
  { label: 'Chilling', tab: 'chilling', image: chillingTileImage },
]

const serviceCards = [
  { label: 'Hobbies Talk', to: '/players', image: hobbiesImage },
  { label: 'E-Chat', to: '/players', image: echatImage },
  { label: 'Watch Together', to: '/players', image: watchTogetherImage },
  { label: 'Valorant', to: { path: '/players', query: { game: 'Valorant' } }, image: valorantCover },
]

const drawerOpen = ref(false)
const activeTab = ref<CategoryTab>('games')
const search = ref('')

const tabItems = [
  { label: 'Games', value: 'games' },
  { label: 'Chilling', value: 'chilling' },
]

function openDrawer(tab: CategoryTab) {
  activeTab.value = tab
  search.value = ''
  drawerOpen.value = true
}

// Placeholder game catalog pending real cover art, mirrors the games already
// used elsewhere in the app (mocks/players.ts, assets/game_cover).
const games = [
  'Apex Legends',
  'CS2',
  'Fortnite',
  'Genshin Impact',
  'League of Legends',
  'Mobile Legends: Bang Bang',
  'Overwatch 2',
  'Valorant',
]

const gameGroups = computed(() => {
  const query = search.value.trim().toLowerCase()
  const filtered = games
    .filter((name) => name.toLowerCase().includes(query))
    .sort((a, b) => a.localeCompare(b))

  const groups = new Map<string, string[]>()
  for (const name of filtered) {
    const letter = name[0]!.toUpperCase()
    if (!groups.has(letter)) groups.set(letter, [])
    groups.get(letter)!.push(name)
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
  <div class="min-h-[calc(100vh-4rem)] px-4 pt-14 pb-8 md:px-6 md:pt-16">
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
            <template v-if="card.image">
              <img :src="card.image" :alt="card.label" class="absolute inset-0 h-full w-full object-cover" />
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
            <UBadge color="primary" variant="solid" size="lg" class="rounded-full text-sm">
              {{ activeTab === 'games' ? 'Regular' : 'Popular' }}
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
                  :key="game"
                  :to="{ path: '/players', query: { game } }"
                  class="relative flex aspect-3/4 items-end overflow-hidden rounded-xl bg-white/5 p-3 ring-1 ring-white/10 transition-colors hover:bg-white/10"
                  @click="drawerOpen = false"
                >
                  <span class="relative text-sm font-medium text-white">{{ game }}</span>
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
