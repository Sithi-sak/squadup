<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  PhArrowsOutSimple,
  PhMagnifyingGlassMinus,
  PhMagnifyingGlassPlus,
} from '@phosphor-icons/vue'

/** Dependency-free image cropper: the image is drawn at a scale that always covers the frame, so
 * panning and zooming can never expose empty edges. `apply` hands back a Blob cropped from the
 * source pixels (not from the on-screen preview) so quality follows the original upload. */
const props = withDefaults(
  defineProps<{
    src: string
    /** Output mime type, kept from the source file when it is a type canvas can encode. */
    type?: string
    /** Longest edge of the exported image, in pixels. */
    maxOutput?: number
  }>(),
  { type: 'image/jpeg', maxOutput: 1600 },
)

const emit = defineEmits<{ cancel: []; apply: [Blob]; error: [string] }>()

const aspectOptions = [
  { label: 'Wide', value: 16 / 9 },
  { label: 'Square', value: 1 },
] as const

const aspect = ref<number>(aspectOptions[0].value)
const zoom = ref(1)
const offset = ref({ x: 0, y: 0 })
const natural = ref({ w: 0, h: 0 })
const frame = ref({ w: 0, h: 0 })
const exporting = ref(false)

const frameEl = ref<HTMLElement | null>(null)
const imageEl = ref<HTMLImageElement | null>(null)

/** Scale at which the source exactly covers the frame; zoom multiplies it. */
const baseScale = computed(() => {
  if (!natural.value.w || !frame.value.w) return 1
  return Math.max(frame.value.w / natural.value.w, frame.value.h / natural.value.h)
})
const scale = computed(() => baseScale.value * zoom.value)
const drawn = computed(() => ({
  w: natural.value.w * scale.value,
  h: natural.value.h * scale.value,
}))

const ready = computed(() => natural.value.w > 0 && frame.value.w > 0)

function clampOffset() {
  const minX = Math.min(0, frame.value.w - drawn.value.w)
  const minY = Math.min(0, frame.value.h - drawn.value.h)
  offset.value = {
    x: Math.min(0, Math.max(minX, offset.value.x)),
    y: Math.min(0, Math.max(minY, offset.value.y)),
  }
}

function center() {
  offset.value = { x: (frame.value.w - drawn.value.w) / 2, y: (frame.value.h - drawn.value.h) / 2 }
  clampOffset()
}

function reset() {
  zoom.value = 1
  center()
}

/** Zooms while keeping the point under (anchorX, anchorY) fixed in the frame. */
function zoomTo(next: number, anchorX = frame.value.w / 2, anchorY = frame.value.h / 2) {
  const clamped = Math.min(4, Math.max(1, next))
  if (clamped === zoom.value || !ready.value) return
  const ratio = clamped / zoom.value
  offset.value = {
    x: anchorX - (anchorX - offset.value.x) * ratio,
    y: anchorY - (anchorY - offset.value.y) * ratio,
  }
  zoom.value = clamped
  clampOffset()
}

function onImageLoad(event: Event) {
  const img = event.target as HTMLImageElement
  natural.value = { w: img.naturalWidth, h: img.naturalHeight }
  reset()
}

let observer: ResizeObserver | null = null
watch(frameEl, (el) => {
  observer?.disconnect()
  observer = null
  if (!el) return
  observer = new ResizeObserver(([entry]) => {
    if (!entry) return
    frame.value = { w: entry.contentRect.width, h: entry.contentRect.height }
    clampOffset()
  })
  observer.observe(el)
})
onBeforeUnmount(() => observer?.disconnect())

watch(aspect, () => reset())
watch(
  () => props.src,
  () => reset(),
)

let dragging: { pointerId: number; x: number; y: number } | null = null

function onPointerDown(event: PointerEvent) {
  if (!ready.value) return
  dragging = { pointerId: event.pointerId, x: event.clientX, y: event.clientY }
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent) {
  if (!dragging || dragging.pointerId !== event.pointerId) return
  offset.value = {
    x: offset.value.x + (event.clientX - dragging.x),
    y: offset.value.y + (event.clientY - dragging.y),
  }
  dragging.x = event.clientX
  dragging.y = event.clientY
  clampOffset()
}

function onPointerUp(event: PointerEvent) {
  if (dragging?.pointerId !== event.pointerId) return
  ;(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId)
  dragging = null
}

function onWheel(event: WheelEvent) {
  if (!frameEl.value) return
  const rect = frameEl.value.getBoundingClientRect()
  zoomTo(
    zoom.value * (event.deltaY < 0 ? 1.1 : 1 / 1.1),
    event.clientX - rect.left,
    event.clientY - rect.top,
  )
}

