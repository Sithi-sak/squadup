<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { PhStar, PhUserCircle } from '@phosphor-icons/vue'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{
  palName: string
  meta: string
}>()

const open = defineModel<boolean>('open', { required: true })

const emit = defineEmits<{
  submit: [payload: { rating: number; highlights: string[]; comment: string; tipCoins: number }]
  skip: []
}>()

const highlightOptions = ['On time', 'Skilled', 'Friendly', 'Great comms', 'Would rebook', 'Patient']
const tipTiers = [50, 100, 200]
const ratingLabels: Record<number, string> = {
  1: 'Poor',
  2: 'Fair',
  3: 'Good',
  4: 'Great!',
  5: 'Excellent!',
}

const rating = ref(0)
const hoverRating = ref(0)
const highlights = ref<string[]>([])
const comment = ref('')
const tipTier = ref<number | 'custom' | null>(null)
const customTip = ref(0)

watch(open, (isOpen) => {
  if (isOpen) return
  rating.value = 0
  hoverRating.value = 0
  highlights.value = []
  comment.value = ''
  tipTier.value = null
  customTip.value = 0
})

const displayRating = computed(() => hoverRating.value || rating.value)

const tipCoins = computed(() => {
  if (tipTier.value === 'custom') return Math.max(customTip.value, 0)
  return tipTier.value ?? 0
})

function toggleHighlight(option: string) {
  const index = highlights.value.indexOf(option)
  if (index === -1) highlights.value.push(option)
  else highlights.value.splice(index, 1)
}

function skip() {
  emit('skip')
  open.value = false
}

function submit() {
  if (!rating.value) return
  emit('submit', { rating: rating.value, highlights: highlights.value, comment: comment.value, tipCoins: tipCoins.value })
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Rate your session"
    :ui="{ content: 'max-w-lg rounded-3xl', body: 'max-h-[75vh] overflow-y-auto' }"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <div class="flex items-center gap-3">
          <UAvatar :src="resolveAvatarUrl(props.palName)" size="lg" class="bg-white/10 text-slate-300">
            <PhUserCircle :size="26" />
          </UAvatar>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold text-white">{{ palName }}</p>
            <p class="truncate text-sm text-slate-400">{{ meta }}</p>
          </div>
        </div>

        <div class="flex flex-col items-center gap-2 py-2">
          <div class="flex items-center gap-2" @mouseleave="hoverRating = 0">
            <button
              v-for="star in 5"
              :key="star"
              type="button"
              class="transition-transform hover:scale-110"
              @mouseenter="hoverRating = star"
              @click="rating = star"
            >
              <PhStar
                :size="36"
                :weight="star <= displayRating ? 'fill' : 'regular'"
                :class="star <= displayRating ? 'text-amber-400' : 'text-slate-600'"
              />
            </button>
          </div>
          <p v-if="displayRating" class="text-sm font-semibold text-amber-400">
            {{ ratingLabels[displayRating] }} {{ displayRating }} out of 5
          </p>
        </div>

        <div>
          <p class="text-sm font-medium text-slate-300">What went well?</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="option in highlightOptions"
              :key="option"
              type="button"
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                highlights.includes(option)
                  ? 'bg-brand-500 text-white'
                  : 'bg-gray-800/70 text-slate-300 hover:bg-gray-700'
              "
              @click="toggleHighlight(option)"
            >
              {{ option }}
            </button>
          </div>
        </div>

        <UTextarea
          v-model="comment"
          placeholder="Share more about your experience (optional)..."
          variant="subtle"
          :rows="3"
          :ui="{ base: 'bg-gray-800/70 px-4 py-3 text-sm ring-0 hover:bg-gray-800' }"
        />

        <div>
          <p class="text-sm font-medium text-slate-300">Add a tip (optional)</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="tier in tipTiers"
              :key="tier"
              type="button"
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                tipTier === tier ? 'bg-brand-500 text-white' : 'bg-gray-800/70 text-slate-300 hover:bg-gray-700'
              "
              @click="tipTier = tipTier === tier ? null : tier"
            >
              +{{ tier }} SC
            </button>
            <button
              type="button"
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                tipTier === 'custom' ? 'bg-brand-500 text-white' : 'bg-gray-800/70 text-slate-300 hover:bg-gray-700'
              "
              @click="tipTier = tipTier === 'custom' ? null : 'custom'"
            >
              Custom
            </button>
          </div>

          <div v-if="tipTier === 'custom'" class="mt-3 flex items-center gap-3 rounded-2xl bg-gray-800/70 p-3">
            <span class="text-sm text-slate-300">Tip amount</span>
            <UInput v-model.number="customTip" type="number" :min="0" size="sm" variant="subtle" class="ml-auto w-28" />
            <span class="shrink-0 text-sm text-slate-400">SC</span>
          </div>
        </div>

        <div class="flex items-center justify-between border-t border-white/10 pt-4">
          <button type="button" class="text-sm font-medium text-slate-400 hover:text-white" @click="skip">
            Skip
          </button>
          <UButton color="primary" size="lg" class="rounded-full" :disabled="!rating" @click="submit">
            Submit review
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
