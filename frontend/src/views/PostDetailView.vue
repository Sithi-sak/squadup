<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import FeedPostThread from '@/components/feed/FeedPostThread.vue'

const route = useRoute()
const router = useRouter()
const postId = computed(() => String(route.params.postId))
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 pt-8 pb-14 md:px-6">
    <div class="mx-auto max-w-2xl">
      <FeedPostThread :post-id="postId" @back="router.push('/feed')" />
    </div>
  </div>
</template>
