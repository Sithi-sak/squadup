<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useUsersStore } from '@/stores/users'
import BlockedAccountsModal from '@/components/modals/BlockedAccountsModal.vue'
import SettingsSelectRow from './SettingsSelectRow.vue'
import SettingsToggleRow from './SettingsToggleRow.vue'
import SettingsActionRow from './SettingsActionRow.vue'

const whoCanSeeProfile = ref('Everyone')
const whoCanMessageYou = ref('Followers')
const showOnlineStatus = ref(true)
const showActivityStatus = ref(true)
const appearInSearch = ref(true)
const personalizedRecommendations = ref(true)

/** Real count from `GET /users/me/blocks` (4.39), replacing `mockBlockedAccountsCount`. */
const usersStore = useUsersStore()
const blockedCount = ref(0)
const blockedModalOpen = ref(false)
const blockedLabel = computed(() =>
  blockedCount.value === 1 ? '1 account blocked' : `${blockedCount.value} accounts blocked`,
)

onMounted(async () => {
  try {
    blockedCount.value = (await usersStore.fetchMyBlocks()).length
  } catch {
    // Leave the count at 0 rather than blocking the whole tab on it.
  }
})

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
          :value="blockedLabel"
          action-label="Manage"
          :disabled="false"
          @action="blockedModalOpen = true"
        />
        <SettingsActionRow
          label="Download your data"
          value="Request a copy of your information"
          action-label="Request"
        />
      </div>
    </div>

    <BlockedAccountsModal v-model:open="blockedModalOpen" @changed="blockedCount = $event" />
  </div>
</template>