function nudge(dx: number, dy: number) {
  offset.value = { x: offset.value.x + dx, y: offset.value.y + dy }
  clampOffset()
}

function onKeydown(event: KeyboardEvent) {
  const step = event.shiftKey ? 32 : 8
  const moves: Record<string, [number, number]> = {
    ArrowLeft: [step, 0],
    ArrowRight: [-step, 0],
    ArrowUp: [0, step],
    ArrowDown: [0, -step],
  }
  const move = moves[event.key]
  if (move) {
    event.preventDefault()
    nudge(move[0], move[1])
    return
  }
  if (event.key === '+' || event.key === '=') {
    event.preventDefault()
    zoomTo(zoom.value * 1.1)
  } else if (event.key === '-' || event.key === '_') {
    event.preventDefault()
    zoomTo(zoom.value / 1.1)
  }
}

const outputType = computed(() =>
  ['image/png', 'image/webp', 'image/jpeg'].includes(props.type) ? props.type : 'image/jpeg',
)

async function apply() {
  const img = imageEl.value
  if (!img || !ready.value || exporting.value) return
  exporting.value = true
  try {
    // Map the visible frame back onto source pixels.
    const sourceW = frame.value.w / scale.value
    const sourceH = frame.value.h / scale.value
    const sx = -offset.value.x / scale.value
    const sy = -offset.value.y / scale.value

    const outputScale = Math.min(1, props.maxOutput / Math.max(sourceW, sourceH))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(sourceW * outputScale))
    canvas.height = Math.max(1, Math.round(sourceH * outputScale))

    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas is unavailable')
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(img, sx, sy, sourceW, sourceH, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, outputType.value, 0.92),
    )
    if (!blob) throw new Error('Could not read the cropped image')
    emit('apply', blob)
  } catch (err) {
    // A remote source (an image already on the post) taints the canvas unless the host allows
    // cross-origin reads, and `toBlob` throws rather than returning null - surface it instead of
    // leaving the button looking dead.
    emit('error', err instanceof Error ? err.message : 'Please try again.')
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div
      ref="frameEl"
      class="relative w-full touch-none overflow-hidden rounded-2xl bg-black/60 ring-1 ring-inset ring-white/10"
      :style="{ aspectRatio: String(aspect) }"
      role="application"
      aria-label="Drag to reposition, scroll or use the slider to zoom"
      tabindex="0"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
      @wheel.prevent="onWheel"
      @keydown="onKeydown"
    >
      <img
        ref="imageEl"
        :src="src"
        alt=""
        crossorigin="anonymous"
        draggable="false"
        class="absolute top-0 left-0 max-w-none origin-top-left cursor-grab select-none active:cursor-grabbing"
        :style="{
          width: `${natural.w}px`,
          height: `${natural.h}px`,
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
        }"
        @load="onImageLoad"
      />
      <div class="pointer-events-none absolute inset-0 grid grid-cols-3 grid-rows-3">
        <div v-for="cell in 9" :key="cell" class="border border-white/10" />
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="option in aspectOptions"
        :key="option.label"
        type="button"
        class="rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors"
        :class="
          aspect === option.value
            ? 'bg-brand-600 text-white'
            : 'bg-gray-800/70 text-slate-300 hover:bg-gray-800'
        "
        @click="aspect = option.value"
      >
        {{ option.label }}
      </button>
      <UButton
        color="neutral"
        variant="ghost"
        size="xs"
        class="ml-auto rounded-full"
        aria-label="Reset crop"
        @click="reset"
      >
        <PhArrowsOutSimple :size="14" />
        Reset
      </UButton>
    </div>

    <div class="flex items-center gap-3">
      <PhMagnifyingGlassMinus :size="16" class="shrink-0 text-slate-400" />
      <input
        :value="zoom"
        type="range"
        min="1"
        max="4"
        step="0.01"
        class="accent-brand-500 h-1 w-full cursor-pointer appearance-none rounded-full bg-gray-700"
        aria-label="Zoom"
        @input="zoomTo(Number(($event.target as HTMLInputElement).value))"
      />
      <PhMagnifyingGlassPlus :size="16" class="shrink-0 text-slate-400" />
    </div>

    <div class="flex items-center justify-between gap-3 border-t border-white/10 pt-4">
      <p class="text-xs text-slate-400">Drag to reposition, scroll or drag the slider to zoom.</p>
      <div class="flex items-center gap-3">
        <UButton color="neutral" variant="soft" class="rounded-full" @click="emit('cancel')"
          >Cancel</UButton
        >
        <UButton
          color="primary"
          class="rounded-full"
          :loading="exporting"
          :disabled="!ready"
          @click="apply"
        >
          Apply crop
        </UButton>
      </div>
    </div>
  </div>
</template>
