<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhAppleLogo, PhBank, PhCreditCard, PhDotsThree } from '@phosphor-icons/vue'
import visaIcon from '@/assets/visa.svg'
import mastercardIcon from '@/assets/mastercard.svg'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { useWalletStore } from '@/stores/wallet'
import AddPayoutMethodModal from '@/components/modals/AddPayoutMethodModal.vue'
import SettingsSelectRow from './SettingsSelectRow.vue'
import SettingsToggleRow from './SettingsToggleRow.vue'

const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const walletStore = useWalletStore()
const toast = useToast()

const isPal = computed(() => Boolean(authStore.user?.playerId))

onMounted(() => {
  settingsStore.fetchPaymentCards()
  if (isPal.value) walletStore.fetchPayoutMethods()
})

/** `payout_methods.brand` stores the detected card network (4.32). */
function brandIcon(brand: string) {
  if (brand === 'visa') return visaIcon
  if (brand === 'mastercard') return mastercardIcon
  return null
}

const addingPayoutMethod = ref(false)
const busyMethodId = ref<string | null>(null)

const payoutMenuItems = (methodId: string) => [
  [
    { label: 'Set as default', onSelect: () => setDefaultPayoutMethod(methodId) },
    { label: 'Remove', onSelect: () => removePayoutMethod(methodId) },
  ],
]

async function setDefaultPayoutMethod(methodId: string) {
  busyMethodId.value = methodId
  try {
    await walletStore.setDefaultPayoutMethod(methodId)
  } catch (err) {
    toast.add({
      title: "Couldn't set default payout method",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    busyMethodId.value = null
  }
}

async function removePayoutMethod(methodId: string) {
  busyMethodId.value = methodId
  try {
    await walletStore.removePayoutMethod(methodId)
  } catch (err) {
    toast.add({
      title: "Couldn't remove payout method",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    busyMethodId.value = null
  }
}

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

      <div v-if="walletStore.payoutMethods.length" class="mt-3 flex flex-col gap-3">
        <div
          v-for="method in walletStore.payoutMethods"
          :key="method.id"
          class="flex items-center justify-between gap-3 rounded-xl bg-gray-700/50 px-4 py-3"
        >
          <div class="flex items-center gap-3">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white">
              <img v-if="brandIcon(method.brand)" :src="brandIcon(method.brand)!" alt="" class="h-7 w-7" />
              <PhBank v-else-if="method.brand === 'bank'" :size="20" weight="fill" class="text-gray-800" />
              <PhCreditCard v-else :size="20" weight="fill" class="text-gray-800" />
            </div>
            <div>
              <p class="font-semibold text-white">{{ method.label }}</p>
              <p class="text-sm text-slate-400">{{ method.detail }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <UBadge v-if="method.isDefault" color="primary" variant="soft" size="md" class="rounded-full">
              Default
            </UBadge>
            <UDropdownMenu :items="payoutMenuItems(method.id)">
              <UButton
                color="neutral"
                variant="ghost"
                square
                :disabled="busyMethodId === method.id"
                aria-label="Payout method options"
              >
                <PhDotsThree :size="20" weight="bold" />
              </UButton>
            </UDropdownMenu>
          </div>
        </div>
      </div>

      <p v-else class="mt-3 text-sm text-slate-400">No payout method on file yet.</p>

      <button
        type="button"
        class="mt-3 w-full cursor-pointer rounded-xl border border-dashed border-white/15 py-3 text-sm font-medium text-brand-400 transition-colors hover:border-brand-400/50 hover:bg-white/5"
        @click="addingPayoutMethod = true"
      >
        + Add payout method
      </button>

      <AddPayoutMethodModal v-model:open="addingPayoutMethod" />

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
