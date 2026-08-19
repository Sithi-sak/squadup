<script setup lang="ts">
import { useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

const route = useRoute()
</script>

<template>
  <UApp>
    <div class="flex min-h-screen flex-col">
      <AppHeader v-if="!route.meta.hideChrome" />
      <main class="w-full flex-1">
        <router-view />
      </main>
      <AppFooter v-if="!route.meta.hideChrome && !route.meta.hideFooter" />
    </div>
  </UApp>
</template>
