<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import FeedRightRail from '@/components/feed/FeedRightRail.vue'
import FeedSidebar from '@/components/feed/FeedSidebar.vue'

/** Persistent shell for every `/feed` page (4.21). The sidebar and right rail live here, one
 * level above the `<router-view>`, so moving between feed tabs swaps only the centre column -
 * the rails keep their component instance, their fetched data and their scroll position
 * instead of unmounting and re-fetching on every navigation. Which nav item is lit and
 * whether the sidebar shows its "Create post" button come from the child route's `meta`. */
const route = useRoute()

const activeTab = computed(() => route.meta.feedTab ?? 'feed')
const showCreatePost = computed(() => route.meta.feedCreatePost === true)

/** The four fixed tabs keep their instance while the shell is mounted, so bouncing between
 * them is instant and their filters survive. Param-driven pages (`/feed/u/:id`, `/feed/me`)
 * mount fresh each time so they never show another account's data. */
const cachedTabViews = ['FeedView', 'FeedFollowingView', 'FeedExploreView', 'FeedSavedView']
</script>

<template>
  <div class="mx-auto max-w-4/5 px-4 py-6 md:px-6">
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr] lg:items-start xl:grid-cols-[260px_1fr_300px]">
      <div class="hidden lg:sticky lg:top-20 lg:block lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
        <FeedSidebar :active="activeTab" :show-create-post="showCreatePost" />
      </div>

      <router-view v-slot="{ Component }">
        <transition name="feed-fade" mode="out-in">
          <keep-alive :include="cachedTabViews">
            <component :is="Component" />
          </keep-alive>
        </transition>
      </router-view>

      <div class="hidden xl:sticky xl:top-20 xl:block xl:max-h-[calc(100vh-5rem)] xl:overflow-y-auto">
        <FeedRightRail />
      </div>
    </div>
  </div>
</template>

<style scoped>
.feed-fade-enter-active,
.feed-fade-leave-active {
  transition: opacity 120ms ease;
}

.feed-fade-enter-from,
.feed-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .feed-fade-enter-active,
  .feed-fade-leave-active {
    transition: none;
  }
}
</style>
