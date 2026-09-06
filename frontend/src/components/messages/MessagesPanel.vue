<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import {
  PhDotsThree,
  PhMagnifyingGlass,
  PhPaperclip,
  PhPhone,
  PhPlus,
  PhSmiley,
  PhUserCircle,
} from '@phosphor-icons/vue'
import { useMessagesStore } from '@/stores/messages'
import { useAuthStore } from '@/stores/auth'
import { mockCurrentUser } from '@/mocks/users'
import { mockPlayers } from '@/mocks/players'
import { resolveAvatarUrl } from '@/utils/avatar'

defineProps<{
  title: string
  subtitle: string
}>()

const store = useMessagesStore()
const authStore = useAuthStore()
const toast = useToast()
const search = ref('')
const draft = ref('')
const sending = ref(false)

// Falls back to the mock identity when signed out (or on a mock-fallback thread), same
// resilience convention `stores/messages.ts` uses for the thread/message data itself.
const currentUserId = computed(() => authStore.user?.id ?? mockCurrentUser.id)

onMounted(async () => {
  await store.fetchThreads()
  const firstThreadId = store.threads[0]?.id
  if (!store.activeThreadId && firstThreadId) {
    store.selectThread(firstThreadId)
  }
})

const filteredThreads = computed(() => {
  const query = search.value.trim().toLowerCase()
  const sorted = [...store.threads].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  )
  if (!query) return sorted
  return sorted.filter((thread) => thread.participantDisplayName.toLowerCase().includes(query))
})

const totalUnread = computed(() => store.threads.reduce((sum, t) => sum + t.unreadCount, 0))

function participant(id: string) {
  return mockPlayers.find((p) => p.id === id) ?? null
}

const activeParticipant = computed(() =>
  store.activeThread ? participant(store.activeThread.participantId) : null,
)

