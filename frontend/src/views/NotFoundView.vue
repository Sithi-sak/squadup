<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhCloudWarning } from '@phosphor-icons/vue'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
</script>

<template>
  <div class="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-16">
    <EmptyState
      :icon="PhCloudWarning"
      badge="Error 404"
      title="Page not found"
      description="This page respawned somewhere else. Let's get you back in the game."
    >
      <template #actions>
        <UButton color="primary" class="rounded-full px-6" @click="router.push('/home')">
          Back to home
        </UButton>
        <UButton color="neutral" variant="soft" class="rounded-full px-6" @click="router.push('/feed')">
          Go to feed
        </UButton>
      </template>
    </EmptyState>
  </div>
</template>
