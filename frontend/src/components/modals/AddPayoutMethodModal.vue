<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhBank, PhCreditCard } from '@phosphor-icons/vue'
import visaIcon from '@/assets/visa.svg'
import mastercardIcon from '@/assets/mastercard.svg'
import { cardDigits, cardNetwork, formatCardNumber, isValidCardNumber } from '@/utils/card'
import { useWalletStore } from '@/stores/wallet'

const { open } = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [boolean]; added: [] }>()

const walletStore = useWalletStore()
const toast = useToast()

const brand = ref<'card' | 'bank'>('card')
const account = ref('')
const submitting = ref(false)

/** Reset on every open so a cancelled attempt does not leak into the next one. */
watch(
  () => open,
  (isOpen) => {
    if (!isOpen) return
    brand.value = 'card'
    account.value = ''
  },
)

const digits = computed(() => cardDigits(account.value))

/** Swaps the icon while you type, the way a real card form does. */
const network = computed(() => cardNetwork(digits.value))
const networkIcon = computed(() =>
  network.value === 'visa' ? visaIcon : network.value === 'mastercard' ? mastercardIcon : null,
)

/** Mirrors the backend's validation (`create_payout_method`) so the button is only live for
 * input that would actually be accepted. */
const canSubmit = computed(() =>
  brand.value === 'card' ? isValidCardNumber(digits.value) : digits.value.length >= 6,
)

/** Only once they have typed enough for the verdict to be meaningful - flagging "invalid" at the
 * fourth digit would be noise, not help. */
const showCardError = computed(
  () => brand.value === 'card' && digits.value.length >= 12 && !canSubmit.value,
)

function onAccountInput(value: string | number) {
  const text = String(value)
  account.value = brand.value === 'card' ? formatCardNumber(text) : text
}

async function submit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    await walletStore.addPayoutMethod({ brand: brand.value, account: account.value.trim() })
    toast.add({ title: 'Payout method added', color: 'success' })
    emit('added')
    emit('update:open', false)
  } catch (err) {
    toast.add({
      title: "Couldn't add payout method",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <UModal
    :open="open"
    title="Add payout method"
    description="Where should SquadUp send your withdrawals?"
    :ui="{ content: 'max-w-md rounded-3xl' }"
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3">
          <button
            type="button"
            class="flex cursor-pointer flex-col items-center gap-2 rounded-xl border bg-gray-700/40 px-4 py-4 transition-colors"
            :class="brand === 'card' ? 'border-brand-400' : 'border-transparent hover:border-white/10'"
            @click="brand = 'card'"
          >
            <PhCreditCard :size="24" weight="fill" class="text-brand-400" />
            <span class="text-sm font-medium text-white">Card</span>
          </button>
          <button
            type="button"
            class="flex cursor-pointer flex-col items-center gap-2 rounded-xl border bg-gray-700/40 px-4 py-4 transition-colors"
            :class="brand === 'bank' ? 'border-brand-400' : 'border-transparent hover:border-white/10'"
            @click="brand = 'bank'"
          >
            <PhBank :size="24" weight="fill" class="text-brand-400" />
            <span class="text-sm font-medium text-white">Bank transfer</span>
            <span class="text-xs text-slate-400">ABA</span>
          </button>
        </div>

        <p v-if="brand === 'bank'" class="text-sm text-slate-400">
          ABA is the only bank supported right now.
        </p>

        <UFormField
          :label="brand === 'card' ? 'Card number' : 'ABA account number'"
          :error="showCardError ? 'That card number is not valid.' : undefined"
          class="text-slate-300"
        >
          <UInput
            :model-value="account"
            type="text"
            inputmode="numeric"
            autocomplete="off"
            :placeholder="brand === 'card' ? '4242 4242 4242 4242' : '000 123 456'"
            variant="subtle"
            size="lg"
            class="w-full"
            @update:model-value="onAccountInput"
            @keyup.enter="submit"
          >
            <template v-if="brand === 'card' && networkIcon" #trailing>
              <img :src="networkIcon" alt="" class="h-5 w-5" />
            </template>
          </UInput>
        </UFormField>

        <p class="text-sm text-slate-400">
          Only the last four digits are stored, so the full number never sits in your profile.
        </p>

        <div class="flex justify-end gap-3 border-t border-white/10 pt-4">
          <UButton color="neutral" variant="soft" class="rounded-full" @click="emit('update:open', false)">
            Cancel
          </UButton>
          <UButton
            color="primary"
            class="rounded-full"
            :loading="submitting"
            :disabled="!canSubmit || submitting"
            @click="submit"
          >
            Add method
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
