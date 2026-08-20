<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhStar, PhUserCircle } from '@phosphor-icons/vue'
import type { PlayerReview } from '@/stores/players'

const props = defineProps<{ reviews: PlayerReview[] }>()

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

    <p v-if="visibleReviews.length === 0" class="py-8 text-center text-sm text-slate-400">No reviews yet.</p>
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
</template>
