<script setup lang="ts">
defineProps<{
  label: string
  description?: string
  modelValue: boolean
}>()
defineEmits<{ 'update:modelValue': [boolean] }>()
</script>

<template>
  <div class="flex items-center justify-between gap-4 py-4">
    <div class="min-w-0">
      <p class="font-medium text-white">{{ label }}</p>
      <p v-if="description" class="text-sm text-slate-400">{{ description }}</p>
    </div>
    <USwitch
      :model-value="modelValue"
      color="primary"
      class="shrink-0"
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>
