<script setup lang="ts">
import { useRouter } from 'vue-router'
import coinIcon from '@/assets/squadup-coin.svg'
import EmptyState from '@/components/common/EmptyState.vue'
import { mockCurrentUser } from '@/mocks/users'

const router = useRouter()
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 py-14 md:px-6">
    <div v-if="mockCurrentUser.coinBalance === 0" class="flex min-h-[60vh] items-center justify-center">
      <EmptyState
        tone="gold"
        badge="0 SC"
        title="Your wallet is empty"
        description="Top up Squad Coin to book Pals, tip, and send gifts. $10 = 990 SC."
      >
        <template #icon>
          <img :src="coinIcon" alt="" class="h-9 w-9" />
        </template>
        <template #actions>
          <UButton color="primary" class="rounded-full px-6">Top up now</UButton>
          <UButton color="neutral" variant="soft" class="rounded-full px-6" @click="router.push('/settings')">
            How it works
          </UButton>
        </template>
      </EmptyState>
    </div>

    <div v-else class="mx-auto max-w-md">
      <h1 class="text-2xl font-bold text-white">Wallet</h1>
      <div class="mt-5 flex flex-col items-center gap-4 rounded-xl bg-gray-800/70 p-8 text-center">
        <img :src="coinIcon" alt="" class="h-12 w-12" />
        <div>
          <p class="text-3xl font-bold text-white">{{ mockCurrentUser.coinBalance.toLocaleString() }} SC</p>
          <p class="mt-1 text-sm text-slate-400">Squad Coin balance</p>
        </div>
        <UButton color="primary" class="rounded-full px-6">Top up now</UButton>
      </div>
    </div>
  </div>
</template>
