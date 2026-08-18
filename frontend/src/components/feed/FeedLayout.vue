<script setup lang="ts">
import FeedRightRail from './FeedRightRail.vue'
import FeedSidebar from './FeedSidebar.vue'

defineProps<{
  active: 'feed' | 'following' | 'explore' | 'saved'
  showCreatePost?: boolean
}>()
</script>

<template>
  <div class="mx-auto max-w-(--content-max-width) px-4 py-6 md:px-6">
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr] xl:grid-cols-[260px_1fr_300px]">
      <div class="hidden lg:block">
        <FeedSidebar :active="active" :show-create-post="showCreatePost" />
      </div>
      <div class="flex min-w-0 flex-col gap-4">
        <slot />
      </div>
      <div class="hidden xl:block">
        <FeedRightRail />
      </div>
    </div>
  </div>
</template>
