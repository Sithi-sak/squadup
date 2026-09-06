<script setup lang="ts">
import { ref } from 'vue'
import { PhShieldCheck, PhSignOut } from '@phosphor-icons/vue'
import brandLogo from '@/assets/brand.svg'
import SettingsNav from '@/components/settings/SettingsNav.vue'
import AdminOverviewPanel from '@/components/admin/AdminOverviewPanel.vue'
import AdminPalApplicationsPanel from '@/components/admin/AdminPalApplicationsPanel.vue'
import AdminFlaggedPlayersPanel from '@/components/admin/AdminFlaggedPlayersPanel.vue'
import AdminDisputesPanel from '@/components/admin/AdminDisputesPanel.vue'
import { useAdminStore } from '@/stores/admin'

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

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'applications', label: 'Pal applications' },
  { key: 'flagged', label: 'Flagged players' },
  { key: 'disputes', label: 'Disputes' },
] as const

const activeTab = ref<(typeof tabs)[number]['key']>('overview')
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
        <SettingsNav v-model:active="activeTab" :tabs="[...tabs]" />
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
        </button>
      </nav>

      <div class="mx-auto w-full max-w-5xl flex-1 p-6 md:p-8">
        <AdminOverviewPanel v-if="activeTab === 'overview'" @view-all="activeTab = $event" />
        <AdminPalApplicationsPanel v-else-if="activeTab === 'applications'" />
        <AdminFlaggedPlayersPanel v-else-if="activeTab === 'flagged'" />
        <AdminDisputesPanel v-else />
      </div>
    </div>
  </div>
</template>
