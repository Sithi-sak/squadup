import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import { mockMessagesByThread, mockThreads } from '@/mocks/messages'

export interface MessageThread {
  id: string
  participantId: string
  participantDisplayName: string
  lastMessagePreview: string | null
  updatedAt: string
  unreadCount: number
}

export interface ChatMessage {
  id: string
  threadId: string
  senderId: string
  body: string
  createdAt: string
}

/** Raw `public.messages` row shape as Supabase Realtime delivers it (snake_case DB columns,
 * not the backend's camelCase `ChatMessage`). */
interface MessageRow {
  id: string
  thread_id: string
  sender_id: string
  body: string
  created_at: string
}

export const useMessagesStore = defineStore('messages', () => {
  const threads = ref<MessageThread[]>([])
  const threadsLoading = ref(false)
  const threadsError = ref<string | null>(null)

  const activeThreadId = ref<string | null>(null)
  const messagesByThread = ref<Record<string, ChatMessage[]>>({})
  const messagesLoading = ref(false)
  const messagesError = ref<string | null>(null)

  const activeThread = computed(
    () => threads.value.find((t) => t.id === activeThreadId.value) ?? null,
  )
  const activeMessages = computed(() =>
    activeThreadId.value ? (messagesByThread.value[activeThreadId.value] ?? []) : [],
  )

  function appendMessage(threadId: string, message: ChatMessage) {
    const existing = (messagesByThread.value[threadId] ??= [])
    if (existing.some((m) => m.id === message.id)) return
    existing.push(message)
    const thread = threads.value.find((t) => t.id === threadId)
    if (thread) {
      thread.lastMessagePreview = message.body
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
        { event: 'INSERT', schema: 'public', table: 'messages', filter: `thread_id=eq.${threadId}` },
        ({ new: row }) => {
          appendMessage(threadId, {
            id: row.id,
            threadId: row.thread_id,
            senderId: row.sender_id,
            body: row.body,
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
      threads.value = await api.get<MessageThread[]>('/messages/threads')
    } catch (err) {
      threadsError.value = err instanceof Error ? err.message : 'Failed to load chats'
      threads.value = [...mockThreads]
    } finally {
      threadsLoading.value = false
    }
  }

  /** Opening a thread - also marks the other party's messages read server-side (replaces the
   * old frontend-only `unreadCount = 0`), so this always refetches rather than reusing a cached
   * list even when messages for this thread were already loaded once. */
  async function fetchMessages(threadId: string) {
    messagesLoading.value = true
    messagesError.value = null
    try {
      messagesByThread.value[threadId] = await api.get<ChatMessage[]>(
        `/messages/threads/${threadId}/messages`,
      )
      const thread = threads.value.find((t) => t.id === threadId)
      if (thread) thread.unreadCount = 0
    } catch (err) {
      messagesError.value = err instanceof Error ? err.message : 'Failed to load messages'
      messagesByThread.value[threadId] = mockMessagesByThread[threadId] ?? []
    } finally {
      messagesLoading.value = false
    }
  }

  async function selectThread(id: string) {
    activeThreadId.value = id
    await fetchMessages(id)
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

  async function sendMessage(body: string) {
    const threadId = activeThreadId.value
    const text = body.trim()
    if (!threadId || !text) return
    const message = await api.post<ChatMessage>(`/messages/threads/${threadId}/messages`, { body: text })
    appendMessage(threadId, message)
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
    fetchThreads,
    selectThread,
    startThread,
    sendMessage,
  }
})
