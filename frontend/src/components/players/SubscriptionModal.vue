<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhCheck, PhStar, PhUserCircle } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { mockCurrentUser } from '@/mocks/users'

const props = withDefaults(
  defineProps<{
    palName: string
    tagline: string
    rating: number | null
    subscriberCount: number
    monthlyPriceCoins?: number
  }>(),
  { monthlyPriceCoins: 990 },
)

const open = defineModel<boolean>('open', { required: true })

const emit = defineEmits<{ subscribe: [plan: 'monthly' | 'quarterly'] }>()

const perks = [
  '20% off every service, always',
  'Priority booking & instant accept',
  'Exclusive subscriber-only posts & clips',
  'Subscriber badge on your profile',
  '100 bonus Squad Coin each month',
]

const plan = ref<'monthly' | 'quarterly'>('monthly')

const quarterlyPriceCoins = computed(() => Math.round(props.monthlyPriceCoins * 3 * 0.9))

const dueTodayCoins = computed(() =>
  plan.value === 'monthly' ? props.monthlyPriceCoins : quarterlyPriceCoins.value,
)

const renewalCaption = computed(() =>
  plan.value === 'monthly'
    ? 'Renews monthly. Cancel anytime from Settings.'
    : 'Renews quarterly. Cancel anytime from Settings.',
)

function formatSubscriberCount(count: number) {
  if (count >= 1000) return `${(count / 1000).toFixed(1).replace(/\.0$/, '')}k`
  return `${count}`
}

function confirmSubscribe() {
  emit('subscribe', plan.value)
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="`Subscribe to ${palName}`"
    :ui="{ content: 'max-w-lg rounded-3xl' }"
  >
    <template #body>
      <div class="flex flex-col gap-5">
        <div class="flex items-center gap-3">
          <UAvatar size="lg" class="bg-white/10 text-slate-300 ring-2 ring-brand-500">
            <PhUserCircle :size="28" />
          </UAvatar>
          <div class="min-w-0">
            <p class="flex items-center gap-1.5 truncate font-semibold text-white">
              {{ palName }}
              <span class="inline-flex items-center gap-1 text-sm font-medium text-amber-400">
                <PhStar :size="14" weight="fill" />
                {{ rating ? rating.toFixed(1) : '--' }}
              </span>
            </p>
            <p class="truncate text-sm text-slate-400">
              {{ tagline }} · {{ formatSubscriberCount(subscriberCount) }} subscribers
            </p>
          </div>
        </div>

        <div class="rounded-2xl bg-gray-800/70 p-4">
          <p class="font-semibold text-white">Subscriber perks</p>
          <ul class="mt-3 flex flex-col gap-3">
            <li v-for="perk in perks" :key="perk" class="flex items-center gap-3 text-sm text-slate-200">
              <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600">
                <PhCheck :size="12" weight="bold" class="text-white" />
              </span>
              {{ perk }}
            </li>
          </ul>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <button
            type="button"
            class="rounded-2xl px-4 py-3 text-left ring-1 ring-inset transition-colors"
            :class="
              plan === 'monthly'
                ? 'bg-brand-900/30 ring-brand-500'
                : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
            "
            @click="plan = 'monthly'"
          >
            <p class="text-sm font-medium text-slate-300">Monthly</p>
            <p class="mt-1 inline-flex items-center gap-1.5 text-xl font-bold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ monthlyPriceCoins.toLocaleString() }}
            </p>
            <p class="mt-1 text-xs text-slate-400">per month</p>
          </button>
          <button
            type="button"
            class="rounded-2xl px-4 py-3 text-left ring-1 ring-inset transition-colors"
            :class="
              plan === 'quarterly'
                ? 'bg-brand-900/30 ring-brand-500'
                : 'bg-gray-800/70 ring-transparent hover:ring-gray-700'
            "
            @click="plan = 'quarterly'"
          >
            <p class="text-sm font-medium text-slate-300">Quarterly</p>
            <p class="mt-1 inline-flex items-center gap-1.5 text-xl font-bold text-white">
              <img :src="coinIcon" alt="" class="h-4 w-4" />
              {{ quarterlyPriceCoins.toLocaleString() }}
            </p>
            <p class="mt-1 text-xs text-slate-400">save 10% · /3 mo</p>
          </button>
        </div>

        <div class="flex items-center justify-between rounded-2xl bg-gray-800/70 p-4">
          <div class="flex items-center gap-3">
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10">
              <img :src="coinIcon" alt="" class="h-5 w-5" />
            </span>
            <div>
              <p class="text-sm font-semibold text-white">Squad Coin Wallet</p>
              <p class="text-xs text-slate-400">Balance {{ mockCurrentUser.coinBalance.toLocaleString() }} SC</p>
            </div>
          </div>
          <UButton color="primary" variant="link" size="sm">Change</UButton>
        </div>

        <div class="flex flex-col gap-3 border-t border-white/10 pt-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-slate-400">Due today</p>
              <p class="inline-flex items-center gap-1.5 text-xl font-bold text-white">
                <img :src="coinIcon" alt="" class="h-4 w-4" />
                {{ dueTodayCoins.toLocaleString() }}
              </p>
            </div>
            <UButton color="primary" size="lg" class="rounded-full px-8" @click="confirmSubscribe">
              Subscribe
            </UButton>
          </div>
          <p class="text-center text-xs text-slate-500">{{ renewalCaption }}</p>
        </div>
      </div>
    </template>
  </UModal>
</template>
