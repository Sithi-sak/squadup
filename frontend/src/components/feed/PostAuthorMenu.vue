<script setup lang="ts">
import { ref } from 'vue'
import { PhDotsThree, PhTrash } from '@phosphor-icons/vue'
import ConfirmModal from '@/components/modals/ConfirmModal.vue'

/** The own-post action in `FeedPostCard`'s `action` slot: edit (what the pencil button used to
 * do on its own) plus delete behind a confirm, since a delete takes the post's comments and
 * likes with it and can't be undone. */
const emit = defineEmits<{ edit: []; delete: [] }>()

const confirmOpen = ref(false)

const items = [
  [{ label: 'Edit post', onSelect: () => emit('edit') }],
  [
    {
      label: 'Delete post',
      color: 'error' as const,
      onSelect: () => {
        confirmOpen.value = true
      },
    },
  ],
]

function confirmDelete() {
  confirmOpen.value = false
  emit('delete')
}
</script>

<template>
  <UDropdownMenu :items="items" :content="{ side: 'bottom', align: 'end' }">
    <UButton
      color="neutral"
      variant="ghost"
      square
      :ui="{ base: 'rounded-full' }"
      aria-label="Post options"
    >
      <PhDotsThree :size="20" weight="bold" />
    </UButton>
  </UDropdownMenu>

  <ConfirmModal
    v-model:open="confirmOpen"
    :icon="PhTrash"
    title="Delete this post?"
    description="The post, its comments and its likes are removed for everyone. This can't be undone."
    confirm-label="Delete"
    destructive
    @confirm="confirmDelete"
  />
</template>
