<script setup lang="ts">
import { ref } from 'vue'
import { mockBlockedAccountsCount } from '@/mocks/settings'
import SettingsSelectRow from './SettingsSelectRow.vue'
import SettingsToggleRow from './SettingsToggleRow.vue'
import SettingsActionRow from './SettingsActionRow.vue'

const whoCanSeeProfile = ref('Everyone')
const whoCanMessageYou = ref('Followers')
const showOnlineStatus = ref(true)
const showActivityStatus = ref(true)
const appearInSearch = ref(true)
const personalizedRecommendations = ref(true)

const profileVisibilityOptions = ['Everyone', 'Followers', 'No one']
const messagePermissionOptions = ['Everyone', 'Followers', 'No one']
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Profile privacy</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsSelectRow v-model="whoCanSeeProfile" label="Who can see your profile" :items="profileVisibilityOptions" />
        <SettingsSelectRow v-model="whoCanMessageYou" label="Who can message you" :items="messagePermissionOptions" />
        <SettingsToggleRow
          v-model="showOnlineStatus"
          label="Show online status"
          description="Let others see when you are active."
        />
        <SettingsToggleRow
          v-model="showActivityStatus"
          label="Show activity status"
          description="Display what you are currently playing."
        />
        <SettingsToggleRow
          v-model="appearInSearch"
          label="Appear in search"
          description="Let people find you by name or @handle."
        />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Data & personalization</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsToggleRow
          v-model="personalizedRecommendations"
          label="Personalized recommendations"
          description="Use my activity to suggest Pals and games."
        />
        <SettingsActionRow
          label="Blocked accounts"
          :value="`${mockBlockedAccountsCount} accounts blocked`"
          action-label="Manage"
        />
        <SettingsActionRow
          label="Download your data"
          value="Request a copy of your information"
          action-label="Request"
        />
      </div>
    </div>
  </div>
</template>
