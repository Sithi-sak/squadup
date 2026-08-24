<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhEye, PhHeart, PhImage, PhShareFat, PhVideoCamera } from '@phosphor-icons/vue'
import type { AlbumItem } from '@/stores/players'

const props = defineProps<{ album: AlbumItem[] }>()

type AlbumFilter = 'all' | 'clip' | 'screenshot'
const filter = ref<AlbumFilter>('all')

const visible = computed(() => {
  if (filter.value === 'all') return props.album
  return props.album.filter((item) => item.kind === filter.value)
})

function formatCount(count: number) {
  if (count < 1000) return String(count)
  const thousands = count / 1000
  return `${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`
}

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-bold text-white">Album · {{ album.length }} highlights</h2>
      <div class="flex items-center gap-2">
        <UButton
          :color="filter === 'all' ? 'primary' : 'neutral'"
          :variant="filter === 'all' ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="filter = 'all'"
        >
          All
        </UButton>
        <UButton
          :color="filter === 'clip' ? 'primary' : 'neutral'"
          :variant="filter === 'clip' ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="filter = 'clip'"
        >
          Clips
        </UButton>
        <UButton
          :color="filter === 'screenshot' ? 'primary' : 'neutral'"
          :variant="filter === 'screenshot' ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="filter = 'screenshot'"
        >
          Screens
        </UButton>
      </div>
    </div>

    <p v-if="visible.length === 0" class="py-10 text-center text-sm text-slate-400">No highlights yet.</p>

    <div v-else class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
      <div
        v-for="item in visible"
        :key="item.id"
        class="relative flex aspect-video flex-col justify-between overflow-hidden rounded-xl bg-white/5 p-3"
      >
        <div class="flex items-center justify-between gap-2 text-xs text-slate-300">
          <span class="flex items-center gap-1">
            <PhEye :size="13" weight="fill" />
            {{ formatCount(item.views) }}
          </span>
          <span class="flex items-center gap-1">
            <PhHeart :size="13" weight="fill" />
            {{ formatCount(item.likes) }}
          </span>
          <span class="flex items-center gap-1">
            <PhShareFat :size="13" weight="fill" />
            {{ formatCount(item.shares) }}
          </span>
        </div>

        <component
          :is="item.kind === 'clip' ? PhVideoCamera : PhImage"
          :size="28"
          class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-slate-500"
        />

        <div class="flex items-end justify-between gap-2">
          <span class="text-sm font-medium text-white">
            {{ item.label ?? (item.kind === 'clip' ? 'Clip' : 'Screenshot') }}
          </span>
          <span v-if="item.durationSeconds" class="text-xs text-slate-300">
            {{ formatDuration(item.durationSeconds) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
