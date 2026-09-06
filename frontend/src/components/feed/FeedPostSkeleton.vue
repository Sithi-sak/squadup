<script setup lang="ts">
// Loading placeholder shown while `feedStore.postsLoading`/`followingLoading` is true, mirroring
// `FeedPostCard.vue`'s layout (avatar + name/handle, text lines, like/comment row) so the feed
// doesn't flash blank or an empty-state message before the real posts land.
</script>

<template>
  <div class="rounded-xl bg-gray-800/70 p-4">
    <div class="flex items-center gap-3">
      <USkeleton class="h-10 w-10 shrink-0 rounded-full" />
      <div class="space-y-2">
        <USkeleton class="h-4 w-32" />
        <USkeleton class="h-3 w-20" />
      </div>
    </div>
    <div class="mt-3 space-y-2">
      <USkeleton class="h-3.5 w-full" />
      <USkeleton class="h-3.5 w-4/5" />
    </div>
    <div class="mt-3 flex items-center gap-4">
      <USkeleton class="h-4 w-10" />
      <USkeleton class="h-4 w-10" />
    </div>
  </div>
</template>
