<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value?: string
    actionLabel: string
    danger?: boolean
    disabled?: boolean
  }>(),
  { danger: false, disabled: true },
)
defineEmits<{ action: [] }>()
</script>

<template>
  <div class="flex items-center justify-between gap-4 py-4">
    <div class="min-w-0">
      <p class="text-sm text-slate-400">{{ label }}</p>
      <p v-if="value" class="font-medium text-white">{{ value }}</p>
    </div>
    <UButton
      color="neutral"
      variant="soft"
      size="sm"
      class="shrink-0 rounded-full text-xs"
      :class="danger && 'text-red-400'"
      :disabled="disabled"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </UButton>
  </div>
</template>
