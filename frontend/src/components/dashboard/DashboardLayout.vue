<script setup lang="ts">
import DashboardSidebar from './DashboardSidebar.vue'

defineProps<{
  active: 'dashboard' | 'orders' | 'services' | 'earnings' | 'messages' | 'settings'
}>()
</script>

<template>
  <div class="mx-auto h-[calc(100vh-65px)] max-w-(--content-max-width) px-4 py-6 md:px-6">
    <div class="grid h-full grid-cols-1 gap-6 lg:grid-cols-[240px_1fr]">
      <div class="hidden lg:block">
        <DashboardSidebar :active="active" />
      </div>
      <div class="min-h-0 min-w-0">
        <slot />
      </div>
    </div>
  </div>
</template>
