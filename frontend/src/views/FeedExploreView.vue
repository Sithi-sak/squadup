<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhHeart, PhMagnifyingGlass, PhUserCircle } from '@phosphor-icons/vue'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import { exploreCategories, mockExplorePosts } from '@/mocks/feed'

const search = ref('')
const activeCategory = ref('Trending')

const visiblePosts = computed(() => {
  const filtered =
    activeCategory.value === 'Trending'
      ? mockExplorePosts
      : mockExplorePosts.filter((p) => p.category === activeCategory.value)

  if (!search.value) return filtered
  const q = search.value.toLowerCase()
  return filtered.filter(
    (p) => p.category.toLowerCase().includes(q) || p.author.toLowerCase().includes(q),
  )
})
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

    <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3">
      <div
        v-for="post in visiblePosts"
        :key="post.id"
        class="relative aspect-square overflow-hidden rounded-lg bg-white/5 ring-1 ring-inset ring-white/10"
      >
        <UBadge color="neutral" variant="solid" size="sm" class="absolute top-2 left-2 rounded-full bg-black/50">
          {{ post.category }}
        </UBadge>
        <div class="absolute inset-x-0 bottom-0 flex items-center justify-between gap-2 bg-linear-to-t from-black/70 to-transparent p-2.5">
          <div class="flex min-w-0 items-center gap-1.5">
            <UAvatar size="xs" class="shrink-0 bg-white/10 text-slate-300">
              <PhUserCircle :size="14" />
            </UAvatar>
            <span class="truncate text-xs font-medium text-white">{{ post.author }}</span>
          </div>
          <span class="flex shrink-0 items-center gap-1 text-xs text-white">
            <PhHeart :size="14" weight="fill" class="text-red-400" />
            {{ post.likes }}
          </span>
        </div>
      </div>
    </div>
  </FeedLayout>
</template>
