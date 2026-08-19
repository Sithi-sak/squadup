<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  bars: { label: string; value: number }[]
  /** Index of the bar to highlight in brand green; defaults to the last bar (the current period). */
  highlightIndex?: number
}>()

const highlighted = computed(() => props.highlightIndex ?? props.bars.length - 1)
const max = computed(() => Math.max(...props.bars.map((b) => b.value), 1))
</script>

<template>
  <div class="flex h-full items-end gap-3">
    <div v-for="(bar, index) in bars" :key="`${bar.label}-${index}`" class="flex flex-1 flex-col items-center gap-2">
      <div class="flex h-full w-full items-end">
        <div
          class="w-full rounded-full transition-all"
          :class="index === highlighted ? 'bg-brand-500' : 'bg-white/10'"
          :style="{ height: `${Math.max((bar.value / max) * 100, 4)}%` }"
        />
      </div>
      <span class="text-xs text-slate-400">{{ bar.label }}</span>
    </div>
  </div>
</template>
