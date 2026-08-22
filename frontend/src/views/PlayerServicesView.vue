<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhStar } from '@phosphor-icons/vue'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { mockPlayerProfiles } from '@/mocks/playerProfiles'

const router = useRouter()

const profile = mockPlayerProfiles.self!

/** `ref()` so toggling a service's `active` state re-renders its status badge (plain mock
 * objects aren't reactive on their own). */
const cards = ref(
  profile.services.map((service) => ({
    service: { ...service },
    detail: profile.serviceDetails[service.id]!,
  })),
)
</script>

<template>
  <DashboardLayout active="services">
    <div class="flex h-full flex-col gap-5 overflow-y-auto pr-1">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">My services</h1>
          <p class="mt-1 text-sm text-slate-400">Manage the services buyers can book from you</p>
        </div>
        <UButton color="primary" class="rounded-full" @click="router.push('/dashboard/player/services/new')">
          New Service
        </UButton>
      </div>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <div v-for="{ service, detail } in cards" :key="service.id" class="overflow-hidden rounded-xl bg-gray-800/70">
          <div class="relative aspect-21/9 w-full bg-white/5 ring-1 ring-inset ring-white/10">
            <span
              class="absolute top-3 right-3 inline-flex items-center gap-1.5 rounded-full bg-squadup-dark/70 px-2.5 py-1 text-xs font-medium"
              :class="service.active ? 'text-brand-400' : 'text-slate-400'"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="service.active ? 'bg-brand-400' : 'bg-slate-500'" />
              {{ service.active ? 'Active' : 'Paused' }}
            </span>
          </div>
          <div class="p-5">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-lg font-semibold text-white">{{ service.name }}</h2>
              <USwitch v-model="service.active" color="primary" />
            </div>
            <p class="mt-1 text-sm text-slate-400">{{ detail.description }}</p>
            <div class="mt-4 flex items-center justify-between text-sm">
              <span class="inline-flex items-center gap-1 font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ service.priceCoins }}{{ service.priceUnit }}
              </span>
              <span class="inline-flex items-center gap-1.5 text-slate-400">
                <PhStar :size="14" weight="fill" class="text-amber-400" />
                {{ detail.rating?.toFixed(1) ?? '--' }}
                <span>· {{ detail.servedCount.toLocaleString() }} orders</span>
              </span>
            </div>
            <div class="mt-4 flex items-center gap-2">
              <UButton color="neutral" variant="soft" block class="rounded-full" disabled>Edit</UButton>
              <UButton color="neutral" variant="soft" block class="rounded-full" disabled>View stats</UButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>
