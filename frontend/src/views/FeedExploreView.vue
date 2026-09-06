<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { PhHeart, PhMagnifyingGlass, PhUserCircle } from '@phosphor-icons/vue'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import { exploreCategories } from '@/mocks/feed'
import { useFeedStore } from '@/stores/feed'
import { resolveAvatarUrl } from '@/utils/avatar'

const route = useRoute()
const feedStore = useFeedStore()

onMounted(() => {
  feedStore.fetchFeed()
})

const search = ref('')
// Deep-linkable from `FeedRightRail.vue`'s "Trending now" (`?category=`), e.g. clicking a real
// post category there. Falls back to the "Trending" (unfiltered) tab otherwise.
const activeCategory = ref(typeof route.query.category === 'string' ? route.query.category : 'Trending')
watch(
  () => route.query.category,
  (category) => {
    if (typeof category === 'string') activeCategory.value = category
  },
)

const visiblePosts = computed(() => {
  const filtered =
    activeCategory.value === 'Trending'
      ? feedStore.posts
      : feedStore.posts.filter((p) => p.category.toLowerCase() === activeCategory.value.toLowerCase())

  if (!search.value) return filtered
  const q = search.value.toLowerCase()
  return filtered.filter(
    (p) => p.category.toLowerCase().includes(q) || p.author.toLowerCase().includes(q),
  )
})

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <FeedLayout active="explore" show-create-post>
    <div>
      <h1 class="text-2xl font-bold text-white">Explore</h1>
      <p class="mt-1 text-sm text-slate-400">Discover trending posts, clips and creators across SquadUp</p>
    </div>

    <UInput
      v-model="search"
      placeholder="Search posts, clips, games or creators..."
      variant="subtle"
      size="lg"
      class="w-full rounded-full"
      :ui="{ base: 'rounded-full' }"
    >
      <template #leading>
        <PhMagnifyingGlass :size="18" />
      </template>
    </UInput>

    <div class="flex flex-wrap items-center gap-2">
      <UButton
        v-for="category in exploreCategories"
        :key="category"
        :color="activeCategory === category ? 'primary' : 'neutral'"
        :variant="activeCategory === category ? 'solid' : 'soft'"
        size="sm"
        class="rounded-full"
        @click="activeCategory = category"
      >
        {{ category }}
      </UButton>
    </div>

    <p v-if="visiblePosts.length === 0" class="py-16 text-center text-sm text-slate-400">
      No posts match this search.
    </p>

    <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <router-link
        v-for="post in visiblePosts"
        :key="post.id"
        :to="`/feed/${post.id}`"
        class="relative aspect-square overflow-hidden rounded-lg bg-white/5"
      >
        <UBadge color="neutral" variant="solid" size="sm" class="absolute top-2 left-2 rounded-full bg-black/50 text-xs">
          {{ post.category }}
        </UBadge>
        <div class="absolute inset-x-0 bottom-0 flex items-center justify-between gap-2 bg-linear-to-t from-black/70 to-transparent p-2.5">
          <div class="flex min-w-0 items-center gap-1.5">
            <UAvatar :src="resolveAvatarUrl(post.authorId, post.avatarUrl)" size="sm" class="shrink-0 bg-white/10 text-slate-300">
              <PhUserCircle :size="20" />
            </UAvatar>
            <span class="truncate text-sm font-medium text-white">{{ post.author }}</span>
          </div>
          <span class="flex shrink-0 items-center gap-1 text-sm text-white">
            <PhHeart :size="14" weight="fill" class="text-red-400" />
            {{ formatCount(post.likes) }}
          </span>
        </div>
      </router-link>
    </div>
  </FeedLayout>
</template>
