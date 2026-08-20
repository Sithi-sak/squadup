<script setup lang="ts">
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    icon: Component
    title: string
    description: string
    cancelLabel?: string
    confirmLabel: string
    /** Right-hand button reads as a destructive action (red) instead of the default brand green. */
    destructive?: boolean
  }>(),
  { cancelLabel: 'Cancel', destructive: false },
)

const open = defineModel<boolean>('open', { required: true })

defineEmits<{ confirm: [] }>()
</script>

<template>
  <UModal v-model:open="open" :close="false" :ui="{ content: 'max-w-md rounded-3xl' }">
    <template #body>
      <div class="flex flex-col items-center gap-5 px-2 py-2 text-center">
        <div class="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-brand-600">
          <component :is="icon" :size="36" weight="bold" class="text-brand-200" />
        </div>

        <div class="flex flex-col gap-2">
          <h2 class="text-xl font-bold text-white">{{ title }}</h2>
          <p class="text-slate-400">{{ description }}</p>
        </div>

        <div class="mt-2 grid w-full grid-cols-2 gap-3">
          <UButton color="neutral" variant="soft" size="lg" block class="rounded-full" @click="open = false">
            {{ cancelLabel }}
          </UButton>
          <UButton
            :color="destructive ? 'error' : 'primary'"
            size="lg"
            block
            class="rounded-full"
            @click="$emit('confirm')"
          >
            {{ confirmLabel }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
