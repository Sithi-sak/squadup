<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhCheck } from '@phosphor-icons/vue'

defineProps<{ displayName: string; email: string }>()

const router = useRouter()

type TimelineState = 'done' | 'active' | 'pending'

const timelineItems: { label: string; status: string; state: TimelineState }[] = [
  { label: 'Application received', status: 'Just now', state: 'done' },
  { label: 'Under review by our team', status: 'In progress', state: 'active' },
  { label: 'Your Pal profile goes live', status: 'Pending', state: 'pending' },
]
</script>

<template>
  <div class="mx-auto flex max-w-xl flex-col items-center py-16 text-center">
    <div class="flex size-24 items-center justify-center rounded-full bg-brand-600/10">
      <div class="flex size-16 items-center justify-center rounded-full bg-brand-600">
        <PhCheck :size="32" weight="bold" class="text-white" />
      </div>
    </div>

    <h1 class="mt-8 text-3xl font-semibold text-white">You're all set, {{ displayName || 'Pal' }}!</h1>
    <p class="mt-3 text-slate-400">
      Your Pal application has been submitted. Our team reviews every application to keep SquadUp
      safe — most are approved within 24–48 hours.
    </p>

    <div class="mt-8 flex w-full flex-col gap-4 rounded-3xl bg-gray-900/60 px-6 py-5 text-left">
      <div v-for="item in timelineItems" :key="item.label" class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <span
            v-if="item.state === 'done'"
            class="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-600"
          >
            <PhCheck :size="14" weight="bold" class="text-white" />
          </span>
          <span
            v-else
            class="flex size-6 shrink-0 items-center justify-center rounded-full border-2"
            :class="item.state === 'active' ? 'border-brand-600' : 'border-gray-700'"
          >
            <span
              class="size-2 rounded-full"
              :class="item.state === 'active' ? 'bg-brand-400' : 'bg-gray-600'"
            />
          </span>
          <span class="text-sm font-medium text-white">{{ item.label }}</span>
        </div>
        <span
          class="text-sm"
          :class="item.state === 'active' ? 'font-medium text-brand-300' : 'text-slate-500'"
        >
          {{ item.status }}
        </span>
      </div>
    </div>

    <p class="mt-6 text-sm text-slate-400">
      We'll email {{ email }} and send an in-app notification the moment you're approved.
    </p>

    <UButton
      color="primary"
      class="mt-6 rounded-full px-8 py-2 text-base"
      @click="router.push('/dashboard/player')"
    >
      Go to Dashboard
    </UButton>
  </div>
</template>
