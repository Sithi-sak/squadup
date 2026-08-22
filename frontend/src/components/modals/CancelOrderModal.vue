<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { PhInfo, PhUserCircle } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'

const props = defineProps<{
  orderNumber: string
  palName: string
  serviceTitle: string
  meta: string
  totalCoins: number
}>()

const open = defineModel<boolean>('open', { required: true })

const emit = defineEmits<{
  confirm: [payload: { reason: string; refundOption: 'full' | 'partial' | 'none'; refundCoins: number; note: string }]
}>()

const reasons = [
  "Buyer didn't show up",
  'Buyer requested to cancel',
  'Scheduling conflict',
  "I can't complete this service",
  'Payment or dispute issue',
  'Other',
]

const reason = ref<string | null>(null)
const refundOption = ref<'full' | 'partial' | 'none'>('full')
const partialCoins = ref(Math.round(props.totalCoins / 2))
const note = ref('')

watch(open, (isOpen) => {
  if (!isOpen) return
  reason.value = null
  refundOption.value = 'full'
  partialCoins.value = Math.round(props.totalCoins / 2)
  note.value = ''
})

const refundCoins = computed(() => {
  if (refundOption.value === 'full') return props.totalCoins
  if (refundOption.value === 'partial') return Math.min(Math.max(partialCoins.value, 0), props.totalCoins)
  return 0
})

const confirmLabel = computed(() =>
  refundCoins.value > 0 ? `Cancel & refund ${refundCoins.value} SC` : 'Cancel order',
)

function confirm() {
  if (!reason.value) return
  emit('confirm', { reason: reason.value, refundOption: refundOption.value, refundCoins: refundCoins.value, note: note.value })
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Cancel order"
    :description="`Order #${orderNumber}`"
    :ui="{ content: 'max-w-lg rounded-3xl', body: 'max-h-[75vh] overflow-y-auto' }"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <div class="flex items-center gap-3 rounded-2xl bg-gray-800/70 p-4">
          <UAvatar size="lg" class="bg-white/10 text-slate-300">
            <PhUserCircle :size="26" />
          </UAvatar>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold text-white">{{ palName }} · {{ serviceTitle }}</p>
            <p class="truncate text-sm text-slate-400">{{ meta }}</p>
          </div>
          <span class="inline-flex shrink-0 items-center gap-1.5 text-sm font-semibold text-white">
            <img :src="coinIcon" alt="" class="h-4 w-4" />
            {{ totalCoins }}
          </span>
        </div>

        <div>
          <p class="text-sm font-medium text-slate-300">Reason for cancelling</p>
          <div class="mt-2 flex flex-col gap-2">
            <button
              v-for="option in reasons"
              :key="option"
              type="button"
              class="flex w-full items-center gap-3 rounded-full px-4 py-3.5 text-left text-sm font-regular ring-1 ring-inset transition-colors"
              :class="
                reason === option
                  ? 'bg-brand-900/20 ring-brand-500'
                  : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
              "
              @click="reason = option"
            >
              <span
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2"
                :class="reason === option ? 'border-brand-500' : 'border-white/20'"
              >
                <span v-if="reason === option" class="h-2.5 w-2.5 rounded-full bg-brand-500" />
              </span>
              <span class="text-white">{{ option }}</span>
            </button>
          </div>
        </div>

        <div>
          <p class="text-sm font-medium text-slate-300">Refund the buyer?</p>
          <div class="mt-2 grid grid-cols-3 gap-3">
            <button
              type="button"
              class="rounded-2xl px-3 py-3 text-center ring-1 ring-inset transition-colors"
              :class="
                refundOption === 'full'
                  ? 'bg-brand-900/20 ring-brand-500'
                  : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
              "
              @click="refundOption = 'full'"
            >
              <p class="font-semibold text-white">Full refund</p>
              <p class="mt-0.5 text-sm text-slate-400">{{ totalCoins }} SC</p>
            </button>
            <button
              type="button"
              class="rounded-2xl px-3 py-3 text-center ring-1 ring-inset transition-colors"
              :class="
                refundOption === 'partial'
                  ? 'bg-brand-900/20 ring-brand-500'
                  : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
              "
              @click="refundOption = 'partial'"
            >
              <p class="font-semibold text-white">Partial</p>
              <p class="mt-0.5 text-sm text-slate-400">
                {{ refundOption === 'partial' ? `${refundCoins} SC` : 'choose' }}
              </p>
            </button>
            <button
              type="button"
              class="rounded-2xl px-3 py-3 text-center ring-1 ring-inset transition-colors"
              :class="
                refundOption === 'none'
                  ? 'bg-brand-900/20 ring-brand-500'
                  : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
              "
              @click="refundOption = 'none'"
            >
              <p class="font-semibold text-white">No refund</p>
              <p class="mt-0.5 text-sm text-slate-400">0 SC</p>
            </button>
          </div>

          <div v-if="refundOption === 'partial'" class="mt-3 flex items-center gap-3 rounded-2xl bg-gray-800/70 p-3">
            <span class="text-sm text-slate-300">Refund amount</span>
            <UInput
              v-model.number="partialCoins"
              type="number"
              :min="0"
              :max="totalCoins"
              size="sm"
              variant="subtle"
              class="ml-auto w-28"
            />
            <span class="shrink-0 text-sm text-slate-400">/ {{ totalCoins }} SC</span>
          </div>
        </div>

        <div
          class="flex items-start gap-2.5 rounded-2xl p-3.5 text-sm"
          :class="refundOption === 'none' ? 'bg-amber-500/10 text-amber-300' : 'bg-brand-900/20 text-brand-300'"
        >
          <PhInfo :size="18" weight="bold" class="mt-0.5 shrink-0" />
          <p v-if="refundOption === 'none'">
            Cancelling without a refund may lower your rating. Only use this when the buyer is at fault.
          </p>
          <p v-else>
            If the cancellation is reasonable, refunding keeps your rating high. Refunds return Squad Coin to the
            buyer's wallet instantly.
          </p>
        </div>

        <UTextarea
          v-model="note"
          placeholder="Add a note for the buyer (optional)..."
          variant="subtle"
          :rows="2"
          :ui="{ base: 'bg-gray-800/70 px-4 py-3 text-sm ring-0 hover:bg-gray-800' }"
        />

        <div class="grid grid-cols-2 gap-3 border-t border-white/10 pt-4">
          <UButton color="neutral" variant="soft" size="lg" block class="rounded-full" @click="open = false">
            Keep order
          </UButton>
          <UButton color="error" size="lg" block class="rounded-full" :disabled="!reason" @click="confirm">
            {{ confirmLabel }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
