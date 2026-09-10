<script setup lang="ts">
import { PhStar, PhTrophy, PhUserCircle } from '@phosphor-icons/vue'
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
    class="flex flex-col gap-3 rounded-xl bg-gray-800/70 p-4 transition-colors hover:bg-gray-800"
  >
    <div class="flex items-center gap-4">
      <div class="relative shrink-0">
        <UAvatar :src="resolveAvatarUrl(player.id, player.avatarUrl)" size="3xl" class="bg-white/10 text-slate-300">
          <PhUserCircle :size="26" />
        </UAvatar>
        <span
          v-if="player.online"
          class="absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-brand-400 ring-2 ring-gray-800"
        />
      </div>
      <div class="min-w-0">
        <div class="flex items-center gap-1.5">
          <span class="truncate font-semibold text-white">{{ player.displayName }}</span>
          <PhTrophy
            v-if="(player.rating ?? 0) >= 4.8"
            :size="14"
            weight="fill"
            class="shrink-0 text-amber-400"
          />
        </div>
        <p class="inline-flex items-center gap-1 text-xs text-slate-400">
          <template v-if="player.rating">
            <PhStar :size="12" weight="fill" class="text-amber-400" />
            {{ player.rating.toFixed(1) }}
            <span v-if="player.reviewCount">({{ formatCount(player.reviewCount) }})</span>
          </template>
          <span v-else>No reviews yet</span>
        </p>
      </div>
    </div>

    <div class="flex flex-wrap gap-1.5">
      <UBadge v-if="player.rank" color="neutral" variant="soft" size="md" class="rounded-full">
        {{ player.rank }}
      </UBadge>
      <UBadge v-if="player.role" color="neutral" variant="soft" size="md" class="rounded-full">
        {{ player.role }}
      </UBadge>
    </div>

    <p v-if="player.tagline" class="line-clamp-2 text-sm text-slate-400">{{ player.tagline }}</p>

    <div class="mt-auto flex items-center justify-between gap-2 pt-1">
      <UBadge
        v-if="player.promoBadge"
        color="primary"
        variant="solid"
        size="lg"
        class="rounded-full"
      >
        {{ player.promoBadge }}
      </UBadge>
      <span v-else />
      <span v-if="player.priceCoins" class="inline-flex items-center gap-2 text-sm font-semibold text-white">
        <img :src="coinIcon" alt="" class="h-6 w-6" />
        {{ player.priceCoins }}/Game
      </span>
    </div>
  </router-link>
</template>
