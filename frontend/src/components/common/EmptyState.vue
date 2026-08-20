<script setup lang="ts">
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    icon?: Component
    tone?: 'brand' | 'gold'
    badge: string
    title: string
    description: string
  }>(),
  { tone: 'brand' },
)
</script>

<template>
  <UEmpty
    :title="title"
    :description="description"
    class="mx-auto max-w-md py-16 text-center"
    :ui="{
      header: 'items-center',
      title: 'text-2xl font-bold text-white',
      description: 'text-slate-400',
      body: 'items-center',
      actions: 'flex-wrap justify-center gap-3',
    }"
  >
    <template #leading>
      <UAvatar
        size="3xl"
        class="mb-4 h-20 w-20 text-white"
        :class="
          tone === 'gold'
            ? 'bg-linear-to-br from-amber-300 to-amber-600'
            : 'bg-linear-to-br from-brand-400 to-brand-700'
        "
      >
        <slot name="icon">
          <component :is="icon" :size="32" weight="fill" />
        </slot>
      </UAvatar>
      <UBadge color="neutral" variant="soft" size="md" class="mb-1 rounded-full">{{ badge }}</UBadge>
    </template>
    <template #actions>
      <slot name="actions" />
    </template>
  </UEmpty>
</template>
