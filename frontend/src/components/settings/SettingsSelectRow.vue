<script setup lang="ts">
defineProps<{
  label: string
  description?: string
  items: string[]
  modelValue: string
}>()
defineEmits<{ 'update:modelValue': [string] }>()

const selectUi = { base: 'rounded-full bg-white/5 px-3.5 py-1.5 text-sm ring-white/10 hover:bg-white/10' }
</script>

<template>
  <div class="flex items-center justify-between gap-4 py-4">
    <div class="min-w-0">
      <p class="font-medium text-white">{{ label }}</p>
      <p v-if="description" class="text-sm text-slate-400">{{ description }}</p>
    </div>
    <USelect
      :model-value="modelValue"
      :items="items"
      variant="soft"
      size="md"
      class="w-auto shrink-0"
      :ui="selectUi"
      @update:model-value="$emit('update:modelValue', $event as string)"
    />
  </div>
</template>
