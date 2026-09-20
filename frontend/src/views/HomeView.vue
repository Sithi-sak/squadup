<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhStar,
  PhUserCircle,
  PhArrowRight,
  PhCaretLeft,
  PhCaretRight,
} from '@phosphor-icons/vue'
import { usePlayersStore } from '@/stores/players'
import { useEstarsStore } from '@/stores/estars'
import PlayerCard from '@/components/players/PlayerCard.vue'
import homeSpotlightImage from '@/assets/home-rec.jpg'
import heroImage1 from '@/assets/hero-1.jpg'
import heroImage2 from '@/assets/hero-2.jpg'
import heroImage3 from '@/assets/hero-3.jpg'
import heroImage4 from '@/assets/hero-4.jpg'
import gamesTileImage from '@/assets/game.jpg'
import chillingTileImage from '@/assets/chilling.jpg'
import allServiceTileImage from '@/assets/all_service.jpg'
import { gameCoverUrl, useCoverManifest } from '@/lib/covers'
import { featuredGames } from '@/data/games'
import { resolveAvatarUrl } from '@/utils/avatar'

const router = useRouter()
const coverFilenames = useCoverManifest()
const playersStore = usePlayersStore()
const estarsStore = useEstarsStore()

function coverSrc(slug: string): string | undefined {
  const filename = coverFilenames.value.get(slug)
  return filename ? gameCoverUrl(slug, filename) : undefined
}

const allPlayers = computed(() => playersStore.list)

const spotlight = computed(
  () => [...estarsStore.leaderboard].sort((a, b) => a.rank - b.rank)[0],
)

const tiles = [
  { label: 'Games', to: '/players', image: gamesTileImage },
  { label: 'Chilling', to: { path: '/services', query: { tab: 'chilling' } }, image: chillingTileImage },
  { label: 'All Services', to: '/services', image: allServiceTileImage },
]

const heroSlides = [homeSpotlightImage, heroImage1, heroImage2, heroImage3, heroImage4]
const heroIndex = ref(0)
const heroPaused = ref(false)
let heroTimer: ReturnType<typeof setInterval> | undefined

function goToSlide(index: number) {
  heroIndex.value = (index + heroSlides.length) % heroSlides.length
  restartHeroTimer()
}

function restartHeroTimer() {
  if (heroTimer) clearInterval(heroTimer)
  heroTimer = setInterval(() => {
    if (!heroPaused.value) heroIndex.value = (heroIndex.value + 1) % heroSlides.length
  }, 5000)
}

onMounted(restartHeroTimer)

onBeforeUnmount(() => {
  if (heroTimer) clearInterval(heroTimer)
})

const eStars = computed(() =>
  [...allPlayers.value].sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0)).slice(0, 4),
)

const morePals = computed(() => allPlayers.value.slice(0, 20))

const gamesRail = ref<HTMLElement | null>(null)
const canScrollGamesLeft = ref(false)
const canScrollGamesRight = ref(false)

function updateGamesScrollState() {
  const el = gamesRail.value
  if (!el) return
  canScrollGamesLeft.value = el.scrollLeft > 0
  canScrollGamesRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 1
}

function scrollGames(direction: 'left' | 'right') {
  const el = gamesRail.value
  if (!el) return
  const amount = el.clientWidth * 0.8 * (direction === 'left' ? -1 : 1)
  el.scrollBy({ left: amount, behavior: 'smooth' })
}

onMounted(() => {
  updateGamesScrollState()
  if (!playersStore.list.length) playersStore.fetchList({ limit: 24 })
  if (!estarsStore.leaderboard.length) estarsStore.fetchLeaderboard('week')
  playersStore.fetchGameCounts()
})

function goToProfile(id: string) {
  router.push(`/players/${id}`)
}
</script>

