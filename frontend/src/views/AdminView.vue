<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { PhBell, PhShieldCheck, PhSignOut } from '@phosphor-icons/vue'
import brandLogo from '@/assets/brand.svg'
import SettingsNav from '@/components/settings/SettingsNav.vue'
import AdminOverviewPanel from '@/components/admin/AdminOverviewPanel.vue'
import AdminPalApplicationsPanel from '@/components/admin/AdminPalApplicationsPanel.vue'
import AdminFlaggedPlayersPanel from '@/components/admin/AdminFlaggedPlayersPanel.vue'
import AdminDisputesPanel from '@/components/admin/AdminDisputesPanel.vue'
import AdminWithdrawalsPanel from '@/components/admin/AdminWithdrawalsPanel.vue'
import AdminNotificationPanel from '@/components/admin/AdminNotificationPanel.vue'
import { useAdminStore } from '@/stores/admin'
import type { AdminTabKey } from '@/mocks/admin'

const admin = useAdminStore()

const code = ref('')
const loading = ref(false)

const fieldUi = {
  base: 'bg-white/5 px-5 py-3.5 text-center text-lg tracking-[0.5em] ring-1 ring-inset ring-white/10 focus-visible:ring-2 focus-visible:ring-brand-600',
}

function handleLogin() {
  loading.value = true
  setTimeout(() => {
    admin.login(code.value)
    loading.value = false
  }, 400)
}

function handleLogout() {
  admin.logout()
  code.value = ''
}

const baseTabs: { key: AdminTabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'applications', label: 'Pal applications' },
  { key: 'flagged', label: 'Flagged players' },
  { key: 'disputes', label: 'Disputes' },
  { key: 'payouts', label: 'Payouts' },
]

const activeTab = ref<AdminTabKey>('overview')

/** How many unread alerts each queue is holding, so the count is visible without opening the
 * bell. Overview never carries one - it is a summary, not a queue. */
const unreadByTab = computed(() => {
  const counts: Partial<Record<AdminTabKey, number>> = {}
  for (const alert of admin.unreadNotifications) {
    counts[alert.tab] = (counts[alert.tab] ?? 0) + 1
  }
  return counts
})

const tabs = computed(() =>
  baseTabs.map((tab) => ({ ...tab, badge: unreadByTab.value[tab.key] ?? 0 })),
)

/** The admin sits on this screen while reports and payout requests arrive elsewhere, so the
 * feed is refetched on a timer rather than only on load. A minute is slow enough to be
 * invisible against the four queries behind `/admin/notifications`. */
const ALERT_POLL_MS = 60_000
let alertTimer: ReturnType<typeof setInterval> | undefined

watch(
  () => admin.isAuthenticated,
  (authenticated) => {
    clearInterval(alertTimer)
    alertTimer = undefined
    if (!authenticated) {
      return
    }
    admin.fetchNotifications()
    alertTimer = setInterval(() => admin.fetchNotifications(), ALERT_POLL_MS)
  },
  { immediate: true },
)

onUnmounted(() => clearInterval(alertTimer))

/** Opening a queue from the bell. The alert itself is retired by the click (the panel marks it
 * read) and leaves the feed for good once the item is decided here. */
function openTab(tab: AdminTabKey) {
  activeTab.value = tab
}
</script>

