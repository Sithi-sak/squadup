<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhMagnifyingGlass,
  PhUserCircle,
  PhCaretLeft,
  PhCaretRight,
} from '@phosphor-icons/vue'
import { usePlayersStore } from '@/stores/players'
import { gameCoverUrl, useCoverManifest } from '@/lib/covers'
import { featuredGames } from '@/data/games'
import { resolveAvatarUrl } from '@/utils/avatar'

const router = useRouter()
const playersStore = usePlayersStore()

const searchQuery = ref('')

const quickGames = ['Valorant', 'League of Legends', 'Fortnite', 'Apex Legends', 'Overwatch 2']

const coverFilenames = useCoverManifest()

function coverSrc(slug: string): string | undefined {
  const filename = coverFilenames.value.get(slug)
  return filename ? gameCoverUrl(slug, filename) : undefined
}

const topPlayers = computed(() =>
  [...playersStore.list].sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0)).slice(0, 8),
)

const servicesRail = ref<HTMLElement | null>(null)
const canScrollServicesLeft = ref(false)
const canScrollServicesRight = ref(false)

function updateServicesScrollState() {
  const el = servicesRail.value
  if (!el) return
  canScrollServicesLeft.value = el.scrollLeft > 0
  canScrollServicesRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 1
}

function scrollServices(direction: 'left' | 'right') {
  const el = servicesRail.value
  if (!el) return
  const amount = el.clientWidth * 0.8 * (direction === 'left' ? -1 : 1)
  el.scrollBy({ left: amount, behavior: 'smooth' })
}

const stats = [
  { value: '100+', label: 'Games' },
  { value: '4K+', label: 'Verified Pals' },
  { value: '4.9★', label: 'Avg rating' },
  { value: '200K+', label: 'Matches played' },
]

function goToPlayers(game?: string) {
  router.push({ path: '/players', query: game ? { game } : undefined })
}

onMounted(() => {
  updateServicesScrollState()
  if (!playersStore.list.length) playersStore.fetchList({ limit: 8 })
  playersStore.fetchGameCounts()
})

function handleSearch() {
  router.push({
    path: '/players',
    query: searchQuery.value ? { q: searchQuery.value } : undefined,
  })
}
</script>

