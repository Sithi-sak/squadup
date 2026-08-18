<script setup lang="ts">
import { PhCopy, PhDotsThree, PhPlus, PhUserCircle } from '@phosphor-icons/vue'
import type { PlayerProfile, PlayerSummary } from '@/stores/players'

defineProps<{ player: PlayerSummary; profile: PlayerProfile }>()

function copyLink() {
  navigator.clipboard?.writeText(window.location.href)
}
</script>

<template>
  <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
    <div class="flex items-start gap-4">
      <div class="relative shrink-0">
        <UAvatar size="3xl" class="bg-white/10 text-slate-300">
          <PhUserCircle :size="40" />
        </UAvatar>
        <span
          v-if="player.online"
          class="absolute right-1 bottom-1 h-3 w-3 rounded-full bg-brand-400 ring-2 ring-squadup-bg"
        />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-white">{{ player.displayName }}</h1>
        <p class="mt-1 text-sm text-slate-400">
          {{ profile.handle }} · {{ profile.timezone }} · {{ profile.language }}
        </p>
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <UBadge v-if="player.online" color="primary" variant="primary" size="sm" class="rounded-full text-xs">
            <span class="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-brand-400" />
            Online
          </UBadge>
          <UBadge color="neutral" variant="soft" size="sm" class="rounded-full text-xs">{{ profile.tier }}</UBadge>
          <UBadge
            v-if="profile.highlightBadge"
            color="neutral"
            variant="soft"
            size="sm"
            class="rounded-full text-amber-400 text-xs"
          >
            {{ profile.highlightBadge }}
          </UBadge>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <UButton
        color="neutral"
        variant="soft"
        square
        :ui="{ base: 'rounded-full' }"
        aria-label="More options"
      >
        <PhDotsThree :size="18" weight="bold" />
      </UButton>
      <UButton
        color="neutral"
        variant="soft"
        square
        :ui="{ base: 'rounded-full' }"
        aria-label="Copy profile link"
        @click="copyLink"
      >
        <PhCopy :size="18" weight="bold" />
      </UButton>
      <UButton
        color="neutral"
        variant="soft"
        square
        :ui="{ base: 'rounded-full' }"
        aria-label="Add to favorites"
      >
        <PhPlus :size="18" weight="bold" />
      </UButton>
      <UButton v-if="profile.subscribeLabel" color="primary" variant="outline" class="rounded-full">
        {{ profile.subscribeLabel }}
      </UButton>
    </div>
  </div>
</template>
