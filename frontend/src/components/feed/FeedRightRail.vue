<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhCaretRight, PhUserCircle } from '@phosphor-icons/vue'
import { usePlayersStore, type PlayerSummary } from '@/stores/players'
import { useFeedStore } from '@/stores/feed'
import { resolveAvatarUrl } from '@/utils/avatar'

const router = useRouter()
const playersStore = usePlayersStore()
const feedStore = useFeedStore()

onMounted(() => {
  playersStore.fetchSuggested()
  if (feedStore.posts.length === 0) feedStore.fetchFeed()
})

function subtitleFor(pal: PlayerSummary): string {
  const game = pal.games[0]
  if (game && pal.rating) return `${game} · ${pal.rating.toFixed(1)}`
  return game ?? 'New Pal'
}

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}

/** Real "Trending now" (was mock-only per CHECKPOINT 3.8a) - top post categories by volume,
 * since there's no dedicated hashtag/topic table. */
const trendingTopics = computed(() => {
  const counts = new Map<string, number>()
  for (const post of feedStore.posts) {
    counts.set(post.category, (counts.get(post.category) ?? 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([category, count]) => ({ category, count }))
})

function exploreCategory(category: string) {
  router.push({ path: '/feed/explore', query: { category } })
}

const following = ref(new Set<string>())

async function follow(pal: PlayerSummary) {
  if (!pal.userId || following.value.has(pal.id)) return
  following.value.add(pal.id)
  try {
    await feedStore.toggleFollow(pal.userId, false)
    playersStore.suggested = playersStore.suggested.filter((p) => p.id !== pal.id)
  } finally {
    following.value.delete(pal.id)
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div v-if="playersStore.suggestedLoading && !playersStore.suggested.length" class="rounded-xl bg-gray-800/70 p-5">
      <div class="flex items-center justify-between">
        <USkeleton class="h-5 w-32" />
        <USkeleton class="h-4 w-12" />
      </div>
      <div class="mt-4 flex flex-col gap-4">
        <div v-for="n in 4" :key="n" class="flex items-center gap-3">
          <USkeleton class="h-10 w-10 shrink-0 rounded-full" />
          <div class="min-w-0 flex-1 space-y-1.5">
            <USkeleton class="h-3.5 w-24" />
            <USkeleton class="h-3 w-16" />
          </div>
          <USkeleton class="h-6 w-16 shrink-0 rounded-full" />
        </div>
      </div>
    </div>

    <div v-else-if="playersStore.suggested.length" class="rounded-xl bg-gray-800/50 p-5">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-white">Suggested Pals</h3>
        <router-link to="/players" class="text-sm text-brand-400 hover:text-brand-300">See all</router-link>
      </div>
      <div class="mt-4 flex flex-col gap-4">
        <div v-for="pal in playersStore.suggested" :key="pal.id" class="flex items-center gap-3">
          <router-link :to="`/players/${pal.id}`" class="flex min-w-0 flex-1 items-center gap-3">
            <UAvatar
              :src="resolveAvatarUrl(pal.id, pal.avatarUrl)"
              size="lg"
              class="shrink-0 bg-white/10 text-slate-300"
            >
              <PhUserCircle :size="20" />
            </UAvatar>
            <div class="min-w-0 flex-1">
              <p class="truncate text-md font-medium text-white">{{ pal.displayName }}</p>
              <p class="truncate text-sm text-slate-400">{{ subtitleFor(pal) }}</p>
            </div>
          </router-link>
          <UButton
            color="primary"
            size="sm"
            class="shrink-0 rounded-full"
            :loading="following.has(pal.id)"
            @click="follow(pal)"
          >
            Follow
          </UButton>
        </div>
      </div>
    </div>

    <div v-if="feedStore.postsLoading && !feedStore.posts.length" class="rounded-xl bg-gray-800/70 p-5">
      <USkeleton class="h-5 w-28" />
      <div class="mt-3 flex flex-col divide-y divide-white/10">
        <div v-for="n in 5" :key="n" class="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
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
