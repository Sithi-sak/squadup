<script setup lang="ts">
import { computed } from 'vue'
import { BarChart } from 'vue-chrts'

const props = withDefaults(
  defineProps<{
    bars: { label: string; value: number }[]
    /** Chart height in px; Unovis needs a fixed number rather than filling its parent. */
    height?: number
    /** Series name shown in the hover tooltip, e.g. "Coins". */
    name?: string
  }>(),
  { height: 128, name: 'Value' },
)

type Row = { label: string; value: number }

const data = computed<Row[]>(() => props.bars.map((b) => ({ label: b.label, value: b.value })))

const categories = computed(() => ({
  value: { name: props.name, color: 'var(--color-brand-500)' },
}))

const xTicks = computed(() => props.bars.map((_, i) => i))

// An all-zero series would otherwise collapse the y-domain to [0, 0].
const yDomain = computed<[number, number | undefined]>(() => [
  0,
  props.bars.some((b) => b.value > 0) ? undefined : 1,
])

const xFormatter = (tick: number | Date) => props.bars[Number(tick)]?.label ?? ''
const yFormatter = (tick: number | Date) => Number(tick).toLocaleString()
</script>

<template>
  <BarChart
    :data="data"
    :height="height"
    :categories="categories"
    :y-axis="['value']"
    :x-formatter="xFormatter"
    :y-formatter="yFormatter"
    :x-explicit-ticks="xTicks"
    :y-num-ticks="4"
    :y-domain="yDomain"
    :bar-padding="0.4"
    :radius="4"
    :tooltip-title-formatter="(d: Row) => d.label"
    hide-legend
    y-grid-line
  />
</template>
