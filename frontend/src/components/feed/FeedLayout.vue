<script setup lang="ts">
import FeedRightRail from './FeedRightRail.vue'
import FeedSidebar from './FeedSidebar.vue'

defineProps<{
  active: 'feed' | 'following' | 'explore' | 'saved' | 'profile'
  showCreatePost?: boolean
}>()
</script>

<template>
  <div class="mx-auto max-w-4/5 px-4 py-6 md:px-6">
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr] lg:items-start xl:grid-cols-[260px_1fr_300px]">
      <div class="hidden lg:sticky lg:top-20 lg:block lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
        <FeedSidebar :active="active" :show-create-post="showCreatePost" />
      </div>
      <div class="flex min-w-0 flex-col gap-4">
        <slot />
      </div>
      <div class="hidden xl:sticky xl:top-20 xl:block xl:max-h-[calc(100vh-5rem)] xl:overflow-y-auto">
        <FeedRightRail />
      </div>
    </div>
  </div>
</template>
