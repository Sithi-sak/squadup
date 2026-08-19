<script setup lang="ts">
import { ref } from 'vue'
import { PhUserCircle } from '@phosphor-icons/vue'
import { mockCurrentUser } from '@/mocks/users'
import { mockPlayerProfiles } from '@/mocks/playerProfiles'
import SettingsToggleRow from './SettingsToggleRow.vue'
import SettingsActionRow from './SettingsActionRow.vue'

const profile = mockPlayerProfiles.self!

const displayName = ref(mockCurrentUser.displayName ?? '')
const headline = ref('Immortal duo who actually carries, never battle alone')
const bio = ref(
  'Immortal 3 Duelist main. 300+ carries on SquadUp. I keep it chill, callouts clean, and we win. Available evenings GMT+7.',
)
const languages = ref(['English', 'Khmer'])

const showOnlineStatus = ref(true)
const instantBooking = ref(false)
const emailNotifications = ref(true)
const pushNotifications = ref(true)
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Profile</h2>

      <div class="mt-4 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <UAvatar size="xl" class="bg-white/10 text-slate-300">
            <PhUserCircle :size="28" />
          </UAvatar>
          <div>
            <p class="font-semibold text-white">{{ mockCurrentUser.displayName }}</p>
            <p class="text-sm text-slate-400">{{ profile.tier }} · {{ profile.handle }}</p>
          </div>
        </div>
        <UButton color="neutral" variant="soft" size="md" class="rounded-full" disabled>
          Change photo
        </UButton>
      </div>

      <div class="mt-6 flex flex-col gap-2">
        <label for="profile-display-name" class="text-sm text-slate-300">Display name</label>
        <UInput id="profile-display-name" v-model="displayName" variant="subtle" size="lg" />
      </div>

      <div class="mt-5 flex flex-col gap-2">
        <label for="profile-headline" class="text-sm text-slate-300">Headline</label>
        <UInput id="profile-headline" v-model="headline" variant="subtle" size="lg" />
      </div>

      <div class="mt-5 flex flex-col gap-2">
        <label for="profile-bio" class="text-sm text-slate-300">Bio</label>
        <UTextarea id="profile-bio" v-model="bio" variant="subtle" :rows="3" />
      </div>

      <div class="mt-5 flex flex-col gap-2">
        <span class="text-sm text-slate-300">Languages</span>
        <div class="flex flex-wrap items-center gap-2">
          <UBadge
            v-for="lang in languages"
            :key="lang"
            color="primary"
            variant="soft"
            size="lg"
            class="rounded-full"
          >
            {{ lang }}
          </UBadge>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" disabled>
            + Add
          </UButton>
        </div>
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Preferences</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsToggleRow
          v-model="showOnlineStatus"
          label="Show online status"
          description="Let buyers see when you are available."
        />
        <SettingsToggleRow
          v-model="instantBooking"
          label="Instant booking"
          description="Accept orders without manual approval."
        />
        <SettingsToggleRow
          v-model="emailNotifications"
          label="Email notifications"
          description="New orders, messages and payouts."
        />
        <SettingsToggleRow
          v-model="pushNotifications"
          label="Push notifications"
          description="Real-time alerts on your devices."
        />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Account & security</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsActionRow label="Email" :value="mockCurrentUser.email" action-label="Edit" />
        <SettingsActionRow label="Region" :value="`Cambodia · ${profile.timezone}`" action-label="Edit" />
        <SettingsActionRow label="Password" value="••••••••••" action-label="Change" />
        <SettingsActionRow
          label="Two-factor authentication"
          value="Off, recommended on"
          action-label="Enable"
        />
      </div>
    </div>
  </div>
</template>
