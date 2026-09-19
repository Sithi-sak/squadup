<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PhCaretRight } from '@phosphor-icons/vue'
import { useFeedStore } from '@/stores/feed'
import SuggestedPalsCard from '@/components/feed/SuggestedPalsCard.vue'

const router = useRouter()
const feedStore = useFeedStore()

onMounted(() => {
  if (feedStore.posts.length === 0) feedStore.fetchFeed()
})

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}

/** Real "Trending now" (was mock-only per CHECKPOINT 3.8a) - top topics by volume, since there's
 * no dedicated hashtag/topic table. A post counts under its composer `tag` when it has one (a
 * game or service name, the more interesting topic) and under its `category` otherwise. */
const trendingTopics = computed(() => {
  const counts = new Map<string, number>()
  for (const post of feedStore.posts) {
    const topic = post.tag || post.category
    counts.set(topic, (counts.get(topic) ?? 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([category, count]) => ({ category, count }))
})

function exploreCategory(category: string) {
  router.push({ path: '/feed/explore', query: { category } })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <SuggestedPalsCard />

    <div
      v-if="feedStore.postsLoading && !feedStore.posts.length"
      class="rounded-xl bg-gray-800/70 p-5"
    >
      <USkeleton class="h-5 w-28" />
      <div class="mt-3 flex flex-col divide-y divide-white/10">
        <div
          v-for="n in 5"
          :key="n"
          class="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
        >
          <div class="space-y-1.5">
            <USkeleton class="h-4 w-24" />
            <USkeleton class="h-3 w-14" />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="trendingTopics.length" class="rounded-xl bg-gray-800/50 p-5">
      <h3 class="font-semibold text-white">Trending now</h3>
      <div class="mt-3 flex flex-col divide-y divide-white/10">
        <button
          v-for="topic in trendingTopics"
          :key="topic.category"
          type="button"
          class="flex items-center justify-between gap-3 py-3 text-left first:pt-0 last:pb-0"
          @click="exploreCategory(topic.category)"
        >
          <div>
            <p class="text-md text-white">#{{ topic.category }}</p>
            <p class="text-sm text-slate-400">{{ formatCount(topic.count) }} posts</p>
          </div>
          <PhCaretRight :size="20" weight="bold" class="shrink-0 text-slate-500" />
        </button>
      </div>
    </div>
  </div>
</template>
