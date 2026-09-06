<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhDesktop, PhDeviceMobile } from '@phosphor-icons/vue'
import { mockAccountDetails } from '@/mocks/settings'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import SettingsSelectRow from './SettingsSelectRow.vue'
import SettingsToggleRow from './SettingsToggleRow.vue'
import SettingsActionRow from './SettingsActionRow.vue'
import TwoFactorAuthModal from '@/components/modals/TwoFactorAuthModal.vue'
import DeleteAccountModal from '@/components/modals/DeleteAccountModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const toast = useToast()

onMounted(() => {
  settingsStore.fetchSessions()
})

const twoFactorEnabled = ref(false)
const twoFactorModalOpen = ref(false)
const deleteAccountModalOpen = ref(false)
const deletingAccount = ref(false)
const loginAlerts = ref('Email')
const loginAlertOptions = ['Email', 'Push', 'Off']

const maskedPhone = computed(() => {
  const parts = mockAccountDetails.phone.split(' ')
  if (parts.length < 3) return mockAccountDetails.phone
  return `${parts[0]} ••• ${parts[parts.length - 1]}`
})

const signingOutId = ref<string | null>(null)
const signingOutOthers = ref(false)

async function signOutSession(sessionId: string) {
  signingOutId.value = sessionId
  try {
    await settingsStore.signOutSession(sessionId)
  } catch (err) {
    toast.add({
      title: "Couldn't sign out session",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    signingOutId.value = null
  }
}

async function signOutAllOthers() {
  signingOutOthers.value = true
  try {
    await settingsStore.signOutOtherSessions()
  } catch (err) {
    toast.add({
      title: "Couldn't sign out other devices",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    signingOutOthers.value = false
  }
}

function handleTwoFactorToggle(value: boolean) {
  if (value) {
    twoFactorModalOpen.value = true
  } else {
    twoFactorEnabled.value = false
  }
}

function confirmTwoFactor() {
  twoFactorEnabled.value = true
  twoFactorModalOpen.value = false
}

async function confirmDeleteAccount() {
  if (deletingAccount.value) return
  deletingAccount.value = true
  try {
    await authStore.deleteAccount()
    deleteAccountModalOpen.value = false
    router.push('/')
  } catch (err) {
    toast.add({
      title: "Couldn't delete account",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    deletingAccount.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Password & sign-in</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsActionRow label="Password" value="Last changed 3 months ago" action-label="Change" />
        <SettingsToggleRow
          :model-value="twoFactorEnabled"
          label="Two-factor authentication"
          description="Off, add an extra layer of security."
          @update:model-value="handleTwoFactorToggle"
        />
        <SettingsSelectRow v-model="loginAlerts" label="Login alerts" :items="loginAlertOptions" />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Active sessions</h2>
      <p v-if="settingsStore.sessionsLoading" class="py-2 text-sm text-slate-400">Loading sessions...</p>
      <p v-else-if="settingsStore.sessions.length === 0" class="py-2 text-sm text-slate-400">No active sessions.</p>
      <div v-else class="flex flex-col divide-y divide-white/10">
        <div
          v-for="session in settingsStore.sessions"
          :key="session.id"
          class="flex items-center justify-between gap-4 py-4"
        >
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
          <UBadge v-if="session.current" color="primary" variant="soft" size="sm" class="rounded-full text-xs">
            This device
          </UBadge>
          <UButton
            v-else
            color="neutral"
            variant="soft"
            size="sm"
            class="rounded-full"
            :loading="signingOutId === session.id"
            :disabled="signingOutId === session.id"
            @click="signOutSession(session.id)"
          >
            Sign out
          </UButton>
        </div>
      </div>

      <button
        v-if="settingsStore.sessions.length > 1"
        type="button"
        class="mt-2 w-full cursor-pointer text-center text-sm font-medium text-red-400 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="signingOutOthers"
        @click="signOutAllOthers"
      >
        {{ signingOutOthers ? 'Signing out...' : 'Sign out of all other devices' }}
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
          :disabled="false"
          @action="deleteAccountModalOpen = true"
        />
      </div>
    </div>

    <TwoFactorAuthModal v-model:open="twoFactorModalOpen" :phone="maskedPhone" @confirm="confirmTwoFactor" />
    <DeleteAccountModal v-model:open="deleteAccountModalOpen" @confirm="confirmDeleteAccount" />
  </div>
</template>
