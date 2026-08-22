<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhChatCircleDots, PhClockAfternoon, PhCurrencyDollar, PhGameController } from '@phosphor-icons/vue'

const router = useRouter()

const perks = [
  { icon: PhCurrencyDollar, label: 'Set your own rates', description: 'Price every service the way you want, per game or per hour.' },
  { icon: PhClockAfternoon, label: 'Play on your schedule', description: 'Go online whenever you have time, pause anytime.' },
  { icon: PhChatCircleDots, label: 'Chat before you play', description: 'Buyers message you first, no surprises when a session starts.' },
]
</script>

<template>
  <div class="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-10 md:px-6">
    <div class="w-full max-w-2xl rounded-2xl bg-linear-to-br from-brand-900/50 to-squadup-bg p-8 text-center ring-1 ring-inset ring-white/10 md:p-12">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300 ring-1 ring-inset ring-brand-700">
        <PhGameController :size="14" weight="fill" />
        Become a Pal
      </span>
      <h1 class="mt-4 text-2xl font-extrabold text-white md:text-3xl">Turn your game time into Squad Coin</h1>
      <p class="mx-auto mt-3 max-w-md text-sm leading-relaxed text-slate-300">
        You don't have a Pal profile yet. Set up services, get discovered by buyers, and earn Squad
        Coin doing what you already love.
      </p>
      <UButton color="primary" size="lg" class="mt-6 rounded-full px-6" @click="router.push('/become-a-pal')">
        Become a Pal
      </UButton>

      <div class="mt-10 grid grid-cols-1 gap-4 text-left sm:grid-cols-3">
        <div v-for="perk in perks" :key="perk.label" class="rounded-xl bg-white/5 p-4">
          <component :is="perk.icon" :size="22" class="text-brand-300" />
          <p class="mt-3 text-sm font-semibold text-white">{{ perk.label }}</p>
          <p class="mt-1 text-xs text-slate-400">{{ perk.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