<template>
  <div v-if="!admin.isAuthenticated" class="flex min-h-screen items-center justify-center px-4 py-10">
    <div class="w-full max-w-sm rounded-2xl bg-gray-800/70 p-8 ring-1 ring-inset ring-white/10">
      <div class="flex flex-col items-center gap-2 text-center">
        <img :src="brandLogo" alt="SquadUp" class="h-8" />
        <h1 class="mt-2 text-xl font-bold text-white">Admin access</h1>
        <p class="text-sm text-slate-400">Restricted. Enter the admin access code.</p>
      </div>

      <form class="mt-6 flex flex-col gap-4" @submit.prevent="handleLogin">
        <UInput
          v-model="code"
          type="password"
          inputmode="numeric"
          maxlength="4"
          placeholder="····"
          autocomplete="off"
          variant="subtle"
          size="xl"
          :ui="fieldUi"
        />
        <p v-if="admin.error" class="text-sm text-red-400">{{ admin.error }}</p>
        <UButton
          type="submit"
          color="primary"
          block
          :loading="loading"
          class="justify-center rounded-full py-3.5 text-base"
        >
          Log in
        </UButton>
      </form>
    </div>
  </div>

  <div v-else class="grid min-h-screen grid-cols-1 lg:grid-cols-[240px_1fr]">
    <aside class="hidden flex-col justify-between border-r border-white/10 p-4 lg:flex">
      <div class="flex flex-col gap-6">
        <router-link to="/" class="flex items-center gap-2 px-2 py-1">
          <img :src="brandLogo" alt="SquadUp" class="h-6" />
          <span class="text-sm font-semibold text-slate-400">Admin</span>
        </router-link>
        <SettingsNav v-model:active="activeTab" :tabs="tabs" />
      </div>

      <div class="flex flex-col gap-3 border-t border-white/10 pt-4">
        <div class="flex items-center gap-2.5 px-2">
          <UAvatar size="md" class="bg-white/10 text-slate-300">
            <PhShieldCheck :size="20" weight="fill" />
          </UAvatar>
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-white">Admin</p>
            <p class="truncate text-xs text-slate-400">SquadUp moderation</p>
          </div>
        </div>
        <UButton color="neutral" variant="soft" block class="justify-center gap-2 rounded-full" @click="handleLogout">
          <PhSignOut :size="16" />
          Log out
        </UButton>
      </div>
    </aside>

    <div class="flex flex-col overflow-y-auto">
      <header class="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3 md:px-8">
        <router-link to="/" class="flex items-center gap-2 lg:hidden">
          <img :src="brandLogo" alt="SquadUp" class="h-6" />
          <span class="text-sm font-semibold text-slate-400">Admin</span>
        </router-link>
        <p class="hidden text-sm text-slate-400 lg:block">Moderation queue</p>

        <UPopover :content="{ side: 'bottom', align: 'end', sideOffset: 8 }">
          <UButton
            color="neutral"
            variant="ghost"
            :ui="{ base: 'rounded-full' }"
            square
            class="relative"
            :aria-label="
              admin.unreadNotificationCount > 0
                ? `Alerts, ${admin.unreadNotificationCount} unread`
                : 'Alerts'
            "
          >
            <PhBell :size="20" />
            <span
              v-if="admin.unreadNotificationCount > 0"
              class="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-brand-400 ring-2 ring-squadup-bg"
            />
          </UButton>
          <template #content="{ close }">
            <AdminNotificationPanel :close="close" @open-tab="openTab" />
          </template>
        </UPopover>
      </header>

      <nav class="flex gap-2 overflow-x-auto border-b border-white/10 p-3 lg:hidden">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="shrink-0 cursor-pointer rounded-full px-4 py-2 text-sm transition-colors"
          :class="
            activeTab === tab.key
              ? 'bg-brand-600/15 font-medium text-brand-400'
              : 'text-slate-300 hover:bg-white/5 hover:text-white'
          "
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <span
            v-if="tab.badge"
            class="ml-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-500 px-1 text-[10px] font-semibold text-white"
          >
            {{ tab.badge }}
          </span>
        </button>
      </nav>

      <div class="mx-auto w-full max-w-full flex-1 p-6 md:p-8">
        <AdminOverviewPanel v-if="activeTab === 'overview'" @view-all="openTab" />
        <AdminPalApplicationsPanel v-else-if="activeTab === 'applications'" />
        <AdminFlaggedPlayersPanel v-else-if="activeTab === 'flagged'" />
        <AdminDisputesPanel v-else-if="activeTab === 'disputes'" />
        <AdminWithdrawalsPanel v-else />
      </div>
    </div>
  </div>
</template>
