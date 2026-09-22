<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import {
  PhBellSlash,
  PhDotsThree,
  PhMagnifyingGlass,
  PhPaperclip,
  PhUserCircle,
  PhX,
} from '@phosphor-icons/vue'
import { useMessagesStore, type MessageThread } from '@/stores/messages'
import { useAuthStore } from '@/stores/auth'
import { mockCurrentUser } from '@/mocks/users'
import { mockPlayers } from '@/mocks/players'
import { resolveAvatarUrl } from '@/utils/avatar'
import { userErrorMessage } from '@/utils/errors'
import { compressImage } from '@/utils/image'

/** Rejected before any decode work - the `message-images` bucket caps uploads at 8MB, and
 * compression only shrinks what it can actually read. */
const MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024

defineProps<{
  title: string
  subtitle: string
}>()

const store = useMessagesStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const toast = useToast()

// `thread.participantId` is a `users.id` (message threads are user-to-user, not
// player-to-player) - `user-profile` looks it up and itself redirects to `/players/{id}` if
// that user turns out to be a Pal, same as `profileRouteFor` does elsewhere.
function goToProfile(participantId: string) {
  router.push({ name: 'user-profile', params: { id: participantId } })
}
const search = ref('')
const draft = ref('')
const sending = ref(false)
/** `?with=` is still resolving to a thread - the conversation pane has nothing to show yet. */
const starting = ref(false)

// Falls back to the mock identity when signed out (or on a mock-fallback thread), same
// resilience convention `stores/messages.ts` uses for the thread/message data itself.
const currentUserId = computed(() => authStore.user?.id ?? mockCurrentUser.id)

// A deep link can request a specific thread via `?thread=id` - falls back to the first thread
// when absent/unknown, same as before.
function openThreadFromQuery() {
  const requestedId = route.query.thread
  if (typeof requestedId !== 'string' || !store.threads.some((t) => t.id === requestedId)) {
    return false
  }
  // `?with=` rewrites the url to `?thread=` once the thread exists, which re-runs the watcher -
  // without this the conversation would be fetched a second time on arrival.
  if (requestedId !== store.activeThreadId) store.selectThread(requestedId)
  return true
}

/** Every "Chat" button in the app links straight here with `?with=<user id>` rather than
 * creating the thread first and then navigating - the page opens immediately and the
 * find-or-create round trip happens under this panel's own loading state. The url is rewritten
 * to `?thread=<id>` afterwards so a reload (or Back) doesn't re-post. */
async function openParticipantFromQuery() {
  const participantId = route.query.with
  if (typeof participantId !== 'string' || !participantId) return false
  // `onMounted` and the `?with=` watcher can both reach here for the same arrival. Two
  // find-or-create posts in flight at once used to race each other in the backend, so only the
  // first one runs.
  if (starting.value) return true
  starting.value = true
  try {
    const thread = await store.startThread(participantId)
    router.replace({ path: route.path, query: { thread: thread.id } })
  } catch (err) {
    toast.add({
      title: "Couldn't start chat",
      description: userErrorMessage(err, 'Please try again in a moment.'),
      color: 'error',
    })
    router.replace({ path: route.path, query: {} })
  } finally {
    starting.value = false
  }
  return true
}

onMounted(() => {
  // Not awaited: opening the requested conversation shouldn't queue behind the whole inbox.
  const threadsLoaded = store.fetchThreads()
  if (route.query.with) {
    void openParticipantFromQuery()
    return
  }
  void threadsLoaded.then(() => {
    if (openThreadFromQuery()) return
    const firstThreadId = store.threads[0]?.id
    if (!store.activeThreadId && firstThreadId) store.selectThread(firstThreadId)
  })
})

// Handles landing on a different conversation while already on the Messages page, where
// `onMounted` won't fire again.
watch(
  () => route.query.thread,
  () => openThreadFromQuery(),
)
watch(
  () => route.query.with,
  (participantId) => {
    if (participantId) void openParticipantFromQuery()
  },
)

const filteredThreads = computed(() => {
  const query = search.value.trim().toLowerCase()
  const sorted = [...store.threads].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  )
  if (!query) return sorted
  return sorted.filter((thread) => thread.participantDisplayName.toLowerCase().includes(query))
})

function threadMenuItems(thread: MessageThread) {
  return [
    [
      {
        label: thread.muted ? 'Unmute chat' : 'Mute chat',
        onSelect: () => toggleMute(thread),
      },
    ],
    [
      {
        label: 'Delete chat',
        color: 'error' as const,
        onSelect: () => deleteChat(thread.id),
      },
    ],
  ]
}

