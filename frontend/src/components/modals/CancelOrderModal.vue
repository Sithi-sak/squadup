<script setup lang="ts">
import { PhExclamationMark } from '@phosphor-icons/vue'
import ConfirmModal from './ConfirmModal.vue'

defineProps<{ palName: string; refundCoins: number }>()

const open = defineModel<boolean>('open', { required: true })

defineEmits<{ confirm: [] }>()
</script>

<template>
  <ConfirmModal
    v-model:open="open"
    :icon="PhExclamationMark"
    title="Cancel this order?"
    :description="`Your order with ${palName} will be cancelled and ${refundCoins} SC refunded to your wallet.`"
    cancel-label="Keep order"
    confirm-label="Cancel order"
    destructive
    @confirm="$emit('confirm')"
  />
</template>
