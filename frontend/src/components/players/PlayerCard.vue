<script setup lang="ts">
import { PhPlay, PhStar, PhUserCircle } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import type { PlayerSummary } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

defineProps<{ player: PlayerSummary }>()

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}
</script>

<template>
  <router-link
    :to="`/players/${player.id}`"
    class="relative isolate flex flex-col gap-2.5 overflow-hidden rounded-xl bg-gray-800/70 p-4 transition duration-200 ease-out hover:-translate-y-1 hover:shadow-lg hover:shadow-black/30"
  >
    <div class="absolute inset-0 -z-10">
      <img
        :src="resolveAvatarUrl(player.id, player.avatarUrl)"
        alt=""
        class="h-full w-full scale-110 object-cover object-top saturate-50 brightness-90"
      />
      <div class="absolute inset-0 bg-linear-to-b from-transparent via-gray-800/80 via-55% to-gray-800" />
      <div class="absolute inset-0 bg-gray-800/70" />
    </div>

    <div class="flex items-start justify-between">
      <div class="relative shrink-0">
        <UAvatar :src="resolveAvatarUrl(player.id, player.avatarUrl)" size="3xl" class="bg-white/10 text-slate-300 size-20">
          <PhUserCircle :size="26" />
        </UAvatar>
        <span
          v-if="player.online"
          class="absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-brand-400 ring-2 ring-gray-800"
        />
      </div>
    </div>

    <span class="truncate font-semibold text-white">{{ player.displayName }}</span>

    <p class="inline-flex items-center gap-1 text-xs text-slate-400">
      <PhStar :size="12" weight="fill" class="text-amber-400" />
      <template v-if="player.rating">
        {{ player.rating.toFixed(1) }}
        <span v-if="player.reviewCount">({{ formatCount(player.reviewCount) }})</span>
      </template>
      <span v-else>--</span>
    </p>

    <div v-if="player.rank || player.role" class="flex flex-wrap gap-1.5">
      <UBadge v-if="player.rank" color="neutral" variant="soft" size="md" class="rounded-full">
        {{ player.rank }}
      </UBadge>
      <UBadge v-if="player.role" color="neutral" variant="soft" size="md" class="rounded-full">
        {{ player.role }}
      </UBadge>
    </div>

    <p v-if="player.tagline" class="line-clamp-2 text-sm text-slate-400">{{ player.tagline }}</p>

    <UBadge
      v-if="player.promoBadge"
      color="primary"
      variant="solid"
      size="lg"
      class="mt-auto w-fit rounded-full"
    >
      {{ player.promoBadge }}
    </UBadge>

    <span v-if="player.priceCoins" class="inline-flex items-center gap-2 text-sm font-semibold text-white">
      <img :src="coinIcon" alt="" class="h-5 w-5" />
      {{ player.priceCoins }}/Game
    </span>
  </router-link>
</template>
