<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhCamera } from '@phosphor-icons/vue'
import type { AccountStepData } from './types'

const data = defineModel<AccountStepData>({ required: true })

const emit = defineEmits<{ continue: [] }>()

const regionOptions = [
  'Cambodia',
  'Vietnam',
  'Philippines',
  'Singapore',
  'Indonesia',
  'Malaysia',
]

const timezoneOptions = [
  'GMT+06:30',
  'GMT+07:00',
  'GMT+08:00',
  'GMT+09:00',
]

const fileInput = ref<HTMLInputElement | null>(null)

const emailValid = computed(() => /^\S+@\S+\.\S+$/.test(data.value.email))
const canSubmit = computed(
  () =>
    data.value.displayName.trim().length > 0 &&
    emailValid.value &&
    data.value.phone.trim().length > 0 &&
    data.value.region.length > 0 &&
    data.value.timezone.length > 0 &&
    data.value.password.length >= 8 &&
    data.value.agreedToTerms,
)

const fieldUi = {
  base: 'bg-gray-900 px-5 py-3.5 text-sm ring-0 focus-visible:ring-2 focus-visible:ring-brand-600',
}
const selectUi = { base: 'bg-gray-900 px-5 py-3.5 text-sm ring-0 hover:bg-gray-800' }

function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (data.value.avatarUrl) URL.revokeObjectURL(data.value.avatarUrl)
  data.value.avatarUrl = URL.createObjectURL(file)
}
</script>

<template>
  <h2 class="text-2xl font-semibold text-white sm:text-3xl">Your account details</h2>
  <p class="mt-2 text-slate-400">
    The basics to get your Pal application started. This info stays private.
  </p>

  <form class="mt-8 flex flex-col gap-6" @submit.prevent="canSubmit && emit('continue')">
    <div class="flex items-center gap-4">
      <div
        class="size-16 shrink-0 overflow-hidden rounded-full bg-linear-to-br from-gray-600 to-gray-800"
      >
        <img
          v-if="data.avatarUrl"
          :src="data.avatarUrl"
          alt=""
          class="size-full object-cover"
        />
      </div>
      <div>
        <UButton
          color="neutral"
          variant="soft"
          class="gap-2 rounded-full bg-gray-800 text-white hover:bg-gray-700"
          @click="openFilePicker"
        >
          <PhCamera :size="16" />
          Upload photo
        </UButton>
        <p class="mt-2 text-xs text-slate-400">PNG or JPG · a square image works best</p>
      </div>
      <input
        ref="fileInput"
        type="file"
        accept="image/png,image/jpeg"
        class="hidden"
        @change="onFileSelected"
      />
    </div>

    <div class="flex flex-col gap-2">
      <label for="displayName" class="text-sm font-medium text-white">Display name</label>
      <UInput
        id="displayName"
        v-model="data.displayName"
        placeholder="Ari"
        variant="subtle"
        size="md"
        :ui="fieldUi"
      />
    </div>

    <div class="grid gap-6 sm:grid-cols-2">
      <div class="flex flex-col gap-2">
        <label for="email" class="text-sm font-medium text-white">Email</label>
        <UInput
          id="email"
          v-model="data.email"
          type="email"
          placeholder="ari@squadup.gg"
          autocomplete="email"
          variant="subtle"
          size="md"
          :ui="fieldUi"
        />
      </div>
      <div class="flex flex-col gap-2">
        <label for="phone" class="text-sm font-medium text-white">Phone</label>
        <UInput
          id="phone"
          v-model="data.phone"
          type="tel"
          placeholder="+855 12 345 678"
          autocomplete="tel"
          variant="subtle"
          size="md"
          :ui="fieldUi"
        />
      </div>
    </div>

    <div class="grid gap-6 sm:grid-cols-2">
      <div class="flex flex-col gap-2">
        <label for="region" class="text-sm font-medium text-white">Region</label>
        <USelect
          id="region"
          v-model="data.region"
          :items="regionOptions"
          placeholder="Select region"
          variant="subtle"
          size="md"
          :ui="selectUi"
        />
      </div>
      <div class="flex flex-col gap-2">
        <label for="timezone" class="text-sm font-medium text-white">Timezone</label>
        <USelect
          id="timezone"
          v-model="data.timezone"
          :items="timezoneOptions"
          placeholder="Select timezone"
          variant="subtle"
          size="md"
          :ui="selectUi"
        />
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <label for="password" class="text-sm font-medium text-white">Password</label>
      <UInput
        id="password"
        v-model="data.password"
        type="password"
        autocomplete="new-password"
        variant="subtle"
        size="xl"
        :ui="fieldUi"
      />
    </div>

    <UCheckbox
      v-model="data.agreedToTerms"
      label="I'm 18 or older and agree to the Pal Terms and Community Guidelines."
      class="text-sm text-slate-300"
    />

    <USeparator />

    <div class="flex justify-end">
      <UButton
        type="submit"
        color="primary"
        :disabled="!canSubmit"
        class="justify-center rounded-full px-8 py-2 text-base"
      >
        Continue
      </UButton>
    </div>
  </form>
</template>
