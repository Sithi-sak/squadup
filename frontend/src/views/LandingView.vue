<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhMagnifyingGlass,
  PhImage,
  PhUserCircle,
  PhCheckCircle,
  PhStar,
  PhCaretLeft,
  PhCaretRight,
} from '@phosphor-icons/vue'
import { mockPlayers } from '@/mocks/players'
import coinIcon from '@/assets/squadup-coin.svg'

const router = useRouter()

const searchQuery = ref('')

const quickGames = ['Valorant', 'League of Legends', 'Fortnite', 'Apex Legends', 'Overwatch 2']

const services = [
  { name: 'Valorant', pals: 145 },
  { name: 'CS2', pals: 214 },
  { name: 'Apex Legends', pals: 3533 },
  { name: 'Overwatch 2', pals: 3533 },
  { name: 'Fortnite', pals: 6230 },
  { name: 'League of Legends', pals: 812 },
]

const topPlayers = mockPlayers

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
      <div class="mx-auto max-w-(--content-max-width)">
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
          class="scrollbar-none grid auto-cols-[200px] grid-flow-col gap-4 overflow-x-auto"
          @scroll="updateServicesScrollState"
        >
          <router-link
            v-for="game in services"
            :key="game.name"
            :to="{ path: '/players', query: { game: game.name } }"
            class="flex flex-col overflow-hidden rounded-xl bg-white/5"
          >
            <div class="flex aspect-[4/5] items-center justify-center bg-white/5 text-slate-500">
              <PhImage :size="28" />
            </div>
            <div class="flex flex-col gap-0.5 px-3 pt-2.5 pb-3">
              <span class="text-sm font-semibold text-white">{{ game.name }}</span>
              <span class="text-xs text-slate-400">{{ game.pals.toLocaleString() }} Pals</span>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- Top Pal -->
    <section class="px-4 py-10 md:px-6 md:py-14">
      <div class="mx-auto max-w-(--content-max-width)">
        <h2 class="mb-5 text-2xl font-bold text-white">Top Pal</h2>
        <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <article
            v-for="player in topPlayers"
            :key="player.id"
            class="flex flex-col overflow-hidden rounded-xl bg-white/5"
          >
            <div class="flex aspect-square items-center justify-center bg-white/5 text-slate-500">
              <PhUserCircle :size="48" />
            </div>
            <div class="flex flex-1 flex-col gap-2 p-3">
              <div class="flex items-center gap-1.5">
                <span class="text-[15px] font-bold text-white">{{ player.displayName }}</span>
                <PhCheckCircle :size="16" weight="fill" class="shrink-0 text-brand-600" />
              </div>
              <p class="truncate text-xs text-slate-400">{{ player.games[0] }} · {{ player.rank }}</p>
              <div class="flex gap-1.5">
                <span class="rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] text-slate-300">
                  PC
                </span>
                <span class="rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] text-slate-300">
                  Ranked
                </span>
              </div>
              <div class="flex items-center justify-between text-[13px] text-white">
                <span class="inline-flex items-center gap-1">
                  <PhStar :size="14" weight="fill" class="text-amber-400" />
                  {{ player.rating ?? '—' }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                  {{ player.pricePerHour ?? '—' }}/hr
                </span>
              </div>
              <UButton
                color="primary"
                block
                class="mt-auto justify-center rounded-full"
                @click="router.push(`/book/${player.id}`)"
              >
                Play now
              </UButton>
            </div>
          </article>
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
            @click="router.push('/become-player')"
          >
            Become a Pal
          </UButton>
        </div>
        <div class="mt-10 flex flex-wrap justify-center gap-x-12 gap-y-8">
          <div v-for="stat in stats" :key="stat.label" class="flex flex-col gap-1">
            <span class="text-[22px] font-extrabold text-white">{{ stat.value }}</span>
            <span class="text-xs text-slate-400">{{ stat.label }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
