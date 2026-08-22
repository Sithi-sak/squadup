<script setup lang="ts">
import { PhProhibit } from '@phosphor-icons/vue'
import ConfirmModal from './ConfirmModal.vue'

const props = defineProps<{ handle: string }>()

const open = defineModel<boolean>('open', { required: true })

defineEmits<{ confirm: [] }>()
</script>

<template>
  <ConfirmModal
    v-model:open="open"
    :icon="PhProhibit"
    :title="`Block ${props.handle}?`"
    description="They can't message, book, or view your profile. You can unblock them anytime from settings."
    cancel-label="Cancel"
    confirm-label="Block"
    destructive
    @confirm="$emit('confirm')"
  />
</template>
