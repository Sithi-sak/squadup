<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  PhCaretUp,
  PhCaretDown,
  PhMedal,
  PhMinus,
  PhStar,
  PhTrophy,
  PhUserCircle,
} from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { estarsCategories } from '@/mocks/estars'
import { useEstarsStore, type EstarPeriod } from '@/stores/estars'
import { resolveAvatarUrl } from '@/utils/avatar'

const estarsStore = useEstarsStore()

const periods = ['This week', 'This month', 'All time'] as const
const periodParams: Record<(typeof periods)[number], EstarPeriod> = {
  'This week': 'week',
  'This month': 'month',
  'All time': 'all_time',
}
const activePeriod = ref<(typeof periods)[number]>('This week')

const activeCategory = ref(estarsCategories[0])

function refetch() {
  const category = activeCategory.value === estarsCategories[0] ? null : activeCategory.value
  estarsStore.fetchLeaderboard(periodParams[activePeriod.value], category)
}

onMounted(refetch)
watch(activePeriod, refetch)
watch(activeCategory, refetch)

const topThree = computed(() =>
  estarsStore.leaderboard.filter((entry) => entry.rank <= 3).sort((a, b) => a.rank - b.rank),
)
const rest = computed(() => estarsStore.leaderboard.filter((entry) => entry.rank > 3))

const tierMeta = {
  1: {
    label: 'Champion',
    order: 'md:order-2',
    card: 'border-amber-400/70 bg-gradient-to-b from-amber-400/15 to-transparent p-8',
    medal: 'bg-amber-400/15 text-amber-400 ring-amber-400/60',
    accent: 'text-amber-400',
    avatarSize: '3xl',
    nameClass: 'text-xl',
    coinsClass: 'text-2xl',
  },
  2: {
    label: 'Runner Up',
    order: 'md:order-1',
    card: 'border-slate-300/50 bg-gradient-to-b from-slate-300/10 to-transparent p-6',
    medal: 'bg-slate-300/15 text-slate-300 ring-slate-300/50',
    accent: 'text-slate-300',
    avatarSize: '3xl',
    nameClass: 'text-lg',
    coinsClass: 'text-xl',
  },
  3: {
    label: 'Third Place',
    order: 'md:order-3',
    card: 'border-orange-500/50 bg-gradient-to-b from-orange-500/10 to-transparent p-6',
    medal: 'bg-orange-500/15 text-orange-400 ring-orange-500/50',
    accent: 'text-orange-400',
    avatarSize: '3xl',
    nameClass: 'text-lg',
    coinsClass: 'text-xl',
  },
} as const

