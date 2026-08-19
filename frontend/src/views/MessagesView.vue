<script setup lang="ts">
import { computed } from 'vue'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import MessagesPanel from '@/components/messages/MessagesPanel.vue'
import { mockCurrentUser } from '@/mocks/users'

const isPal = computed(() => Boolean(mockCurrentUser.playerId))
</script>

<template>
  <DashboardLayout v-if="isPal" active="messages">
    <MessagesPanel title="Messages" subtitle="Chat with your buyers in real time" />
  </DashboardLayout>
  <div v-else class="h-[calc(100vh-65px)] px-4 py-6 md:px-6">
    <div class="mx-auto h-full max-w-(--content-max-width)">
      <MessagesPanel title="Messages" subtitle="Chat with your Pals" />
    </div>
  </div>
</template>
