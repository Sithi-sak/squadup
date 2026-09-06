<script setup lang="ts">
import { PhInfo, PhUserCircle } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{
  palName: string
  billingCycle: string
  priceCoins: number
  accessUntil: string
}>()

const open = defineModel<boolean>('open', { required: true })

const emit = defineEmits<{ confirm: [] }>()

function confirm() {
  emit('confirm')
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Cancel subscription"
    :description="`Subscribed to ${palName}`"
    :ui="{ content: 'max-w-lg rounded-3xl' }"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <div class="flex items-center gap-3 rounded-2xl bg-gray-800/70 p-4">
          <UAvatar :src="resolveAvatarUrl(props.palName)" size="lg" class="bg-white/10 text-slate-300">
            <PhUserCircle :size="26" />
          </UAvatar>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold text-white">{{ palName }}</p>
            <p class="truncate text-sm text-slate-400">{{ billingCycle }}</p>
          </div>
          <span class="inline-flex shrink-0 items-center gap-1.5 text-sm font-semibold text-white">
            <img :src="coinIcon" alt="" class="h-4 w-4" />
            {{ priceCoins }}
          </span>
        </div>

        <div class="flex items-start gap-2.5 rounded-2xl bg-amber-500/10 p-3.5 text-sm text-amber-300">
          <PhInfo :size="18" weight="bold" class="mt-0.5 shrink-0" />
          <p>
            You'll keep {{ palName }}'s subscriber perks until {{ accessUntil }}. You won't be charged again after
            that.
          </p>
        </div>

        <div class="grid grid-cols-2 gap-3 border-t border-white/10 pt-4">
          <UButton color="neutral" variant="soft" size="lg" block class="rounded-full" @click="open = false">
            Keep subscription
          </UButton>
          <UButton color="error" size="lg" block class="rounded-full" @click="confirm">
            Cancel subscription
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
