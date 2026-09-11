<script setup lang="ts">
import { useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

const route = useRoute()

/** Kept alive so revisiting a nav-bar tab reuses its existing instance instead of
 * remounting - instant, no re-fetch, no blank flash. Scoped to the 6 top-nav views
 * (see AppHeader's `navLinks`); every other route mounts/unmounts normally. */
const cachedViewNames = [
  'HomeView',
  'FeedView',
  'AllServicesView',
  'EstarsLeaderboardView',
  'BecomeAPalView',
  'HelpCenterView',
]
</script>

<template>
  <UApp>
    <div class="flex min-h-screen flex-col">
      <AppHeader v-if="!route.meta.hideChrome" />
      <main class="w-full flex-1">
        <router-view v-slot="{ Component }">
          <transition name="route-fade" mode="out-in">
            <keep-alive :include="cachedViewNames">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
      <AppFooter v-if="!route.meta.hideChrome && !route.meta.hideFooter" />
    </div>
  </UApp>
</template>

<style scoped>
.route-fade-enter-active,
.route-fade-leave-active {
  transition: opacity 120ms ease;
}

.route-fade-enter-from,
.route-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .route-fade-enter-active,
  .route-fade-leave-active {
    transition: none;
  }
}
</style>
