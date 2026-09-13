<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import { useAuthStore } from '@/stores/auth'

/** Persistent shell for every `/dashboard/player` page, plus `/messages` and `/settings`
 * (nested here via an absolute child path so their URLs stay top-level - see router/index.ts).
 * The sidebar lives here, one level above the `<router-view>`, so moving between Dashboard/
 * Orders/My services/Earnings/Messages/Settings swaps only the content column - the sidebar
 * keeps its component instance and scroll position instead of unmounting and re-rendering on
 * every navigation (mirrors FeedShellView). Which nav item is lit comes from the child route's
 * `meta.dashboardTab`.
 *
 * Messages and Settings also serve buyers (non-Pal accounts), who don't get this sidebar at
 * all - each of those two views renders its own buyer-facing layout when `!isPal`, so the
 * shell skips the sidebar chrome entirely and hands the route straight through. */
const route = useRoute()
const authStore = useAuthStore()

const isPal = computed(() => Boolean(authStore.user?.playerId))
const activeTab = computed(() => route.meta.dashboardTab ?? 'dashboard')

/** These keep their instance while the shell is mounted, so bouncing between tabs is instant
 * and doesn't re-fetch or reset scroll/filters/selection. */
const cachedTabViews = [
  'PlayerDashboardView',
  'PlayerOrdersView',
  'PlayerServicesView',
  'PlayerEarningsView',
  'MessagesView',
  'SettingsView',
]
</script>

<template>
  <DashboardLayout v-if="isPal" :active="activeTab">
    <router-view v-slot="{ Component }">
      <transition name="dashboard-fade" mode="out-in">
        <keep-alive :include="cachedTabViews">
          <component :is="Component" />
        </keep-alive>
      </transition>
    </router-view>
  </DashboardLayout>
  <router-view v-else />
</template>

<style scoped>
.dashboard-fade-enter-active,
.dashboard-fade-leave-active {
  transition: opacity 120ms ease;
}

.dashboard-fade-enter-from,
.dashboard-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-fade-enter-active,
  .dashboard-fade-leave-active {
    transition: none;
  }
}
</style>
