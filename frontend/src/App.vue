<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import { useAuthStore } from '@/stores/auth'
import { useMessagesStore } from '@/stores/messages'
import { useNotificationsStore } from '@/stores/notifications'
import { usePresenceStore } from '@/stores/presence'
import { useWalletStore } from '@/stores/wallet'

const route = useRoute()

const authStore = useAuthStore()
const messagesStore = useMessagesStore()
const notificationsStore = useNotificationsStore()
const presenceStore = usePresenceStore()
const walletStore = useWalletStore()

/** Live bell, messages badge and inbox (4.73), header balance (4.74) and online presence (4.78), for the whole signed-in session. Here rather
 * than in `AppHeader`, which unmounts on chrome-less routes. Keyed on the id, not the user
 * object, so a token refresh (which replaces the object) doesn't tear the channels down. */
watch(
  () => authStore.user?.id,
  (userId) => {
    if (userId) {
      notificationsStore.subscribeRealtime(userId)
      messagesStore.subscribeRealtime(userId)
      walletStore.subscribeRealtime(userId)
      presenceStore.subscribe(userId)
    } else {
      notificationsStore.unsubscribeRealtime()
      messagesStore.unsubscribeRealtime()
      walletStore.unsubscribeRealtime()
      presenceStore.unsubscribe()
    }
  },
  { immediate: true },
)

/** Kept alive so revisiting a nav-bar tab reuses its existing instance instead of
 * remounting - instant, no re-fetch, no blank flash. Scoped to the 6 top-nav views
 * (see AppHeader's `navLinks`); every other route mounts/unmounts normally. The feed's
 * entry here is its shell, not `FeedView` - the shell owns the sidebar/right rail and
 * keeps its own tabs alive one level down (4.21). */
const cachedViewNames = [
  'HomeView',
  'FeedShellView',
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
