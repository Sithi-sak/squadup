<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhStar,
  PhUserCircle,
  PhArrowRight,
  PhTrophy,
  PhCaretLeft,
  PhCaretRight,
} from '@phosphor-icons/vue'
import { usePlayersStore } from '@/stores/players'
import { useEstarsStore } from '@/stores/estars'
import coinIcon from '@/assets/squadup-coin.svg'
import homeSpotlightImage from '@/assets/home-rec.jpg'
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
          class="grid overflow-hidden rounded-2xl bg-gradient-to-br from-brand-900/50 to-squadup-bg ring-0 ring-inset ring-white/10 md:grid-cols-2"
        >
          <div class="flex flex-col justify-center gap-4 p-8 md:p-10">
            <span
              class="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300"
            >
              <PhStar :size="14" weight="fill" />
              eStar of the Week
            </span>
            <h1 class="text-3xl font-extrabold text-white md:text-4xl">
              {{ spotlight.displayName }}
            </h1>
            <p class="max-w-100 text-sm leading-relaxed text-slate-300">
              Top-rated {{ spotlight.category }} Pal this week, {{ spotlight.rating }} rating and
              glowing reviews. Book a session before the spot is gone.
            </p>
            <UButton
              color="primary"
              class="w-fit rounded-full px-5"
              @click="goToProfile(spotlight.id)"
            >
              Check profile
            </UButton>
          </div>
          <div class="min-h-50">
            <img
              :src="homeSpotlightImage"
              alt="Featured Pals streaming a Valorant duo session"
              class="h-full w-full object-cover"
            />
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
          <div v-for="n in 8" :key="n" class="flex flex-col gap-3 rounded-2xl bg-gray-800/70 p-4">
            <div class="flex items-center gap-2.5">
              <USkeleton class="h-12 w-12 rounded-full" />
              <div class="min-w-0 flex-1 space-y-1.5">
                <USkeleton class="h-4 w-24" />
                <USkeleton class="h-3 w-14" />
              </div>
            </div>
            <USkeleton class="h-3 w-32" />
            <div class="mt-auto flex items-center justify-between pt-1">
              <USkeleton class="h-4 w-14" />
              <USkeleton class="h-8 w-16 rounded-full" />
            </div>
          </div>
        </div>
        <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <article
            v-for="player in morePals"
            :key="player.id"
            class="flex flex-col gap-3 rounded-2xl bg-gray-800/70 p-4"
          >
            <div class="flex items-center gap-2.5">
              <UAvatar :src="resolveAvatarUrl(player.id, player.avatarUrl)" size="xl" class="bg-white/10 text-slate-300">
                <PhUserCircle :size="22" />
              </UAvatar>
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="truncate font-semibold text-white">{{ player.displayName }}</span>
                  <PhTrophy
                    v-if="(player.rating ?? 0) >= 4.8"
                    :size="20"
                    weight="fill"
                    class="shrink-0 text-amber-400"
                  />
                </div>
                <p class="inline-flex items-center gap-1 text-sm text-slate-400">
                  <PhStar :size="16" weight="fill" class="text-amber-400" />
                  {{ player.rating ?? '—' }}
                </p>
              </div>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <UBadge v-if="player.rank" color="neutral" variant="soft" size="md" class="rounded-full text-xs">
                {{ player.rank }}
              </UBadge>
              <UBadge v-if="player.role" color="neutral" variant="soft" size="md" class="rounded-full text-xs">
                {{ player.role }}
              </UBadge>
            </div>
            <div class="mt-auto flex items-center justify-between pt-1">
              <span class="inline-flex items-center gap-2 text-md font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-6 w-6" />
                {{ player.pricePerHour ?? '—' }}/hr
              </span>
              <UButton
                size="md"
                variant="solid"
                class="rounded-full"
                @click="router.push(`/players/${player.id}`)"
              >
                Book
              </UButton>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>
