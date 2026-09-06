<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhAppleLogo, PhDotsThree } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import visaIcon from '@/assets/visa.svg'
import { mockCurrentUser } from '@/mocks/users'
import { mockPlayerProfiles } from '@/mocks/playerProfiles'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import SettingsSelectRow from './SettingsSelectRow.vue'
import SettingsToggleRow from './SettingsToggleRow.vue'

const profile = mockPlayerProfiles.self!
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const toast = useToast()

const isPal = computed(() => Boolean(authStore.user?.playerId))

onMounted(() => {
  settingsStore.fetchPaymentCards()
})

const payoutSchedule = ref('Weekly')
const currencyDisplay = ref('USD ($)')
const autoTopUp = ref(false)

const scheduleOptions = ['Daily', 'Weekly', 'Bi-weekly', 'Monthly']
const currencyOptions = ['USD ($)', 'KHR (៛)', 'THB (฿)']

const busyCardId = ref<string | null>(null)

const cardMenuItems = (cardId: string) => [
  [
    { label: 'Set as default', onSelect: () => setDefault(cardId) },
    { label: 'Remove', onSelect: () => removeCard(cardId) },
  ],
]

async function setDefault(cardId: string) {
  busyCardId.value = cardId
  try {
    await settingsStore.setDefaultPaymentCard(cardId)
  } catch (err) {
    toast.add({
      title: "Couldn't set default card",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    busyCardId.value = null
  }
}

async function removeCard(cardId: string) {
  busyCardId.value = cardId
  try {
    await settingsStore.removePaymentCard(cardId)
  } catch (err) {
    toast.add({
      title: "Couldn't remove card",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    busyCardId.value = null
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div v-if="isPal" class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Payout method</h2>

      <div class="mt-3 flex items-center justify-between gap-3 rounded-xl bg-gray-700/50 px-4 py-3">
        <div class="flex items-center gap-3">
          <img :src="coinIcon" alt="" class="h-8 w-8" />
          <div>
            <p class="font-semibold text-white">Squad Coin Wallet</p>
            <p class="text-sm text-slate-400">
              {{ profile.handle }} · Balance {{ mockCurrentUser.coinBalance.toLocaleString() }} SC
            </p>
          </div>
        </div>
        <UBadge color="primary" variant="soft" size="sm" class="rounded-full">Default</UBadge>
      </div>

      <button
        type="button"
        disabled
        class="mt-3 w-full cursor-not-allowed rounded-xl border border-dashed border-white/15 py-3 text-sm font-medium text-brand-400"
      >
        + Add payout method
      </button>

      <div class="flex flex-col divide-y divide-white/10">
        <SettingsSelectRow v-model="payoutSchedule" label="Payout schedule" :items="scheduleOptions" />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Payment methods</h2>

      <div class="mt-3 flex flex-col gap-3">
        <p v-if="settingsStore.paymentCardsLoading" class="py-2 text-sm text-slate-400">Loading payment methods...</p>
        <p v-else-if="settingsStore.paymentCards.length === 0" class="py-2 text-sm text-slate-400">
          No payment methods yet.
        </p>
        <div
          v-for="card in settingsStore.paymentCards"
          :key="card.id"
          class="flex items-center justify-between gap-3 rounded-xl bg-gray-700/50 px-4 py-3"
        >
          <div class="flex items-center gap-3">
            <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-white">
              <img v-if="card.brand === 'visa'" :src="visaIcon" alt="" class="h-7 w-7" />
              <PhAppleLogo v-else :size="18" class="text-white" />
            </div>
            <div>
              <p class="font-medium text-white">{{ card.label }}</p>
              <p class="text-sm text-slate-400">{{ card.detail }}</p>
            </div>
          </div>
          <UBadge v-if="card.isDefault" color="primary" variant="soft" size="md" class="rounded-full">
            Default
          </UBadge>
          <UDropdownMenu v-else :items="cardMenuItems(card.id)">
            <UButton
              color="neutral"
              variant="ghost"
              square
              size="sm"
              :ui="{ base: 'rounded-full' }"
              aria-label="Card options"
              :loading="busyCardId === card.id"
              :disabled="busyCardId === card.id"
            >
              <PhDotsThree :size="18" />
            </UButton>
          </UDropdownMenu>
        </div>
      </div>

      <button
        type="button"
        disabled
        class="mt-3 w-full cursor-not-allowed rounded-xl border border-dashed border-white/15 py-3 text-sm font-medium text-brand-400"
      >
        + Add card
      </button>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Preferences</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsSelectRow v-model="currencyDisplay" label="Currency display" :items="currencyOptions" />
        <SettingsToggleRow
          v-model="autoTopUp"
          label="Auto top-up when low"
          description="Buy 990 SC automatically below 200 SC."
        />
      </div>
    </div>
  </div>
</template>
