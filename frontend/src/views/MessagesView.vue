<script setup lang="ts">
import { computed } from 'vue'
import MessagesPanel from '@/components/messages/MessagesPanel.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isPal = computed(() => Boolean(authStore.user?.playerId))
</script>

<template>
  <MessagesPanel v-if="isPal" title="Messages" subtitle="Chat with your buyers in real time" />
  <div v-else class="h-[calc(100vh-65px)] px-4 py-6 md:px-6">
    <div class="mx-auto h-full max-w-(--content-max-width)">
      <MessagesPanel title="Messages" subtitle="Chat with your Pals" />
    </div>
  </div>
</template>
