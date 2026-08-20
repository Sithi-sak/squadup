<script setup lang="ts">
import { PhTrash } from '@phosphor-icons/vue'
import ConfirmModal from './ConfirmModal.vue'

const open = defineModel<boolean>('open', { required: true })

defineEmits<{ confirm: [] }>()
</script>

<template>
  <ConfirmModal
    v-model:open="open"
    :icon="PhTrash"
    title="Delete your account?"
    description="This permanently removes your profile, orders and Squad Coin balance. This can't be undone."
    cancel-label="Keep account"
    confirm-label="Delete"
    destructive
    @confirm="$emit('confirm')"
  />
</template>
