<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhPaperclip, PhUserCircle } from '@phosphor-icons/vue'
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
  confirm: [payload: { reason: string; outcome: 'full' | 'partial' | 'reporting'; note: string }]
}>()

const reasons = [
  "The Pal didn't show up",
  'Service not as described',
  'Poor quality or unskilled',
  'Inappropriate behaviour',
  'Billing - charged incorrectly',
  'Something else',
]

const outcomes: { value: 'full' | 'partial' | 'reporting'; label: string }[] = [
  { value: 'full', label: 'Full refund' },
  { value: 'partial', label: 'Partial refund' },
  { value: 'reporting', label: 'Just reporting it' },
]

const reason = ref<string | null>(null)
const outcome = ref<'full' | 'partial' | 'reporting'>('full')
const note = ref('')

watch(open, (isOpen) => {
  if (!isOpen) return
  reason.value = null
  outcome.value = 'full'
  note.value = ''
})

function confirm() {
  if (!reason.value) return
  emit('confirm', { reason: reason.value, outcome: outcome.value, note: note.value })
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Report an issue"
    :description="`Order #${orderNumber} · we usually respond within 24 hours`"
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
          <p class="text-sm font-medium text-slate-300">What went wrong?</p>
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
          <p class="text-sm font-medium text-slate-300">What outcome would you like?</p>
          <div class="mt-2 grid grid-cols-3 gap-3">
            <button
              v-for="option in outcomes"
              :key="option.value"
              type="button"
              class="rounded-full px-3 py-3 text-center text-sm font-semibold transition-colors"
              :class="
                outcome === option.value
                  ? 'bg-brand-500 text-gray-950'
                  : 'bg-gray-800/70 text-white hover:bg-gray-800'
              "
              @click="outcome = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <UTextarea
          v-model="note"
          placeholder="Tell us what happened..."
          variant="subtle"
          :rows="3"
          :ui="{ base: 'bg-gray-800/70 px-4 py-3 text-sm ring-0 hover:bg-gray-800' }"
        />

        <label
          class="flex cursor-pointer flex-col items-center gap-1 rounded-2xl border border-dashed border-white/15 px-4 py-8 text-center transition-colors hover:border-white/25 hover:bg-gray-800/40"
        >
          <input type="file" multiple accept="image/*,video/*" class="hidden" />
          <span class="inline-flex items-center gap-2 text-sm font-medium text-white">
            <PhPaperclip :size="18" />
            Add screenshots or a clip
          </span>
          <span class="text-sm text-slate-400">Evidence helps us resolve faster</span>
        </label>

        <div class="grid grid-cols-2 gap-3 border-t border-white/10 pt-4">
          <UButton color="neutral" variant="soft" size="lg" block class="rounded-full" @click="open = false">
            Cancel
          </UButton>
          <UButton color="primary" size="lg" block class="rounded-full" :disabled="!reason" @click="confirm">
            Submit request
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
