<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { useUsersStore, type BlockedUser } from '@/stores/users'
import { resolveAvatarUrl } from '@/utils/avatar'

/** Settings > Privacy > Blocked accounts (4.39). The block modal has always told people they
 * can unblock "anytime from settings"; this is that screen. */
const open = defineModel<boolean>('open', { required: true })

const emit = defineEmits<{ changed: [count: number] }>()

const usersStore = useUsersStore()
const toast = useToast()

const blocked = ref<BlockedUser[]>([])
const loading = ref(false)
const pendingId = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    blocked.value = await usersStore.fetchMyBlocks()
    emit('changed', blocked.value.length)
  } catch (err) {
    toast.add({
      title: 'Could not load blocked accounts',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

watch(open, (isOpen) => {
  if (isOpen) load()
})

async function unblock(user: BlockedUser) {
  if (pendingId.value) return
  pendingId.value = user.id
  try {
    await usersStore.unblockUser(user.id)
    blocked.value = blocked.value.filter((u) => u.id !== user.id)
    emit('changed', blocked.value.length)
    toast.add({ title: `Unblocked ${user.handle ?? user.displayName ?? 'account'}`, color: 'success' })
  } catch (err) {
    toast.add({
      title: 'Could not unblock',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    pendingId.value = null
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Blocked accounts"
    :ui="{ content: 'max-w-lg rounded-3xl', body: 'max-h-[70vh] overflow-y-auto' }"
  >
    <template #body>
      <div class="flex flex-col gap-3">
        <p class="text-sm text-slate-400">
          Blocked accounts can't message you, book your services, or view your profile.
        </p>

        <div v-if="loading" class="flex flex-col gap-3">
          <USkeleton v-for="n in 3" :key="n" class="h-14 w-full rounded-2xl" />
        </div>

        <p v-else-if="blocked.length === 0" class="py-10 text-center text-sm text-slate-400">
          You haven't blocked anyone.
        </p>

        <div
          v-for="user in blocked"
          v-else
          :key="user.id"
          class="flex items-center gap-3 rounded-2xl bg-gray-800/70 p-3"
        >
          <UAvatar
            :src="resolveAvatarUrl(user.id, user.avatarUrl)"
            size="md"
            class="shrink-0 bg-white/10 text-slate-300"
          >
            <PhUserCircle :size="20" />
          </UAvatar>
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium text-white">{{ user.displayName ?? 'SquadUp user' }}</p>
            <p v-if="user.handle" class="truncate text-sm text-slate-400">{{ user.handle }}</p>
          </div>
          <UButton
            color="neutral"
            variant="soft"
            size="sm"
            class="shrink-0 rounded-full"
            :loading="pendingId === user.id"
            :disabled="pendingId === user.id"
            @click="unblock(user)"
          >
            Unblock
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
