<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhList,
  PhMagnifyingGlass,
  PhBell,
  PhChatCircle,
  PhCaretDown,
  PhUserCircle,
  PhPlus,
} from '@phosphor-icons/vue'
import brandLogo from '@/assets/brand.svg'
import coinIcon from '@/assets/squadup-coin.svg'
import { mockCurrentUser } from '@/mocks/users'
import { useNotificationsStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'
import { useWalletStore } from '@/stores/wallet'
import NotificationPanel from '@/components/layout/NotificationPanel.vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const notificationsStore = useNotificationsStore()
const authStore = useAuthStore()
const walletStore = useWalletStore()

const router = useRouter()

const mobileMenuOpen = ref(false)
const searchQuery = ref('')

const isAuthenticated = computed(() => authStore.isAuthenticated)

/** Bell badge and coin balance need to be populated across every authenticated page, not just
 * `/notifications`/`/wallet`, so they're fetched here rather than per-view - re-fires whenever a
 * session is (re)established (initial mount once `authStore.init()` resolves, or a fresh login).
 * `walletStore` is the same Pinia instance `WalletView` uses, so a top-up there updates this
 * balance too without an extra fetch. */
watch(
  () => authStore.user,
  (user) => {
    if (!user) return
    notificationsStore.fetchNotifications()
    walletStore.fetchWallet()
  },
  { immediate: true },
)

const isPal = computed(() => !!authStore.user?.playerId)

const navLinks = computed(() => [
  { label: 'Discover', to: '/home' },
  { label: 'Feed', to: '/feed' },
  { label: 'Games', to: '/services' },
  { label: 'eStars', to: '/estars' },
  ...(isPal.value ? [] : [{ label: 'Become a Pal', to: '/become-a-pal' }]),
  { label: 'Help', to: '/help' },
])

const dashboardPath = computed(() => (isPal.value ? '/dashboard/player' : '/feed/me'))
const firstName = computed(
  () => (authStore.user?.displayName ?? mockCurrentUser.displayName)?.split(' ')[0] ?? 'Account',
)
const avatarUrl = computed(() => resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id))

const accountMenuItems = [
  [
    { label: 'My orders', to: '/bookings' },
    { label: 'Wallet', to: '/wallet' },
    { label: 'Subscriptions', to: '/subscriptions' },
    { label: 'Settings', to: '/settings' },
  ],
  [{ label: 'Log out', onSelect: handleLogout }],
]

async function handleLogout() {
  await authStore.signOut()
  router.push('/')
}

