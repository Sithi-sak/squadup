<script setup lang="ts">
defineProps<{
  tabs: { key: string; label: string }[]
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
      {{ tab.label }}
    </button>
  </nav>
</template>