async function toggleMute(thread: MessageThread) {
  try {
    await store.muteThread(thread.id, !thread.muted)
  } catch (err) {
    toast.add({
      title: "Couldn't update chat",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

async function deleteChat(threadId: string) {
  try {
    await store.deleteThread(threadId)
  } catch (err) {
    toast.add({
      title: "Couldn't delete chat",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}

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

// Attachment ------------------------------------------------------------------------------

const fileInput = ref<HTMLInputElement | null>(null)
/** The picked image, already downscaled - `compressImage` runs at pick time rather than at send
 * time so the wait lands while the user is still typing, not after they hit Send. */
const attachment = ref<File | null>(null)
const attachmentPreview = ref<string | null>(null)
const compressing = ref(false)

function clearAttachment() {
  if (attachmentPreview.value) URL.revokeObjectURL(attachmentPreview.value)
  attachmentPreview.value = null
  attachment.value = null
  if (fileInput.value) fileInput.value.value = ''
}

onBeforeUnmount(clearAttachment)

async function onFilePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    toast.add({ title: 'Only images can be attached', color: 'error' })
    return
  }
  if (file.size > MAX_ATTACHMENT_BYTES) {
    toast.add({
      title: 'That image is too large',
      description: 'Pick one under 25MB.',
      color: 'error',
    })
    return
  }

  clearAttachment()
  compressing.value = true
  try {
    const compressed = await compressImage(file)
    attachment.value = compressed
    attachmentPreview.value = URL.createObjectURL(compressed)
  } finally {
    compressing.value = false
  }
}

// Transcript ------------------------------------------------------------------------------

const transcript = ref<HTMLElement | null>(null)

function scrollToBottom() {
  const el = transcript.value
  if (el) el.scrollTop = el.scrollHeight
}

// Covers the first paint of a conversation, every incoming realtime message and every sent one.
// `loadEarlier` prepends instead of appending, so it deliberately isn't in this count.
watch(
  () => [store.activeThreadId, store.activeMessages.length],
  () => {
    void nextTick(scrollToBottom)
  },
)

async function handleLoadEarlier() {
  const el = transcript.value
  const before = el?.scrollHeight ?? 0
  try {
    await store.loadEarlier()
  } catch (err) {
    toast.add({
      title: "Couldn't load earlier messages",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
    return
  }
  // Keeps the message the user was reading where it was, instead of yanking the view to the top
  // of the newly prepended page.
  await nextTick()
  if (el) el.scrollTop = el.scrollHeight - before
}

async function handleSend() {
  const body = draft.value.trim()
  const image = attachment.value
  if ((!body && !image) || sending.value || compressing.value) return
  sending.value = true
  try {
    await store.sendMessage({ body, image })
    draft.value = ''
    clearAttachment()
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
    <div>
      <h1 class="text-3xl font-bold text-white">{{ title }}</h1>
      <p class="mt-1 text-sm text-slate-400">{{ subtitle }}</p>
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
            size="lg"
            class="w-full rounded-full"
            :ui="{ base: 'rounded-full' }"
          >
            <template #leading>
              <PhMagnifyingGlass :size="20" />
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
              <UButton color="primary" class="rounded-full" @click="store.fetchThreads()"
                >Retry</UButton
              >
            </template>
          </UEmpty>

          <template v-else>
            <div
              v-for="thread in filteredThreads"
              :key="thread.id"
              role="button"
              tabindex="0"
              class="group flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
              :class="thread.id === store.activeThreadId ? 'bg-brand-600/15' : 'hover:bg-white/5'"
              @click="store.selectThread(thread.id)"
              @keydown.enter="store.selectThread(thread.id)"
            >
              <button
                type="button"
                class="relative shrink-0 cursor-pointer"
                aria-label="View profile"
                @click.stop="goToProfile(thread.participantId)"
              >
                <UAvatar
                  :src="
                    resolveAvatarUrl(
                      thread.participantId,
                      participant(thread.participantId)?.avatarUrl,
                    )
                  "
                  size="md"
                  class="bg-white/10 text-slate-300"
                >
                  <PhUserCircle :size="22" />
                </UAvatar>
                <span
                  v-if="participant(thread.participantId)?.online"
                  class="absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-brand-400 ring-2 ring-gray-800"
                />
              </button>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <p
                    class="w-fit truncate text-sm font-semibold text-white hover:underline"
                    @click.stop="goToProfile(thread.participantId)"
                  >
                    {{ thread.participantDisplayName }}
                  </p>
                  <PhBellSlash v-if="thread.muted" :size="14" class="shrink-0 text-slate-500" />
                </div>
                <p class="truncate text-sm text-slate-400">{{ thread.lastMessagePreview }}</p>
              </div>
              <div class="flex shrink-0 flex-col items-end gap-1.5">
                <div class="flex items-center gap-1">
                  <span class="text-xs text-slate-500">{{ formatRelative(thread.updatedAt) }}</span>
                  <UDropdownMenu
                    :items="threadMenuItems(thread)"
                    :content="{ side: 'bottom', align: 'end' }"
                  >
                    <UButton
                      color="neutral"
                      variant="ghost"
                      size="xs"
                      square
                      :ui="{ base: 'rounded-full' }"
                      aria-label="Chat options"
                      class="opacity-0 group-hover:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100"
                      @click.stop
                    >
                      <PhDotsThree :size="24" />
                    </UButton>
                  </UDropdownMenu>
                </div>
                <span
                  v-if="thread.unreadCount"
                  class="flex h-5 w-5 items-center justify-center rounded-full bg-brand-500 text-xs font-semibold text-white"
                >
                  {{ thread.unreadCount }}
                </span>
              </div>
            </div>

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
          <router-link
            :to="{ name: 'user-profile', params: { id: store.activeThread.participantId } }"
            class="flex items-center gap-3"
          >
            <UAvatar
              :src="
                resolveAvatarUrl(store.activeThread.participantId, activeParticipant?.avatarUrl)
              "
              size="md"
              class="bg-white/10 text-slate-300"
            >
              <PhUserCircle :size="22" />
            </UAvatar>
            <div>
              <p class="font-semibold text-white hover:underline">
                {{ store.activeThread.participantDisplayName }}
              </p>
              <p class="text-sm text-slate-400">
                <span v-if="activeParticipant?.games?.[0]"
                  >{{ activeParticipant.games[0] }} ·
                </span>
                {{ activeParticipant?.online ? 'Online' : 'Offline' }}
              </p>
            </div>
          </router-link>
        </div>

        <div ref="transcript" class="flex-1 space-y-4 overflow-y-auto px-5 py-4">
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
              <UButton
                color="primary"
                class="rounded-full"
                @click="store.selectThread(store.activeThread.id)"
              >
                Retry
              </UButton>
            </template>
          </UEmpty>

          <template v-else>
            <div v-if="store.activeHasMore" class="flex justify-center">
              <UButton
                color="neutral"
                variant="soft"
                size="sm"
                class="rounded-full"
                :loading="store.loadingEarlier"
                @click="handleLoadEarlier"
              >
                Load earlier messages
              </UButton>
            </div>

            <div
              v-for="message in store.activeMessages"
              :key="message.id"
              class="flex flex-col"
              :class="message.senderId === currentUserId ? 'items-end' : 'items-start'"
            >
              <a
                v-if="message.imageUrl"
                :href="message.imageUrl"
                target="_blank"
                rel="noopener"
                class="max-w-[75%] overflow-hidden rounded-2xl ring-1 ring-white/10"
              >
                <img
                  :src="message.imageUrl"
                  alt="Shared image"
                  loading="lazy"
                  class="max-h-80 w-full object-cover"
                  @load="scrollToBottom"
                />
              </a>
              <div
                v-if="message.body"
                class="max-w-[75%] rounded-full px-4 py-2.5 text-sm"
                :class="[
                  message.senderId === currentUserId
                    ? 'bg-brand-600 text-white'
                    : 'bg-white/10 text-slate-100',
                  message.imageUrl ? 'mt-1.5' : '',
                ]"
              >
                {{ message.body }}
              </div>
              <span class="mt-1 text-xs text-slate-500">{{ formatTime(message.createdAt) }}</span>
            </div>
          </template>
        </div>

        <div class="border-t border-white/10 px-4 py-3">
          <div v-if="compressing || attachmentPreview" class="mb-2 flex items-center gap-3">
            <div class="relative">
              <div
                v-if="compressing"
                class="flex h-16 w-16 items-center justify-center rounded-lg bg-white/5 text-xs text-slate-400"
              >
                Resizing
              </div>
              <img
                v-else-if="attachmentPreview"
                :src="attachmentPreview"
                alt="Attachment preview"
                class="h-16 w-16 rounded-lg object-cover ring-1 ring-white/10"
              />
              <button
                v-if="attachmentPreview"
                type="button"
                class="absolute -top-1.5 -right-1.5 flex h-5 w-5 cursor-pointer items-center justify-center rounded-full bg-gray-900 text-slate-300 ring-1 ring-white/20 hover:text-white"
                aria-label="Remove attachment"
                @click="clearAttachment"
              >
                <PhX :size="12" />
              </button>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onFilePicked"
            />
            <UButton
              color="neutral"
              variant="ghost"
              square
              :ui="{ base: 'rounded-full' }"
              aria-label="Attach an image"
              :disabled="compressing"
              @click="fileInput?.click()"
            >
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
            />
            <UButton
              color="primary"
              size="lg"
              class="rounded-full px-5"
              :loading="sending"
              :disabled="compressing"
              @click="handleSend"
            >
              Send
            </UButton>
          </div>
        </div>
      </div>

      <div
        v-else-if="starting"
        class="flex flex-1 items-center justify-center text-sm text-slate-400"
      >
        Opening chat...
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