function formatRelative(iso: string) {
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (minutes < 1) return 'now'
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

async function handleSend() {
  if (!draft.value.trim() || sending.value) return
  const body = draft.value
  sending.value = true
  try {
    await store.sendMessage(body)
    draft.value = ''
  } catch (err) {
    toast.add({
      title: "Couldn't send message",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="flex h-full flex-col gap-5">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-white">{{ title }}</h1>
        <p class="mt-1 text-sm text-slate-400">{{ subtitle }}</p>
      </div>
      <UButton color="primary" class="rounded-full" disabled title="Coming soon">
        <PhPlus :size="16" weight="bold" />
        New chat
      </UButton>
    </div>

    <div
      class="grid min-h-0 flex-1 grid-cols-1 overflow-hidden rounded-xl bg-gray-800/70 md:grid-cols-[320px_1fr]"
    >
      <div class="flex min-h-0 flex-col border-b border-white/10 md:border-r md:border-b-0">
        <div class="flex items-center justify-between gap-2 px-4 pt-4">
          <h2 class="text-lg font-semibold text-white">Chats</h2>
          <UBadge v-if="totalUnread" color="primary" variant="soft" size="sm" class="rounded-full">
            {{ totalUnread }} new
          </UBadge>
        </div>
        <div class="px-4 pt-3">
          <UInput
            v-model="search"
            placeholder="Search chats"
            variant="subtle"
            class="w-full rounded-full"
            :ui="{ base: 'rounded-full' }"
          >
            <template #leading>
              <PhMagnifyingGlass :size="16" />
            </template>
          </UInput>
        </div>

        <div class="mt-3 flex-1 overflow-y-auto">
          <div
            v-if="store.threadsLoading && store.threads.length === 0"
            class="py-10 text-center text-sm text-slate-400"
          >
            Loading chats...
          </div>

          <UEmpty
            v-else-if="store.threadsError"
            variant="naked"
            title="Couldn't load chats"
            :description="store.threadsError"
            class="py-10 text-white"
          >
            <template #actions>
              <UButton color="primary" class="rounded-full" @click="store.fetchThreads()">Retry</UButton>
            </template>
          </UEmpty>

          <template v-else>
            <button
              v-for="thread in filteredThreads"
              :key="thread.id"
              type="button"
              class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
              :class="thread.id === store.activeThreadId ? 'bg-brand-600/15' : 'hover:bg-white/5'"
              @click="store.selectThread(thread.id)"
            >
              <div class="relative shrink-0">
                <UAvatar
                  :src="resolveAvatarUrl(thread.participantId, participant(thread.participantId)?.avatarUrl)"
                  size="md"
                  class="bg-white/10 text-slate-300"
                >
                  <PhUserCircle :size="22" />
                </UAvatar>
                <span
                  v-if="participant(thread.participantId)?.online"
                  class="absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-brand-400 ring-2 ring-gray-800"
                />
              </div>
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-semibold text-white">{{ thread.participantDisplayName }}</p>
                <p class="truncate text-sm text-slate-400">{{ thread.lastMessagePreview }}</p>
              </div>
              <div class="flex shrink-0 flex-col items-end gap-1.5">
                <span class="text-xs text-slate-500">{{ formatRelative(thread.updatedAt) }}</span>
                <span
                  v-if="thread.unreadCount"
                  class="flex h-5 w-5 items-center justify-center rounded-full bg-brand-500 text-xs font-semibold text-white"
                >
                  {{ thread.unreadCount }}
                </span>
              </div>
            </button>

            <UEmpty
              v-if="filteredThreads.length === 0 && store.threads.length === 0"
              variant="naked"
              title="No chats yet"
              description="Start a conversation from a Pal's profile or booking to see it here."
              class="py-10 text-white"
            />
            <UEmpty
              v-else-if="filteredThreads.length === 0"
              variant="naked"
              title="No chats found"
              class="py-10 text-white"
            />
          </template>
        </div>
      </div>

      <div v-if="store.activeThread" class="flex min-h-0 min-w-0 flex-col">
        <div class="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
          <div class="flex items-center gap-3">
            <UAvatar
              :src="resolveAvatarUrl(store.activeThread.participantId, activeParticipant?.avatarUrl)"
              size="md"
              class="bg-white/10 text-slate-300"
            >
              <PhUserCircle :size="22" />
            </UAvatar>
            <div>
              <p class="font-semibold text-white">{{ store.activeThread.participantDisplayName }}</p>
              <p class="text-xs text-slate-400">
                <span v-if="activeParticipant?.games?.[0]">{{ activeParticipant.games[0] }} · </span>
                {{ activeParticipant?.online ? 'Online' : 'Offline' }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <UButton color="neutral" variant="ghost" square :ui="{ base: 'rounded-full' }" aria-label="Call">
              <PhPhone :size="24" />
            </UButton>
            <UButton color="neutral" variant="ghost" square :ui="{ base: 'rounded-full' }" aria-label="More">
              <PhDotsThree :size="24" />
            </UButton>
          </div>
        </div>

        <div class="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          <div
            v-if="store.messagesLoading && store.activeMessages.length === 0"
            class="py-10 text-center text-sm text-slate-400"
          >
            Loading messages...
          </div>

          <UEmpty
            v-else-if="store.messagesError"
            variant="naked"
            title="Couldn't load messages"
            :description="store.messagesError"
            class="py-10 text-white"
          >
            <template #actions>
              <UButton color="primary" class="rounded-full" @click="store.selectThread(store.activeThread.id)">
                Retry
              </UButton>
            </template>
          </UEmpty>

          <template v-else>
            <div
              v-for="message in store.activeMessages"
              :key="message.id"
              class="flex flex-col"
              :class="message.senderId === currentUserId ? 'items-end' : 'items-start'"
            >
              <div
                class="max-w-[75%] rounded-full px-4 py-2.5 text-sm"
                :class="
                  message.senderId === currentUserId
                    ? 'bg-brand-600 text-white'
                    : 'bg-white/10 text-slate-100'
                "
              >
                {{ message.body }}
              </div>
              <span class="mt-1 text-xs text-slate-500">{{ formatTime(message.createdAt) }}</span>
            </div>
          </template>
        </div>

        <div class="flex items-center gap-2 border-t border-white/10 px-4 py-3">
          <UButton color="neutral" variant="ghost" square :ui="{ base: 'rounded-full' }" aria-label="Attach">
            <PhPaperclip :size="24" />
          </UButton>
          <UInput
            v-model="draft"
            :placeholder="`Message ${store.activeThread.participantDisplayName}...`"
            variant="subtle"
            size="lg"
            class="flex-1 rounded-full"
            :ui="{ base: 'rounded-full' }"
            :disabled="sending"
            @keyup.enter="handleSend"
          >
            <template #trailing>
              <PhSmiley :size="24" class="text-slate-400" />
            </template>
          </UInput>
          <UButton color="primary" size="lg" class="rounded-full px-5" :loading="sending" @click="handleSend">
            Send
          </UButton>
        </div>
      </div>

      <UEmpty
        v-else
        variant="naked"
        title="Select a chat"
        description="Choose a conversation to start messaging."
        class="flex-1 text-white"
      />
    </div>
  </div>
</template>
