import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export interface MessageThread {
  id: string
  participantId: string
  participantName: string
  lastMessagePreview: string | null
  updatedAt: string
}

export interface ChatMessage {
  id: string
  threadId: string
  senderId: string
  body: string
  createdAt: string
}

export const useMessagesStore = defineStore('messages', () => {
  const threads = ref<MessageThread[]>([])
  const activeThreadId = ref<string | null>(null)
  const messagesByThread = ref<Record<string, ChatMessage[]>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeMessages = computed(() =>
    activeThreadId.value ? (messagesByThread.value[activeThreadId.value] ?? []) : [],
  )

  return { threads, activeThreadId, messagesByThread, activeMessages, loading, error }
})
