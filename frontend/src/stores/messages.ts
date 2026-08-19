import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { mockMessagesByThread, mockThreads } from '@/mocks/messages'
import { mockCurrentUser } from '@/mocks/users'

export interface MessageThread {
  id: string
  participantId: string
  participantName: string
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

export const useMessagesStore = defineStore('messages', () => {
  const threads = ref<MessageThread[]>([...mockThreads])
  const activeThreadId = ref<string | null>(threads.value[0]?.id ?? null)
  const messagesByThread = ref<Record<string, ChatMessage[]>>({ ...mockMessagesByThread })
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeThread = computed(
    () => threads.value.find((t) => t.id === activeThreadId.value) ?? null,
  )
  const activeMessages = computed(() =>
    activeThreadId.value ? (messagesByThread.value[activeThreadId.value] ?? []) : [],
  )

  function selectThread(id: string) {
    activeThreadId.value = id
    const thread = threads.value.find((t) => t.id === id)
    if (thread) thread.unreadCount = 0
  }

  function sendMessage(body: string) {
    const threadId = activeThreadId.value
    const text = body.trim()
    if (!threadId || !text) return

    const message: ChatMessage = {
      id: `m-${Date.now()}`,
      threadId,
      senderId: mockCurrentUser.id,
      body: text,
      createdAt: new Date().toISOString(),
    }
    ;(messagesByThread.value[threadId] ??= []).push(message)

    const thread = threads.value.find((t) => t.id === threadId)
    if (thread) {
      thread.lastMessagePreview = text
      thread.updatedAt = message.createdAt
    }
  }

  return {
    threads,
    activeThreadId,
    activeThread,
    messagesByThread,
    activeMessages,
    loading,
    error,
    selectThread,
    sendMessage,
  }
})
