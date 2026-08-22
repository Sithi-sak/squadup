<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhLockSimple } from '@phosphor-icons/vue'

const props = defineProps<{
  handle: string
}>()

const open = defineModel<boolean>('open', { required: true })

const emit = defineEmits<{
  submit: [payload: { reason: string; details: string; alsoBlock: boolean }]
}>()

const reasons = [
  'Harassment or bullying',
  'Spam or a scam',
  'Inappropriate content',
  'Impersonation',
  'Underage or safety concern',
  'Something else',
]

const reason = ref<string | null>(null)
const details = ref('')
const alsoBlock = ref(true)

watch(open, (isOpen) => {
  if (!isOpen) return
  reason.value = null
  details.value = ''
  alsoBlock.value = true
})

function submit() {
  if (!reason.value) return
  emit('submit', { reason: reason.value, details: details.value, alsoBlock: alsoBlock.value })
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="`Report ${props.handle}`"
    :ui="{ content: 'max-w-lg rounded-3xl', body: 'max-h-[75vh] overflow-y-auto' }"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <div class="flex items-start gap-2.5 rounded-2xl bg-brand-900/20 p-3.5 text-sm text-brand-300">
          <PhLockSimple :size="18" weight="fill" class="mt-0.5 shrink-0" />
          <p>Reports are confidential — {{ props.handle }} won't know who reported them.</p>
        </div>

        <div>
          <p class="text-sm font-medium text-slate-300">Why are you reporting this?</p>
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

        <UTextarea
          v-model="details"
          placeholder="Add details (optional) — what happened?"
          variant="subtle"
          :rows="2"
          :ui="{ base: 'bg-gray-800/70 px-4 py-3 text-sm ring-0 hover:bg-gray-800' }"
        />

        <div class="flex items-center justify-between gap-4 rounded-2xl bg-gray-800/70 p-4">
          <div class="min-w-0">
            <p class="font-medium text-white">Also block {{ props.handle }}</p>
            <p class="text-sm text-slate-400">They can't message, book, or view your profile.</p>
          </div>
          <USwitch v-model="alsoBlock" color="primary" class="shrink-0" />
        </div>

        <div class="grid grid-cols-2 gap-3 border-t border-white/10 pt-4">
          <UButton color="neutral" variant="soft" size="lg" block class="rounded-full" @click="open = false">
            Cancel
          </UButton>
          <UButton color="error" size="lg" block class="rounded-full" :disabled="!reason" @click="submit">
            Submit report
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
