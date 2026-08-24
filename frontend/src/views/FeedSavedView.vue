<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PhBookmarkSimple } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import coinIcon from '@/assets/squadup-coin.svg'
import FeedLayout from '@/components/feed/FeedLayout.vue'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import { useFeedStore, type FeedSavedItem } from '@/stores/feed'
import { formatTimeAgo } from '@/utils/timeAgo'

const feedStore = useFeedStore()
const toast = useToast()

onMounted(() => {
  feedStore.fetchSaved()
})

const filters = [
  { key: 'all', label: 'All' },
  { key: 'post', label: 'Posts' },
  { key: 'clip', label: 'Clips' },
  { key: 'service', label: 'Services' },
  { key: 'pal', label: 'Pals' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')

const visibleItems = computed(() => {
  if (activeFilter.value === 'all') return feedStore.saved
  return feedStore.saved.filter((item) => item.kind === activeFilter.value)
})

async function unsave(item: FeedSavedItem) {
  try {
    await feedStore.toggleSaved(item.kind, (item.kind === 'post' ? item.postId : item.serviceId) ?? item.id)
  } catch (err) {
    toast.add({
      title: 'Could not unsave',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}
</script>

<template>
  <FeedLayout active="saved" show-create-post>
    <div>
      <h1 class="text-2xl font-bold text-white">Saved</h1>
      <p class="mt-1 text-sm text-slate-400">Your bookmarked posts, clips, Pals and services</p>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <UButton
        v-for="filter in filters"
        :key="filter.key"
        :color="activeFilter === filter.key ? 'primary' : 'neutral'"
        :variant="activeFilter === filter.key ? 'solid' : 'soft'"
        size="sm"
        class="rounded-full"
        @click="activeFilter = filter.key"
      >
        {{ filter.label }}
      </UButton>
    </div>

    <UEmpty v-if="visibleItems.length === 0" title="Nothing saved here yet" class="py-16 text-white" />

    <template v-for="item in visibleItems" :key="item.id">
      <FeedPostCard
        v-if="item.kind === 'post'"
        :id="item.postId ?? item.id"
        :author="item.author ?? ''"
        :handle="item.handle ?? ''"
        :tier="item.tier"
        :time-ago="formatTimeAgo(item.createdAt)"
        :text="item.text ?? ''"
        :has-image="item.hasImage ?? false"
        :likes="item.likes ?? 0"
        :comments="item.comments ?? 0"
      >
        <template #action>
          <UButton
            color="neutral"
            variant="ghost"
            square
            :ui="{ base: 'rounded-full' }"
            aria-label="Unsave"
            @click="unsave(item)"
          >
            <PhBookmarkSimple :size="18" weight="fill" class="text-brand-400" />
          </UButton>
        </template>
      </FeedPostCard>

      <div v-else class="flex items-center gap-4 rounded-xl bg-gray-800/70 p-4">
        <div class="h-16 w-16 shrink-0 rounded-lg bg-white/5 ring-1 ring-inset ring-white/10" />
        <div class="min-w-0 flex-1">
          <p class="truncate font-semibold text-white">{{ item.name }}</p>
          <p class="truncate text-sm text-slate-400">by {{ item.by }} · {{ item.category }}</p>
          <p class="mt-1 flex items-center gap-1 text-sm text-slate-300">
            <img :src="coinIcon" alt="" class="h-4 w-4" />
            {{ item.priceCoins }} {{ item.priceUnit }}
            <span v-if="item.promoLabel" class="text-brand-400">· {{ item.promoLabel }}</span>
          </p>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <UButton
            color="neutral"
            variant="ghost"
            square
            :ui="{ base: 'rounded-full' }"
            aria-label="Unsave"
            @click="unsave(item)"
          >
            <PhBookmarkSimple :size="18" weight="fill" class="text-brand-400" />
          </UButton>
          <UButton color="primary" size="sm" class="rounded-full">Book</UButton>
        </div>
      </div>
    </template>
  </FeedLayout>
</template>
