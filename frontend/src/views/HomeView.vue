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
import { mockPlayers } from '@/mocks/players'
import coinIcon from '@/assets/squadup-coin.svg'
import homeSpotlightImage from '@/assets/home-rec.jpg'
import gamesTileImage from '@/assets/game.jpg'
import chillingTileImage from '@/assets/chilling.jpg'
import allServiceTileImage from '@/assets/all_service.jpg'
import valorantCover from '@/assets/game_cover/valorant.png'
import cs2Cover from '@/assets/game_cover/cs2.png'
import apexLegendsCover from '@/assets/game_cover/apex_legend.png'
import overwatch2Cover from '@/assets/game_cover/overwatch2.png'
import fortniteCover from '@/assets/game_cover/fortnite.png'
import leagueOfLegendsCover from '@/assets/game_cover/league_of_legend.png'
import genshinImpactCover from '@/assets/game_cover/genshin_impact.png'

const router = useRouter()

const spotlight = [...mockPlayers].sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0))[0]!

const tiles = [
  { label: 'Games', to: '/players', image: gamesTileImage },
  { label: 'Chilling', to: '/players', image: chillingTileImage },
  { label: 'All Services', to: '/services', image: allServiceTileImage },
]

const games = [
  { name: 'Valorant', pals: 145, cover: valorantCover },
  { name: 'CS2', pals: 214, cover: cs2Cover },
  { name: 'Apex Legends', pals: 3533, cover: apexLegendsCover },
  { name: 'Overwatch 2', pals: 3533, cover: overwatch2Cover },
  { name: 'Fortnite', pals: 6230, cover: fortniteCover },
  { name: 'League of Legends', pals: 812, cover: leagueOfLegendsCover },
  { name: 'Genshin Impact', pals: 1112, cover: genshinImpactCover },
]

const eStars = computed(() =>
  [...mockPlayers].sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0)).slice(0, 4),
)

const morePals = mockPlayers

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
})

function goToProfile(id: string) {
  router.push(`/players/${id}`)
}
</script>

<template>
  <div class="flex flex-col">
    <!-- eStar of the Week spotlight -->
    <section class="px-4 pt-8 md:px-6">
      <div class="mx-auto max-w-(--content-max-width)">
        <div
          class="grid overflow-hidden rounded-2xl bg-gradient-to-br from-brand-900/50 to-squadup-bg ring-1 ring-inset ring-white/10 md:grid-cols-2"
        >
          <div class="flex flex-col justify-center gap-4 p-8 md:p-10">
            <span
              class="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300 ring-1 ring-inset ring-brand-700"
            >
              <PhStar :size="14" weight="fill" />
              eStar of the Week
            </span>
            <h1 class="text-3xl font-extrabold text-white md:text-4xl">
              {{ spotlight.displayName }}
            </h1>
            <p class="max-w-100 text-sm leading-relaxed text-slate-300">
              Top-rated {{ spotlight.games[0] }} Pal this week, {{ spotlight.rating }} rating and
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
      <div class="mx-auto grid max-w-(--content-max-width) grid-cols-1 gap-4 sm:grid-cols-3">
        <router-link
          v-for="tile in tiles"
          :key="tile.label"
          :to="tile.to"
          class="relative flex h-24 items-center justify-between overflow-hidden rounded-xl bg-cover bg-center px-5 py-4"
          :style="{ backgroundImage: `url(${tile.image})` }"
        >
          <div class="absolute inset-0 bg-squadup-dark/60 hover:bg-squadup-dark/20 transition-colors" />
          <span class="relative font-semibold text-white">{{ tile.label }}</span>
          <PhArrowRight :size="18" class="relative text-white" weight="bold" />
        </router-link>
      </div>
    </section>

    <!-- Games rail -->
    <section class="px-4 py-10 md:px-6 md:py-14">
      <div class="mx-auto max-w-(--content-max-width)">
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
          class="scrollbar-none grid auto-cols-[200px] grid-flow-col gap-4 overflow-x-auto"
          @scroll="updateGamesScrollState"
        >
          <router-link
            v-for="game in games"
            :key="game.name"
            :to="{ path: '/players', query: { game: game.name } }"
            class="relative flex aspect-[10/16] flex-col justify-end overflow-hidden rounded-xl"
          >
            <img
              :src="game.cover"
              :alt="game.name"
              class="absolute inset-0 h-full w-full object-cover"
            />
            <div
              class="absolute inset-0 bg-linear-to-t from-squadup-dark via-squadup-dark/15 to-transparent"
            />
            <div class="relative flex flex-col gap-0.5 px-3 pb-3">
              <span class="text-md font-semibold text-white">{{ game.name }}</span>
              <span class="text-sm text-slate-300">{{ game.pals.toLocaleString() }} Pals</span>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- eStars -->
    <section class="px-4 pb-10 md:px-6">
      <div class="mx-auto max-w-(--content-max-width)">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-white">eStars · Top Pals</h2>
          <router-link to="/players" class="text-sm font-medium text-brand-400 hover:text-brand-300">
            More ›
          </router-link>
        </div>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <button
            v-for="player in eStars"
            :key="player.id"
            type="button"
            class="flex cursor-pointer flex-col items-center gap-3 rounded-xl bg-gray-800/70 p-5 text-center hover:bg-gray-800 transition-colors"
            @click="goToProfile(player.id)"
          >
            <UAvatar size="2xl" class="bg-squadup-bg text-brand-300 ring-2 ring-brand-300/60">
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

    <!-- More Pals -->
    <section class="px-4 pb-14 md:px-6">
      <div class="mx-auto max-w-(--content-max-width)">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-white">More Pals</h2>
          <router-link to="/players" class="text-sm font-medium text-brand-400 hover:text-brand-300">
            More ›
          </router-link>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <article
            v-for="player in morePals"
            :key="player.id"
            class="flex flex-col gap-3 rounded-xl bg-gray-800/70 p-4"
          >
            <div class="flex items-center gap-2.5">
              <UAvatar size="md" class="bg-white/10 text-slate-300">
                <PhUserCircle :size="22" />
              </UAvatar>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5">
                  <span class="truncate font-semibold text-white">{{ player.displayName }}</span>
                  <PhTrophy
                    v-if="(player.rating ?? 0) >= 4.8"
                    :size="14"
                    weight="fill"
                    class="shrink-0 text-amber-400"
                  />
                </div>
                <p class="inline-flex items-center gap-1 text-xs text-slate-400">
                  <PhStar :size="12" weight="fill" class="text-amber-400" />
                  {{ player.rating ?? '—' }}
                </p>
              </div>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <UBadge v-if="player.rank" color="neutral" variant="soft" size="sm" class="rounded-full">
                {{ player.rank }}
              </UBadge>
              <UBadge v-if="player.role" color="neutral" variant="soft" size="sm" class="rounded-full">
                {{ player.role }}
              </UBadge>
            </div>
            <div class="mt-auto flex items-center justify-between pt-1">
              <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ player.pricePerHour ?? '—' }}/hr
              </span>
              <UButton
                size="sm"
                variant="solid"
                class="rounded-full"
                @click="router.push(`/book/${player.id}`)"
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