<template>
  <div class="flex flex-col">
    <!-- Hero -->
    <section
      class="px-4 py-16 md:px-6 md:py-22"
      style="
        background:
          radial-gradient(
            ellipse 80% 60% at 50% 100%,
            color-mix(in srgb, var(--color-brand-600) 35%, transparent),
            transparent
          ),
          var(--color-squadup-bg);
      "
    >
      <div class="mx-auto max-w-190 text-center">
        <h1 class="text-4xl leading-tight font-bold text-white md:text-5xl">
          You Will Never <span class="text-brand-500">Walk Alone</span>
        </h1>
        <p class="mx-auto mt-5 max-w-140 text-[15px] leading-relaxed text-slate-300">
          Team up, make friends, and have fun. Book a top-tier gaming companion in seconds and
          never play solo again.
        </p>

        <div
          class="mx-auto mt-8 flex max-w-155 items-center gap-2 rounded-full border border-white/10 bg-white/5 py-1.5 pr-1.5 pl-5"
        >
          <PhMagnifyingGlass :size="18" class="shrink-0 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search a game, e.g. Valorant, League of Legends..."
            class="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-400"
            @keyup.enter="handleSearch"
          />
          <UButton color="primary" class="rounded-full px-5" @click="handleSearch">
            Find my Pal
          </UButton>
        </div>

        <div class="mt-5 flex flex-wrap justify-center gap-2.5">
          <button
            v-for="game in quickGames"
            :key="game"
            type="button"
            class="cursor-pointer rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-[13px] text-slate-300 hover:border-brand-600 hover:text-white"
            @click="goToPlayers(game)"
          >
            {{ game }}
          </button>
        </div>
      </div>
    </section>

    <!-- All Services -->
    <section class="px-4 py-10 md:px-6 md:py-14">
      <div class="mx-auto max-w-4/5">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-2xl font-bold text-white">All Services</h2>
          <div class="hidden items-center gap-2 md:flex">
            <button
              type="button"
              aria-label="Scroll left"
              class="flex size-9 cursor-pointer items-center justify-center rounded-full bg-white/5 text-white hover:border-brand-600 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-white/10"
              :disabled="!canScrollServicesLeft"
              @click="scrollServices('left')"
            >
              <PhCaretLeft :size="16" weight="bold" />
            </button>
            <button
              type="button"
              aria-label="Scroll right"
              class="flex size-9 cursor-pointer items-center justify-center rounded-full bg-white/5 text-white hover:border-brand-600 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-white/10"
              :disabled="!canScrollServicesRight"
              @click="scrollServices('right')"
            >
              <PhCaretRight :size="16" weight="bold" />
            </button>
          </div>
        </div>
        <div
          ref="servicesRail"
          class="scrollbar-none grid auto-cols-50 grid-flow-col gap-4 overflow-x-auto"
          @scroll="updateServicesScrollState"
        >
          <router-link
            v-for="game in featuredGames"
            :key="game.id"
            :to="{ path: '/players', query: { game: game.name } }"
            class="relative flex aspect-10/16 flex-col justify-end overflow-hidden rounded-xl"
          >
            <img
              v-if="coverSrc(game.id)"
              :src="coverSrc(game.id)"
              :alt="game.name"
              class="absolute inset-0 h-full w-full object-cover"
              loading="lazy"
            />
            <div
              class="absolute inset-0 bg-linear-to-t from-squadup-dark via-squadup-dark/15 to-transparent"
            />
            <div class="relative flex flex-col gap-0.5 px-3 pb-3">
              <span class="text-md font-semibold text-white">{{ game.name }}</span>
              <span class="text-sm text-slate-300">
                {{ (playersStore.gameCounts[game.id] ?? 0).toLocaleString() }} Pals
              </span>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- Top Pal -->
    <section v-if="topPlayers.length" class="px-4 py-10 md:px-6 md:py-14">
      <div class="mx-auto max-w-4/5">
        <h2 class="mb-5 text-2xl font-bold text-white">Top Pal</h2>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <button
            v-for="player in topPlayers"
            :key="player.id"
            type="button"
            class="flex cursor-pointer flex-col items-center gap-3 rounded-2xl bg-gray-800/70 p-5 text-center transition-colors hover:bg-gray-800"
            @click="router.push(`/players/${player.id}`)"
          >
            <UAvatar
              :src="resolveAvatarUrl(player.id, player.avatarUrl)"
              size="2xl"
              class="bg-squadup-bg text-brand-300 ring-2 ring-brand-300/60"
            >
              <PhUserCircle :size="32" />
            </UAvatar>
            <div>
              <p class="font-semibold text-white">{{ player.displayName }}</p>
              <p class="text-xs text-slate-400">{{ player.games[0] }} · {{ player.rating ?? '—' }}</p>
            </div>
          </button>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="bg-squadup-bg px-4 py-14 text-center md:py-16">
      <div class="mx-auto max-w-160">
        <h2 class="text-[28px] font-bold text-white">Ready to squad up?</h2>
        <p class="mt-3 text-sm text-slate-300">
          Join hundreds of players who never battle alone. Your next win is one click away.
        </p>
        <div class="mt-6 flex justify-center gap-3">
          <UButton
            color="neutral"
            variant="solid"
            class="rounded-full bg-white px-5 text-squadup-dark hover:bg-white/90"
            @click="goToPlayers()"
          >
            Find a Pal
          </UButton>
          <UButton
            color="neutral"
            variant="soft"
            class="rounded-full bg-squadup-dark px-5 text-white"
            @click="router.push('/become-a-pal')"
          >
            Become a Pal
          </UButton>
        </div>
        <div class="mt-10 flex flex-wrap justify-center gap-x-12 gap-y-8">
          <div v-for="stat in stats" :key="stat.label" class="flex flex-col gap-1">
            <span class="text-[22px] font-bold text-white">{{ stat.value }}</span>
            <span class="text-xs text-slate-400">{{ stat.label }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
