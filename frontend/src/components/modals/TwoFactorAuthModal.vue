<script setup lang="ts">
import { PhLock } from '@phosphor-icons/vue'
import ConfirmModal from './ConfirmModal.vue'

withDefaults(defineProps<{ phone?: string }>(), { phone: '+855 ••• 678' })

const open = defineModel<boolean>('open', { required: true })

defineEmits<{ confirm: [] }>()
</script>

<template>
  <ConfirmModal
    v-model:open="open"
    :icon="PhLock"
    title="Enable two-factor auth?"
    :description="`We'll text a 6-digit code to ${phone} each time you sign in on a new device.`"
    cancel-label="Not now"
    confirm-label="Enable 2FA"
    @confirm="$emit('confirm')"
  />
</template>
