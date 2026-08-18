<script setup lang="ts">
import { PhCaretRight, PhUserCircle } from '@phosphor-icons/vue'
import { mockSuggestedPals, mockTrendingTopics } from '@/mocks/feed'
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-white">Suggested Pals</h3>
        <router-link to="/players" class="text-sm text-brand-400 hover:text-brand-300">See all</router-link>
      </div>
      <div class="mt-4 flex flex-col gap-4">
        <div v-for="pal in mockSuggestedPals" :key="pal.id" class="flex items-center gap-3">
          <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
            <PhUserCircle :size="20" />
          </UAvatar>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-white">{{ pal.name }}</p>
            <p class="truncate text-xs text-slate-400">{{ pal.subtitle }}</p>
          </div>
          <UButton color="primary" size="xs" class="shrink-0 rounded-full">Follow</UButton>
        </div>
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h3 class="font-semibold text-white">Trending now</h3>
      <div class="mt-3 flex flex-col divide-y divide-white/10">
        <button
          v-for="topic in mockTrendingTopics"
          :key="topic.id"
          type="button"
          class="flex items-center justify-between gap-3 py-3 text-left first:pt-0 last:pb-0"
        >
          <div>
            <p class="text-sm text-white">{{ topic.label }}</p>
            <p class="text-xs text-slate-400">{{ topic.postCount }}</p>
          </div>
          <PhCaretRight :size="16" class="shrink-0 text-slate-500" />
        </button>
      </div>
    </div>
  </div>
</template>
