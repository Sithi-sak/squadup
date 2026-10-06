<script setup lang="ts">
import { PhMedal } from '@phosphor-icons/vue'

/** The rank a service is offered at (4.68), on My Services, the profile services sidebar/tab,
 * Service Detail and the Create/Edit Service preview. */
withDefaults(defineProps<{ rank: string; size?: 'sm' | 'md' }>(), { size: 'md' })
</script>

<template>
  <UBadge color="neutral" variant="soft" :size="size" class="shrink-0 gap-1 rounded-full">
    <PhMedal :size="size === 'sm' ? 10 : 12" weight="fill" class="text-amber-400" />
    {{ rank }}
  </UBadge>
</template>
