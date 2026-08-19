<script setup lang="ts">
import { computed, ref } from 'vue'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import SettingsNav from '@/components/settings/SettingsNav.vue'
import SettingsProfileTab from '@/components/settings/SettingsProfileTab.vue'
import SettingsAccountTab from '@/components/settings/SettingsAccountTab.vue'
import SettingsNotificationsTab from '@/components/settings/SettingsNotificationsTab.vue'
import SettingsPaymentsTab from '@/components/settings/SettingsPaymentsTab.vue'
import SettingsPrivacyTab from '@/components/settings/SettingsPrivacyTab.vue'
import SettingsSecurityTab from '@/components/settings/SettingsSecurityTab.vue'
import { mockCurrentUser } from '@/mocks/users'

const isPal = computed(() => Boolean(mockCurrentUser.playerId))

const tabs = computed(() => [
  ...(isPal.value ? [{ key: 'profile', label: 'Profile' }] : []),
  { key: 'account', label: 'Account' },
  { key: 'notifications', label: 'Notifications' },
  { key: 'payments', label: 'Payments' },
  { key: 'privacy', label: 'Privacy' },
  { key: 'security', label: 'Security' },
])

const activeTab = ref(isPal.value ? 'profile' : 'account')
</script>

<template>
  <DashboardLayout v-if="isPal" active="settings">
    <div class="flex h-full flex-col gap-6 overflow-y-auto pr-1">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">Settings</h1>
          <p class="mt-1 text-sm text-slate-400">Manage your profile, account and preferences</p>
        </div>
        <UButton color="primary" class="rounded-full" disabled>Save changes</UButton>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr]">
        <SettingsNav v-model:active="activeTab" :tabs="tabs" />

        <div class="min-w-0">
          <SettingsProfileTab v-if="activeTab === 'profile'" />
          <SettingsAccountTab v-else-if="activeTab === 'account'" />
          <SettingsNotificationsTab v-else-if="activeTab === 'notifications'" />
          <SettingsPaymentsTab v-else-if="activeTab === 'payments'" />
          <SettingsPrivacyTab v-else-if="activeTab === 'privacy'" />
          <SettingsSecurityTab v-else-if="activeTab === 'security'" />
        </div>
      </div>
    </div>
  </DashboardLayout>

  <div v-else class="h-[calc(100vh-65px)] overflow-y-auto px-4 py-6 md:px-6">
    <div class="mx-auto flex max-w-(--content-max-width) flex-col gap-6">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">Settings</h1>
          <p class="mt-1 text-sm text-slate-400">Manage your account and preferences</p>
        </div>
        <UButton color="primary" class="rounded-full" disabled>Save changes</UButton>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr]">
        <SettingsNav v-model:active="activeTab" :tabs="tabs" />

        <div class="min-w-0">
          <SettingsAccountTab v-if="activeTab === 'account'" />
          <SettingsNotificationsTab v-else-if="activeTab === 'notifications'" />
          <SettingsPaymentsTab v-else-if="activeTab === 'payments'" />
          <SettingsPrivacyTab v-else-if="activeTab === 'privacy'" />
          <SettingsSecurityTab v-else-if="activeTab === 'security'" />
        </div>
      </div>
    </div>
  </div>
</template>