const trendIcon = { up: PhCaretUp, down: PhCaretDown, flat: PhMinus } as const
const trendClass = { up: 'text-brand-400', down: 'text-red-400', flat: 'text-slate-500' } as const
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div class="mx-auto max-w-4/5">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="flex items-center gap-2 text-3xl font-bold text-white md:text-4xl">
            eStars Leaderboard
          </h1>
          <p class="mt-2 text-slate-400">The top-earning Pals on SquadUp this week</p>
        </div>
        <USelect
          v-model="activeCategory"
          :items="estarsCategories"
          size="lg"
          variant="subtle"
          class="w-44"
          :ui="{ base: 'rounded-full' }"
        />
      </div>

      <div class="mt-6 flex flex-wrap items-center gap-2">
        <UButton
          v-for="period in periods"
          :key="period"
          :color="activePeriod === period ? 'primary' : 'neutral'"
          :variant="activePeriod === period ? 'solid' : 'soft'"
          size="md"
          class="rounded-full"
          @click="activePeriod = period"
        >
          {{ period }}
        </UButton>
      </div>

      <template v-if="estarsStore.loading">
        <div class="mt-8 grid grid-cols-1 items-center gap-4 md:grid-cols-3">
          <div
            v-for="(order, n) in ['md:order-2', 'md:order-1', 'md:order-3']"
            :key="n"
            :class="order"
            class="flex flex-col items-center gap-3 rounded-3xl border-white/10 bg-gray-800/70 p-6 text-center"
          >
            <USkeleton class="h-11 w-11 rounded-full" />
            <USkeleton class="h-3 w-16" />
            <USkeleton class="h-16 w-16 rounded-full" />
            <USkeleton class="h-5 w-24" />
            <USkeleton class="h-5 w-20 rounded-full" />
            <USkeleton class="h-4 w-12" />
            <USkeleton class="h-6 w-16" />
          </div>
        </div>

        <div class="mt-8 divide-y divide-white/10 border-t border-white/10">
          <div v-for="n in 6" :key="n" class="flex items-center gap-4 py-4">
            <USkeleton class="h-4 w-6 shrink-0" />
            <USkeleton class="h-9 w-9 shrink-0 rounded-full" />
            <div class="min-w-0 flex-1 space-y-1.5">
              <USkeleton class="h-4 w-28" />
              <USkeleton class="h-3 w-20" />
            </div>
            <USkeleton class="hidden h-4 w-10 shrink-0 sm:block" />
            <USkeleton class="h-4 w-14 shrink-0" />
          </div>
        </div>
      </template>

      <template v-else>
        <div class="mt-8 grid grid-cols-1 items-center gap-4 md:grid-cols-3">
          <div
            v-for="entry in topThree"
            :key="entry.id"
            :class="[tierMeta[entry.rank as 1 | 2 | 3].order, tierMeta[entry.rank as 1 | 2 | 3].card]"
            class="flex flex-col items-center gap-3 rounded-3xl text-center"
          >
            <div
              :class="tierMeta[entry.rank as 1 | 2 | 3].medal"
              class="flex h-11 w-11 items-center justify-center rounded-full"
            >
              <PhMedal :size="22" weight="fill" />
            </div>
            <p
              :class="tierMeta[entry.rank as 1 | 2 | 3].accent"
              class="text-xs font-semibold tracking-wide uppercase"
            >
              {{ tierMeta[entry.rank as 1 | 2 | 3].label }}
            </p>

            <UAvatar
              :src="resolveAvatarUrl(entry.id, entry.avatarUrl)"
              :size="tierMeta[entry.rank as 1 | 2 | 3].avatarSize"
              class="bg-white/10 text-slate-300 size-20"
            >
              <PhUserCircle :size="36" />
            </UAvatar>

            <div>
              <p :class="tierMeta[entry.rank as 1 | 2 | 3].nameClass" class="font-semibold text-white">
                {{ entry.displayName }}
              </p>
              <UBadge color="neutral" variant="soft" size="sm" class="mt-1.5 rounded-full text-xs">
                {{ entry.category ?? '—' }}
              </UBadge>
            </div>

            <p class="inline-flex items-center gap-1 text-sm text-slate-300">
              <PhStar :size="14" weight="fill" class="text-amber-400" />
              {{ entry.rating ? entry.rating.toFixed(entry.rating % 1 === 0 ? 1 : 2) : '--' }}
            </p>

            <p
              :class="tierMeta[entry.rank as 1 | 2 | 3].coinsClass"
              class="inline-flex items-center gap-1.5 font-bold text-white"
            >
              <img :src="coinIcon" alt="" class="h-5 w-5" />
              {{ entry.coins.toLocaleString() }}
            </p>
          </div>
        </div>

        <div class="mt-8 divide-y divide-white/10 border-t border-white/10">
          <div
            v-for="entry in rest"
            :key="entry.id"
            class="flex items-center gap-4 py-4"
          >
            <span class="w-8 shrink-0 font-semibold text-slate-400">#{{ entry.rank }}</span>

            <UAvatar :src="resolveAvatarUrl(entry.id, entry.avatarUrl)" size="md" class="shrink-0 bg-white/10 text-slate-300">
              <PhUserCircle :size="20" />
            </UAvatar>

            <div class="min-w-0 flex-1">
              <p class="truncate font-medium text-white">{{ entry.displayName }}</p>
              <p class="truncate text-sm text-slate-400">{{ entry.category ?? '—' }}</p>
            </div>

            <span class="hidden shrink-0 items-center gap-1 text-sm text-slate-300 sm:inline-flex">
              <PhStar :size="14" weight="fill" class="text-amber-400" />
              {{ entry.rating ? entry.rating.toFixed(entry.rating % 1 === 0 ? 1 : 2) : '--' }}
            </span>

            <span class="inline-flex shrink-0 items-center gap-1.5 text-sm font-semibold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ entry.coins.toLocaleString() }}
            </span>

            <component
              :is="trendIcon[entry.trend]"
              :size="16"
              weight="bold"
              :class="trendClass[entry.trend]"
              class="shrink-0"
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
