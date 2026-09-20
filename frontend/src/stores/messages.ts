import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import { mockMessagesByThread, mockThreads } from '@/mocks/messages'
import { useNotificationsStore } from '@/stores/notifications'

export interface MessageThread {
  id: string
  participantId: string
  participantDisplayName: string
  lastMessagePreview: string | null
  updatedAt: string
  unreadCount: number
  muted: boolean
}

export interface ChatMessage {
  id: string
  threadId: string
  senderId: string
  body: string
  imageUrl: string | null
  createdAt: string
}

/** Raw `public.messages` row shape as Supabase Realtime delivers it (snake_case DB columns,
 * not the backend's camelCase `ChatMessage`). */
interface MessageRow {
  id: string
  thread_id: string
  sender_id: string
  body: string
  image_url: string | null
  created_at: string
}

/** Messages a conversation opens with, and the size of each "Load earlier" page. Matches the
 * backend's own `_MESSAGE_PAGE_SIZE` default - sent explicitly so the two can't drift apart
 * without `hasMoreByThread` noticing. */
const PAGE_SIZE = 40

export const useMessagesStore = defineStore('messages', () => {
  const threads = ref<MessageThread[]>([])
  const threadsLoading = ref(false)
  const threadsError = ref<string | null>(null)

  const activeThreadId = ref<string | null>(null)
  const messagesByThread = ref<Record<string, ChatMessage[]>>({})
  const messagesLoading = ref(false)
  const messagesError = ref<string | null>(null)
  /** Whether an older page exists for a thread - a full page came back, so there may be more. */
  const hasMoreByThread = ref<Record<string, boolean>>({})
  const loadingEarlier = ref(false)

  const activeThread = computed(
    () => threads.value.find((t) => t.id === activeThreadId.value) ?? null,
  )
  const activeMessages = computed(() =>
    activeThreadId.value ? (messagesByThread.value[activeThreadId.value] ?? []) : [],
  )
  const activeHasMore = computed(() =>
    activeThreadId.value ? (hasMoreByThread.value[activeThreadId.value] ?? false) : false,
  )

  function appendMessage(threadId: string, message: ChatMessage) {
    const existing = (messagesByThread.value[threadId] ??= [])
    if (existing.some((m) => m.id === message.id)) return
    existing.push(message)
    const thread = threads.value.find((t) => t.id === threadId)
    if (thread) {
      // An image-only message has an empty body, same as the backend's own `_preview`.
      thread.lastMessagePreview = message.body || (message.imageUrl ? 'Photo' : '')
      thread.updatedAt = message.createdAt
    }
  }

  // Live updates for the open thread (CHECKPOINT.md 3.5b's RLS policies authorize each event
  // against the viewer's own JWT), replacing polling - subscribes/unsubscribes as
  // `activeThreadId` changes rather than staying on one thread's channel forever.
  let realtimeChannel: RealtimeChannel | null = null

  function unsubscribeRealtime() {
    if (realtimeChannel) {
      supabase.removeChannel(realtimeChannel)
      realtimeChannel = null
    }
  }

  function subscribeRealtime(threadId: string) {
    unsubscribeRealtime()
    realtimeChannel = supabase
      .channel(`messages:${threadId}`)
      .on<MessageRow>(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `thread_id=eq.${threadId}`,
        },
        ({ new: row }) => {
          appendMessage(threadId, {
            id: row.id,
            threadId: row.thread_id,
            senderId: row.sender_id,
            body: row.body,
            imageUrl: row.image_url,
            createdAt: row.created_at,
          })
        },
      )
      .subscribe()
  }

  watch(activeThreadId, (id) => {
    if (id) subscribeRealtime(id)
    else unsubscribeRealtime()
  })

  /** Messages page's thread list. Falls back to `mockThreads` if the request fails (signed out,
   * network error, backend down), same resilience convention as 3.1j/3.2d/3.4c. */
  async function fetchThreads() {
    threadsLoading.value = true
    threadsError.value = null
    try {
      const fetched = await api.get<MessageThread[]>('/messages/threads')
      // `MessagesPanel` fires this alongside `?with=`'s `startThread`, so a thread created
      // after the server had already read the list would otherwise vanish from the inbox the
      // moment this response lands - and take the open conversation down with it.
      const active = threads.value.find((t) => t.id === activeThreadId.value)
      threads.value =
        active && !fetched.some((t) => t.id === active.id) ? [active, ...fetched] : fetched
    } catch (err) {
      threadsError.value = err instanceof Error ? err.message : 'Failed to load chats'
      threads.value = [...mockThreads]
    } finally {
      threadsLoading.value = false
    }
  }

  /** Opening a thread - also marks the other party's messages read server-side (replaces the
   * old frontend-only `unreadCount = 0`), so this always refetches rather than reusing a cached
   * list even when messages for this thread were already loaded once. Only the newest
   * `PAGE_SIZE` come back; `loadEarlier` walks backwards from there (4.49). */
  async function fetchMessages(threadId: string) {
    // A cached transcript stays on screen while the refresh runs - re-opening a chat you were
    // just in shouldn't blank the pane and then repaint it.
    messagesLoading.value = !messagesByThread.value[threadId]?.length
    messagesError.value = null
    try {
      const page = await api.get<ChatMessage[]>(
        `/messages/threads/${threadId}/messages?limit=${PAGE_SIZE}`,
      )
      messagesByThread.value[threadId] = page
      hasMoreByThread.value[threadId] = page.length === PAGE_SIZE
      const thread = threads.value.find((t) => t.id === threadId)
      if (thread) thread.unreadCount = 0
    } catch (err) {
      messagesError.value = err instanceof Error ? err.message : 'Failed to load messages'
      messagesByThread.value[threadId] = mockMessagesByThread[threadId] ?? []
      hasMoreByThread.value[threadId] = false
    } finally {
      messagesLoading.value = false
    }
  }

  /** Prepends the page of messages older than the oldest one held for `threadId`. Errors are
   * swallowed into `hasMore` staying true rather than replacing the transcript with an error
   * state - the conversation on screen is still perfectly readable. */
  async function loadEarlier(threadId: string | null = activeThreadId.value) {
    if (!threadId || loadingEarlier.value || !hasMoreByThread.value[threadId]) return
    const existing = messagesByThread.value[threadId] ?? []
    const oldest = existing[0]
    if (!oldest) return
    loadingEarlier.value = true
    try {
      const page = await api.get<ChatMessage[]>(
        `/messages/threads/${threadId}/messages?limit=${PAGE_SIZE}&before=${encodeURIComponent(oldest.createdAt)}`,
      )
      const known = new Set(existing.map((m) => m.id))
      messagesByThread.value[threadId] = [...page.filter((m) => !known.has(m.id)), ...existing]
      hasMoreByThread.value[threadId] = page.length === PAGE_SIZE
    } finally {
      loadingEarlier.value = false
    }
  }

  async function selectThread(id: string) {
    activeThreadId.value = id
    await fetchMessages(id)
    // Chat alerts live on the header's messages badge rather than the bell, so reading the
    // conversation is what takes them down. Strictly best-effort and deliberately not awaited:
    // clearing a badge must never be the reason opening (or starting) a chat fails.
    try {
      void useNotificationsStore()
        .markThreadRead(id)
        .catch(() => {})
    } catch {
      // ignore
    }
  }

  /** Find-or-create a thread with `participantId` and select it (backend dedups regardless of
   * who initiates, CHECKPOINT.md 3.5a). */
  async function startThread(participantId: string) {
    const thread = await api.post<MessageThread>('/messages/threads', { participantId })
    const index = threads.value.findIndex((t) => t.id === thread.id)
    if (index === -1) threads.value.unshift(thread)
    else threads.value[index] = thread
    await selectThread(thread.id)
    return thread
  }

  /** Multipart rather than JSON (4.49) so an attached image rides along as a real file, the
   * same way the feed composer posts one - the caller compresses it first (`utils/image.ts`)
   * and the backend re-encodes it to WebP. Either the text or the image may be missing, not
   * both. */
  async function sendMessage(payload: { body?: string; image?: File | null }) {
    const threadId = activeThreadId.value
    const text = (payload.body ?? '').trim()
    if (!threadId || (!text && !payload.image)) return
    const formData = new FormData()
    formData.append('body', text)
    if (payload.image) formData.append('image', payload.image)
    const message = await api.post<ChatMessage>(`/messages/threads/${threadId}/messages`, formData)
    appendMessage(threadId, message)
    return message
  }

  /** Optimistic: flips `muted` immediately rather than waiting on the round trip, since nothing
   * about the mute state depends on the server's response - rolls back on failure. */
  async function muteThread(threadId: string, muted: boolean) {
    const thread = threads.value.find((t) => t.id === threadId)
    if (!thread) return
    const previous = thread.muted
    thread.muted = muted
    try {
      await api.patch(`/messages/threads/${threadId}/mute`, { muted })
    } catch (err) {
      thread.muted = previous
      throw err
    }
  }

  /** Optimistic removal, same rationale as `muteThread` - restores the thread (and active
   * selection) in place on failure. */
  async function deleteThread(threadId: string) {
    const index = threads.value.findIndex((t) => t.id === threadId)
    if (index === -1) return
    const [removed] = threads.value.splice(index, 1)
    const wasActive = activeThreadId.value === threadId
    if (wasActive) activeThreadId.value = null

    try {
      await api.delete(`/messages/threads/${threadId}`)
    } catch (err) {
      threads.value.splice(index, 0, removed)
      if (wasActive) activeThreadId.value = threadId
      throw err
    }

    if (wasActive) {
      delete messagesByThread.value[threadId]
      const fallbackId = threads.value[0]?.id
      if (fallbackId) await selectThread(fallbackId)
    }
  }

  return {
    threads,
    threadsLoading,
    threadsError,
    activeThreadId,
    activeThread,
    messagesByThread,
    activeMessages,
    messagesLoading,
    messagesError,
    hasMoreByThread,
    activeHasMore,
    loadingEarlier,
    fetchThreads,
    selectThread,
    loadEarlier,
    startThread,
    sendMessage,
    muteThread,
    deleteThread,
  }
})