<template>
  <div class="flex flex-col">
    <!-- eStar of the Week spotlight -->
    <section v-if="spotlight" class="px-4 pt-8 md:px-6">
      <div class="mx-auto max-w-4/5">
        <div
          class="relative grid overflow-hidden rounded-2xl bg-gradient-to-br from-brand-900/60 via-squadup-bg to-squadup-bg ring-1 ring-inset ring-white/10 md:grid-cols-2"
        >
          <div
            class="pointer-events-none absolute -left-24 -top-24 size-72 rounded-full bg-brand-500/20 blur-3xl"
          />
          <div class="relative flex flex-col justify-center gap-4 p-8 md:p-10">
            <div class="flex flex-wrap items-center gap-2">
              <span
                class="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-900/60 px-3 py-1 text-sm font-medium text-brand-300 ring-1 ring-inset ring-brand-500/30"
              >
                <PhStar :size="16" weight="fill" />
                eStar of the Week
              </span>
              <span
                v-if="spotlight.rating"
                class="inline-flex w-fit items-center gap-1.5 rounded-full bg-white/5 px-3 py-1 text-sm font-medium text-slate-200 ring-1 ring-inset ring-white/10"
              >
                <PhStar :size="14" weight="fill" class="text-amber-400" />
                {{ spotlight.rating }}
              </span>
            </div>
            <h1
              class="bg-gradient-to-r from-white to-brand-200 bg-clip-text text-4xl font-extrabold text-transparent md:text-5xl"
            >
              {{ spotlight.displayName }}
            </h1>
            <p class="max-w-120 text-md leading-relaxed text-slate-300">
              Top-rated {{ spotlight.category }} Pal this week, {{ spotlight.rating }} rating and
              glowing reviews. Book a session before the spot is gone.
            </p>
            <UButton
              color="primary"
              class="w-fit rounded-full px-5 shadow-lg shadow-brand-900/40 transition-transform hover:scale-105"
              @click="goToProfile(spotlight.id)"
            >
              Check profile
            </UButton>
          </div>
          <div
            class="group relative min-h-50 overflow-hidden"
            @mouseenter="heroPaused = true"
            @mouseleave="heroPaused = false"
          >
            <img
              v-for="(slide, index) in heroSlides"
              :key="slide"
              :src="slide"
              alt="Featured Pals streaming a gaming session"
              class="absolute inset-0 h-full w-full object-cover transition-opacity duration-700 ease-in-out"
              :class="index === heroIndex ? 'opacity-100' : 'opacity-0'"
            />
            <div
              class="pointer-events-none absolute inset-0 bg-gradient-to-r from-squadup-bg/80 via-transparent to-transparent md:block hidden"
            />
            <button
              type="button"
              aria-label="Previous image"
              class="absolute left-3 top-1/2 flex size-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-squadup-dark/60 text-white opacity-0 transition-opacity hover:bg-squadup-dark/80 group-hover:opacity-100"
              @click="goToSlide(heroIndex - 1)"
            >
              <PhCaretLeft :size="16" weight="bold" />
            </button>
            <button
              type="button"
              aria-label="Next image"
              class="absolute right-3 top-1/2 flex size-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-squadup-dark/60 text-white opacity-0 transition-opacity hover:bg-squadup-dark/80 group-hover:opacity-100"
              @click="goToSlide(heroIndex + 1)"
            >
              <PhCaretRight :size="16" weight="bold" />
            </button>
            <div class="absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-2">
              <button
                v-for="(slide, index) in heroSlides"
                :key="`dot-${slide}`"
                type="button"
                :aria-label="`Show image ${index + 1}`"
                class="h-1.5 cursor-pointer rounded-full transition-all"
                :class="index === heroIndex ? 'w-6 bg-brand-400' : 'w-1.5 bg-white/50 hover:bg-white/80'"
                @click="goToSlide(index)"
              />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Category tiles -->
    <section class="px-4 pt-6 md:px-6">
      <div class="mx-auto grid max-w-4/5 grid-cols-1 gap-4 sm:grid-cols-3">
        <router-link
          v-for="tile in tiles"
          :key="tile.label"
          :to="tile.to"
          class="relative flex h-24 items-center justify-center overflow-hidden rounded-xl bg-cover bg-center px-5 py-4"
          :style="{ backgroundImage: `url(${tile.image})` }"
        >
          <div class="absolute inset-0 bg-squadup-dark/60 hover:bg-squadup-dark/20 transition-colors" />
          <span class="relative text-lg font-semibold text-white">{{ tile.label }}</span>
        </router-link>
      </div>
    </section>

    <!-- Games rail -->
    <section class="px-4 py-10 md:px-6 md:py-14">
      <div class="mx-auto max-w-4/5">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-white">Browse by game</h2>
          <div class="hidden items-center gap-2 md:flex">
            <button
              type="button"
              aria-label="Scroll left"
              class="flex size-9 cursor-pointer items-center justify-center rounded-full bg-white/5 text-white hover:border-brand-600 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-white/10"
              :disabled="!canScrollGamesLeft"
              @click="scrollGames('left')"
            >
              <PhCaretLeft :size="16" weight="bold" />
            </button>
            <button
              type="button"
              aria-label="Scroll right"
              class="flex size-9 cursor-pointer items-center justify-center rounded-full bg-white/5 text-white hover:border-brand-600 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-white/10"
              :disabled="!canScrollGamesRight"
              @click="scrollGames('right')"
            >
              <PhCaretRight :size="16" weight="bold" />
            </button>
          </div>
        </div>
        <div
          ref="gamesRail"
          class="scrollbar-none grid auto-cols-50 grid-flow-col gap-4 overflow-x-auto"
          @scroll="updateGamesScrollState"
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

    <!-- eStars -->
    <section class="px-4 pb-10 md:px-6">
      <div class="mx-auto max-w-4/5">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-white">eStars · Top Pals</h2>
          <router-link to="/players" class="text-sm font-medium text-brand-400 hover:text-brand-300">
            More ›
          </router-link>
        </div>
        <div v-if="playersStore.loading && !eStars.length" class="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div
            v-for="n in 4"
            :key="n"
            class="flex flex-col items-center gap-3 rounded-2xl bg-gray-800/70 p-5 text-center"
          >
            <USkeleton class="h-16 w-16 rounded-full" />
            <USkeleton class="h-4 w-20" />
            <USkeleton class="h-3 w-14" />
          </div>
        </div>
        <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <button
            v-for="player in eStars"
            :key="player.id"
            type="button"
            class="flex cursor-pointer flex-col items-center gap-3 rounded-2xl bg-gray-800/70 p-5 text-center hover:bg-gray-800 transition-colors"
            @click="goToProfile(player.id)"
          >
            <UAvatar
              :src="resolveAvatarUrl(player.id, player.avatarUrl)"
              class="bg-squadup-bg text-brand-300 ring-2 ring-brand-300/60 size-20"
            >
              <PhUserCircle :size="32" />
            </UAvatar>
            <div>
              <p class="font-semibold text-white">{{ player.displayName }}</p>
              <p class="text-sm text-slate-400">{{ player.games[0] }} · {{ player.rating ?? '—' }}</p>
            </div>
          </button>
        </div>
      </div>
    </section>

    <!-- More Pals -->
    <section class="px-4 pb-14 md:px-6">
      <div class="mx-auto max-w-4/5">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-white">More Pals</h2>
          <router-link to="/players" class="text-sm font-medium text-brand-400 hover:text-brand-300">
            More ›
          </router-link>
        </div>
        <div
          v-if="playersStore.loading && !morePals.length"
          class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          <div v-for="n in 8" :key="n" class="flex flex-col gap-2.5 rounded-xl bg-gray-800/70 p-4">
            <div class="flex items-start justify-between">
              <USkeleton class="size-20 rounded-full" />
              <USkeleton class="size-8 rounded-full" />
            </div>
            <USkeleton class="h-4 w-28" />
            <USkeleton class="h-3 w-14" />
            <div class="flex gap-1.5">
              <USkeleton class="h-6 w-16 rounded-full" />
              <USkeleton class="h-6 w-14 rounded-full" />
            </div>
            <USkeleton class="h-3 w-36" />
            <USkeleton class="mt-auto h-5 w-20" />
          </div>
        </div>
        <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <PlayerCard v-for="player in morePals" :key="player.id" :player="player" />
        </div>
      </div>
    </section>
  </div>
</template>
