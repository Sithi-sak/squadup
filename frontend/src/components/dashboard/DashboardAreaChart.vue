<script setup lang="ts">
import { computed } from 'vue'
import { AreaChart, CurveType } from 'vue-chrts'

const props = withDefaults(
  defineProps<{
    points: { label: string; value: number }[]
    /** Chart height in px; Unovis needs a fixed number rather than filling its parent. */
    height?: number
    /** Series name shown in the hover tooltip, e.g. "Coins". */
    name?: string
    /** Label only every Nth point, counted back from the last so the current period always keeps
     * its label; for dense series (e.g. 30 days) whose labels would otherwise collide. */
    labelEvery?: number
  }>(),
  { height: 192, name: 'Value', labelEvery: 1 },
)

type Row = { label: string; value: number }

const data = computed<Row[]>(() => props.points.map((p) => ({ label: p.label, value: p.value })))

// brand-500 as a literal: the area gradient is written into SVG `stop-color` attributes, where
// CSS variables don't resolve.
const categories = computed(() => ({ value: { name: props.name, color: 'hsl(160 84% 46%)' } }))

const xTicks = computed(() =>
  props.points
    .map((_, i) => i)
    .filter((i) => (props.points.length - 1 - i) % props.labelEvery === 0),
)

// An all-zero series would otherwise collapse the y-domain to [0, 0].
const yDomain = computed<[number, number | undefined]>(() => [
  0,
  props.points.some((p) => p.value > 0) ? undefined : 1,
])

const xFormatter = (tick: number | Date) => props.points[Number(tick)]?.label ?? ''
const yFormatter = (tick: number | Date) => Number(tick).toLocaleString()
</script>

<template>
  <AreaChart
    :data="data"
    :height="height"
    :categories="categories"
    :x-formatter="xFormatter"
    :y-formatter="yFormatter"
    :x-explicit-ticks="xTicks"
    :y-num-ticks="4"
    :y-domain="yDomain"
    :curve-type="CurveType.MonotoneX"
    :gradient-stops="[
      { offset: '0%', stopOpacity: 0.35 },
      { offset: '100%', stopOpacity: 0 },
    ]"
    :crosshair-config="{ color: 'hsl(160 84% 46%)', strokeColor: 'rgb(255 255 255 / 0.2)' }"
    :tooltip-title-formatter="(d: Row) => d.label"
    hide-legend
    y-grid-line
  />
</template>