function handleSearch() {
  mobileMenuOpen.value = false
  router.push({
    path: '/players',
    query: searchQuery.value ? { q: searchQuery.value } : undefined,
  })
}
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-white/10 bg-squadup-bg">
    <div class="mx-auto flex h-16 max-w-(--content-max-width) items-center gap-6 px-4">
      <router-link :to="isAuthenticated ? '/home' : '/'" class="flex shrink-0 items-center">
        <img :src="brandLogo" alt="SquadUp" class="h-6.5 w-auto" />
      </router-link>

      <nav v-if="isAuthenticated" class="hidden items-center gap-5 md:flex">
        <template v-for="link in navLinks" :key="link.label">
          <router-link
            v-if="link.to"
            :to="link.to"
            class="text-sm text-slate-300 hover:text-white"
            active-class="text-brand-400"
          >
            {{ link.label }}
          </router-link>
          <span v-else class="text-sm text-slate-300">{{ link.label }}</span>
        </template>
      </nav>

      <div v-if="isAuthenticated" class="ml-auto hidden items-center gap-3 lg:flex">
        <UInput
          v-model="searchQuery"
          placeholder="Search"
          variant="subtle"
          size="md"
          color="primary"
          class="w-56 rounded-full"
          :ui="{ base: 'rounded-full' }"
          @keyup.enter="handleSearch"
        >
          <template #leading>
            <PhMagnifyingGlass :size="16" weight="bold" />
          </template>
        </UInput>

        <div class="flex items-center gap-1.5">
          <UButton to="/wallet" color="neutral" variant="soft" size="lg" class="gap-1.5 rounded-full py-1.5">
            <template #leading>
              <img :src="coinIcon" alt="" class="h-4.5 w-4.5" />
            </template>
            {{ walletStore.balance.toLocaleString() }}
          </UButton>
          <UButton
            to="/wallet"
            color="primary"
            variant="solid"
            square
            size="sm"
            class="rounded-full"
            aria-label="Top up coins"
          >
            <PhPlus :size="16" weight="bold" />
          </UButton>
        </div>

        <UPopover :content="{ side: 'bottom', align: 'end', sideOffset: 8 }">
          <UButton
            color="neutral"
            variant="ghost"
            :ui="{ base: 'rounded-full' }"
            square
            aria-label="Notifications"
            class="relative"
          >
            <PhBell :size="20" />
            <span
              v-if="notificationsStore.unreadCount > 0"
              class="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-brand-400 ring-2 ring-squadup-bg"
            />
          </UButton>
          <template #content="{ close }">
            <NotificationPanel :close="close" />
          </template>
        </UPopover>
        <UButton to="/messages" color="neutral" variant="ghost" :ui="{ base: 'rounded-full' }" square aria-label="Messages">
          <PhChatCircle :size="20" />
        </UButton>

        <UButton :to="dashboardPath" variant="outline" class="rounded-full px-4 text-white bg-brand-600/15 ring-brand-600 hover:bg-brand-600/40 transition-all">
          Dashboard
        </UButton>

        <UDropdownMenu :items="accountMenuItems">
          <button
            type="button"
            class="flex cursor-pointer items-center gap-1.5 rounded-full py-1 pr-1.5 pl-1 hover:bg-white/5"
          >
            <UAvatar :src="avatarUrl" size="sm" class="bg-white/10 text-slate-300">
              <PhUserCircle :size="20" />
            </UAvatar>
            <span class="text-sm text-white">{{ firstName }}</span>
            <PhCaretDown :size="14" class="text-slate-400" />
          </button>
        </UDropdownMenu>
      </div>

      <div v-else class="ml-auto hidden items-center gap-5 md:flex">
        <router-link to="/login" class="text-sm text-slate-300 hover:text-white">
          Sign in
        </router-link>
        <UButton to="/become-a-pal" color="primary" class="rounded-full px-5">
          Become a Pal
        </UButton>
      </div>

      <UButton
        class="ml-auto md:hidden"
        color="neutral"
        variant="ghost"
        square
        aria-label="Open menu"
        @click="mobileMenuOpen = true"
      >
        <PhList :size="22" />
      </UButton>
    </div>

    <USlideover v-model:open="mobileMenuOpen" side="right" title="Menu">
      <template #body>
        <template v-if="isAuthenticated">
          <UInput
            v-model="searchQuery"
            placeholder="Search"
            variant="soft"
            class="mb-4 w-full rounded-full"
            :ui="{ base: 'rounded-full' }"
            @keyup.enter="handleSearch"
          >
            <template #leading>
              <PhMagnifyingGlass :size="16" />
            </template>
          </UInput>
          <nav class="flex flex-col gap-4" @click="mobileMenuOpen = false">
            <router-link to="/home" class="text-base text-white">Discover</router-link>
            <router-link to="/feed" class="text-base text-white">Feed</router-link>
            <router-link to="/players" class="text-base text-white">Browse Players</router-link>
            <router-link to="/estars" class="text-base text-white">eStars</router-link>
            <router-link to="/messages" class="text-base text-white">Messages</router-link>
            <router-link to="/notifications" class="text-base text-white">Notifications</router-link>
            <router-link to="/bookings" class="text-base text-white">My Bookings</router-link>
            <router-link to="/wallet" class="text-base text-white">Wallet</router-link>
            <router-link to="/subscriptions" class="text-base text-white">Subscriptions</router-link>
            <router-link :to="dashboardPath" class="text-base text-white">Dashboard</router-link>
            <router-link to="/settings" class="text-base text-white">Settings</router-link>
            <template v-if="!isPal">
              <USeparator />
              <router-link to="/become-a-pal" class="text-base text-white">
                Become a Pal
              </router-link>
            </template>
          </nav>
        </template>
        <nav v-else class="flex flex-col gap-4" @click="mobileMenuOpen = false">
          <router-link to="/players" class="text-base text-white">Browse Players</router-link>
          <router-link to="/login" class="text-base text-white">Sign in</router-link>
          <USeparator />
          <router-link to="/become-player" class="text-base text-white">
            Become a Pal
          </router-link>
        </nav>
      </template>
    </USlideover>
  </header>
</template>
