<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
</script>

<template>
  <UApp>
    <div class="flex min-h-screen flex-col">
      <AppHeader />
      <main class="w-full flex-1">
        <router-view />
      </main>
      <AppFooter />
    </div>
  </UApp>
</template>
