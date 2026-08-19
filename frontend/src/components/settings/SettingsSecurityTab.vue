<script setup lang="ts">
import { ref } from 'vue'
import { PhDesktop, PhDeviceMobile } from '@phosphor-icons/vue'
import { mockActiveSessions } from '@/mocks/settings'
import SettingsSelectRow from './SettingsSelectRow.vue'
import SettingsToggleRow from './SettingsToggleRow.vue'
import SettingsActionRow from './SettingsActionRow.vue'

const twoFactorEnabled = ref(false)
const loginAlerts = ref('Email')
const loginAlertOptions = ['Email', 'Push', 'Off']

const sessions = ref(mockActiveSessions.map((session) => ({ ...session })))

function signOutSession(sessionId: string) {
  sessions.value = sessions.value.filter((session) => session.id !== sessionId)
}

function signOutAllOthers() {
  sessions.value = sessions.value.filter((session) => session.current)
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Password & sign-in</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsActionRow label="Password" value="Last changed 3 months ago" action-label="Change" />
        <SettingsToggleRow
          v-model="twoFactorEnabled"
          label="Two-factor authentication"
          description="Off, add an extra layer of security."
        />
        <SettingsSelectRow v-model="loginAlerts" label="Login alerts" :items="loginAlertOptions" />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Active sessions</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <div v-for="session in sessions" :key="session.id" class="flex items-center justify-between gap-4 py-4">
          <div class="flex items-center gap-3">
            <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 text-slate-300">
              <PhDeviceMobile v-if="session.device.includes('iPhone')" :size="18" />
              <PhDesktop v-else :size="18" />
            </div>
            <div>
              <p class="font-semibold text-white">{{ session.device }}</p>
              <p class="text-sm text-slate-400">{{ session.location }} · {{ session.lastActive }}</p>
            </div>
          </div>
          <UBadge v-if="session.current" color="primary" variant="soft" size="sm" class="rounded-full">
            This device
          </UBadge>
          <UButton
            v-else
            color="neutral"
            variant="soft"
            size="sm"
            class="rounded-full"
            @click="signOutSession(session.id)"
          >
            Sign out
          </UButton>
        </div>
      </div>

      <button
        v-if="sessions.length > 1"
        type="button"
        class="mt-2 w-full cursor-pointer text-center text-sm font-medium text-red-400 hover:text-red-300"
        @click="signOutAllOthers"
      >
        Sign out of all other devices
      </button>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Danger zone</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsActionRow
          label="Delete account"
          value="Permanently remove your account and data"
          action-label="Delete"
          danger
        />
      </div>
    </div>
  </div>
</template>
