<script setup lang="ts">
defineProps<{
  /** `badge` is optional and only rendered when > 0 - the Admin panel uses it for the number
   * of unread alerts sitting in each queue (4.54). */
  tabs: { key: string; label: string; badge?: number }[]
  active: string
}>()
defineEmits<{ 'update:active': [string] }>()
</script>

<template>
  <nav class="flex flex-col gap-1">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      class="cursor-pointer rounded-full px-4 py-2.5 text-left text-sm transition-colors"
      :class="
        active === tab.key
          ? 'bg-brand-600/15 font-medium text-brand-400'
          : 'text-slate-300 hover:bg-white/5 hover:text-white'
      "
      @click="$emit('update:active', tab.key)"
    >
      <span class="flex items-center justify-between gap-2">
        {{ tab.label }}
        <span
          v-if="tab.badge"
          class="flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-500 px-1.5 text-[11px] font-semibold text-white"
        >
          {{ tab.badge }}
        </span>
      </span>
    </button>
  </nav>
</template>
