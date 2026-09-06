<script setup lang="ts">
import { computed, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { mockCurrentUser } from '@/mocks/users'
import { mockPlayerProfiles } from '@/mocks/playerProfiles'
import { mockAccountDetails } from '@/mocks/settings'
import { useAuthStore } from '@/stores/auth'
import SettingsActionRow from './SettingsActionRow.vue'

const authStore = useAuthStore()
const toast = useToast()

const profile = computed(() =>
  mockCurrentUser.playerId ? mockPlayerProfiles[mockCurrentUser.playerId] : null,
)

const displayName = ref(authStore.user?.displayName ?? mockCurrentUser.displayName ?? '')
const username = ref(authStore.user?.handle ?? '')
const email = computed(() => authStore.user?.email ?? mockCurrentUser.email)
const phone = ref(authStore.user?.phone ?? '')
const country = ref(authStore.user?.country ?? '')
const language = ref(profile.value?.language ?? 'English')
const timezone = ref(profile.value?.timezone ?? 'GMT+07:00 · Phnom Penh')

const countryOptions = ['Cambodia', 'Vietnam', 'Philippines', 'Singapore', 'Indonesia', 'Malaysia']
const languageOptions = ['English', 'Khmer', 'Vietnamese']
const timezoneOptions = ['GMT+06:30', 'GMT+07:00 · Phnom Penh', 'GMT+08:00', 'GMT+09:00']

const accountType = computed(() =>
  profile.value ? profile.value.tier.replace(/^(\D+?)\s*(\d+)$/, '$1 · Level $2') : 'User',
)

const savingAccount = ref(false)

async function saveAccountDetails() {
  savingAccount.value = true
  try {
    await authStore.updateAccount({
      displayName: displayName.value,
      handle: username.value,
      phone: phone.value,
      country: country.value,
    })
    toast.add({ title: 'Account details saved', color: 'success' })
  } catch (err) {
    toast.add({
      title: "Couldn't save account details",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    savingAccount.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Account details</h2>

      <div class="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div class="flex flex-col gap-2">
          <label for="account-display-name" class="text-sm text-slate-300">Display name</label>
          <UInput id="account-display-name" v-model="displayName" variant="subtle" size="lg" />
        </div>
        <div class="flex flex-col gap-2">
          <label for="account-username" class="text-sm text-slate-300">Username</label>
          <UInput id="account-username" v-model="username" variant="subtle" size="lg" />
        </div>
        <div class="flex flex-col gap-2">
          <label for="account-email" class="text-sm text-slate-300">Email</label>
          <UInput id="account-email" :model-value="email" type="email" disabled variant="subtle" size="lg" />
          <p class="text-xs text-slate-500">Changing your email requires verification, coming soon.</p>
        </div>
        <div class="flex flex-col gap-2">
          <label for="account-phone" class="text-sm text-slate-300">Phone</label>
          <UInput id="account-phone" v-model="phone" type="tel" variant="subtle" size="lg" />
        </div>
        <div class="flex flex-col gap-2">
          <label for="account-country" class="text-sm text-slate-300">Country / Region</label>
          <USelect id="account-country" v-model="country" :items="countryOptions" variant="subtle" size="lg" />
        </div>
        <div class="flex flex-col gap-2">
          <label for="account-language" class="text-sm text-slate-300">Language</label>
          <USelect id="account-language" v-model="language" :items="languageOptions" variant="subtle" size="lg" />
        </div>
      </div>

      <div class="mt-5 flex flex-col gap-2 sm:w-[calc(50%-0.625rem)]">
        <label for="account-timezone" class="text-sm text-slate-300">Timezone</label>
        <USelect id="account-timezone" v-model="timezone" :items="timezoneOptions" variant="subtle" size="lg" />
      </div>

      <div class="mt-5 flex justify-end">
        <UButton color="primary" :loading="savingAccount" class="rounded-full px-6" @click="saveAccountDetails">
          Save changes
        </UButton>
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Account status</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <div class="flex items-center justify-between gap-4 py-4">
          <div>
            <p class="text-sm text-slate-400">Member since</p>
            <p class="font-medium text-white">{{ mockAccountDetails.memberSince }}</p>
          </div>
        </div>
        <div class="flex items-center justify-between gap-4 py-4">
          <div>
            <p class="text-sm text-slate-400">Account type</p>
            <p class="font-medium text-white">{{ accountType }}</p>
          </div>
        </div>
        <SettingsActionRow
          label="Deactivate account"
          value="Temporarily hide your profile"
          action-label="Deactivate"
          danger
        />
      </div>
    </div>
  </div>
</template>
