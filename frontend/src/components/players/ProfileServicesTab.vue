<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhStar, PhUserCircle } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import type { PlayerReview, PlayerServiceDetail } from '@/stores/players'

const props = defineProps<{
  playerId: string
  detail: PlayerServiceDetail
  reviews: PlayerReview[]
}>()

const router = useRouter()

type ReviewFilter = 'all' | 'positive' | 'other'
const reviewFilter = ref<ReviewFilter>('all')

const visibleReviews = computed(() => {
  if (props.reviews.length === 0) return []
  if (reviewFilter.value === 'positive') return props.reviews.filter((r) => r.sentiment === 'positive')
  if (reviewFilter.value === 'other') return props.reviews.filter((r) => r.sentiment !== 'positive')
  return props.reviews
})
</script>

<template>
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
    <div class="flex flex-col gap-4">
      <div class="rounded-xl bg-gray-800/70 p-5">
        <h2 class="text-2xl font-bold text-white">{{ detail.title }}</h2>
        <p class="mt-2 inline-flex items-center gap-1.5 text-sm text-slate-400">
          <PhStar :size="14" weight="fill" class="text-amber-400" />
          {{ detail.rating ? detail.rating.toFixed(1) : '--' }}
          <span>· {{ detail.servedCount.toLocaleString() }} Served</span>
        </p>
        <p class="mt-4 text-sm leading-relaxed text-slate-300">{{ detail.description }}</p>

        <div class="mt-4 flex flex-col gap-2 text-sm">
          <div v-if="detail.styles.length" class="flex items-center justify-between gap-4">
            <span class="text-slate-400">Styles</span>
            <span class="text-right font-medium text-white">{{ detail.styles.join(', ') }}</span>
          </div>
          <div v-if="detail.platforms.length" class="flex items-center justify-between gap-4">
            <span class="text-slate-400">Platforms</span>
            <span class="text-right font-medium text-white">{{ detail.platforms.join(', ') }}</span>
          </div>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h3 class="text-lg font-bold text-white">Service Types · {{ detail.serviceTypes.length }}</h3>
        <div class="mt-3 flex flex-col gap-2">
          <div
            v-for="type in detail.serviceTypes"
            :key="type.label"
            class="flex items-center justify-between gap-3 rounded-full bg-gray-700/50 px-4 py-3"
          >
            <span class="text-sm font-medium text-white">{{ type.label }}</span>
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center gap-1 text-sm font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ type.priceCoins }}{{ type.priceUnit }}
              </span>
              <UBadge v-if="type.promoBadge" color="primary" variant="soft" size="sm" class="rounded-full text-xs text-brand-500">
                {{ type.promoBadge }}
              </UBadge>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-xl bg-gray-800/70 p-5">
        <h3 class="text-lg font-bold text-white">Reviews · {{ reviews.length }} Reviews</h3>
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <UButton
            :color="reviewFilter === 'all' ? 'primary' : 'neutral'"
            :variant="reviewFilter === 'all' ? 'solid' : 'soft'"
            size="sm"
            class="rounded-full"
            @click="reviewFilter = 'all'"
          >
            All
          </UButton>
          <UButton
            :color="reviewFilter === 'positive' ? 'primary' : 'neutral'"
            :variant="reviewFilter === 'positive' ? 'solid' : 'soft'"
            size="sm"
            class="rounded-full"
            @click="reviewFilter = 'positive'"
          >
            Positive
          </UButton>
          <UButton
            :color="reviewFilter === 'other' ? 'primary' : 'neutral'"
            :variant="reviewFilter === 'other' ? 'solid' : 'soft'"
            size="sm"
            class="rounded-full"
            @click="reviewFilter = 'other'"
          >
            Neutral/Negative
          </UButton>
        </div>

        <p v-if="visibleReviews.length === 0" class="py-8 text-center text-sm text-slate-400">
          No reviews yet.
        </p>
        <div v-else class="mt-4 flex flex-col divide-y divide-white/10">
          <div v-for="review in visibleReviews" :key="review.id" class="flex gap-3 py-4 first:pt-0 last:pb-0">
            <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
              <PhUserCircle :size="20" />
            </UAvatar>
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-2">
                <span class="font-medium text-white">{{ review.author }}</span>
                <span class="shrink-0 text-xs text-slate-400">{{ review.timeAgo }}</span>
              </div>
              <p class="mt-0.5 inline-flex items-center gap-1 text-xs text-amber-400">
                <PhStar :size="12" weight="fill" />
                {{ review.rating }}
              </p>
              <p class="mt-1.5 text-sm text-slate-300">{{ review.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-4">
      <div class="aspect-video w-full rounded-xl bg-white/5 ring-1 ring-inset ring-white/10" />

      <div class="rounded-xl bg-gray-800/70 p-4">
        <UButton
          color="primary"
          variant="outline"
          block
          size="lg"
          class="rounded-full"
          @click="router.push('/messages')"
        >
          Chat
        </UButton>
        <UButton
          color="primary"
          block
          size="lg"
          class="mt-2.5 rounded-full"
          @click="router.push(`/book/${playerId}`)"
        >
          Order
        </UButton>
        <p class="mt-3 text-center text-xs text-slate-400">Avg Response Time {{ detail.avgResponseTime }}</p>
      </div>
    </div>
  </div>
</template>
