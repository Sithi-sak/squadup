import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { useMessagesStore } from '@/stores/messages'

/** "Chat" button behaviour, shared by every place on a Pal's profile that offers it (the
 * Services book rail and the About card on Feeds): sign-in redirect, thread creation, and the
 * seed-Pal case where there is no `users.id` to message. */
export function usePalChat() {
  const router = useRouter()
  const messagesStore = useMessagesStore()
  const authStore = useAuthStore()
  const toast = useToast()

  return async function startChat(palUserId: string | null | undefined) {
    if (!authStore.isAuthenticated) {
      router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      return
    }
    if (!palUserId) {
      toast.add({ title: "Can't message this Pal yet", color: 'error' })
      return
    }
    try {
      await messagesStore.startThread(palUserId)
      router.push('/messages')
    } catch (err) {
      toast.add({
        title: "Couldn't start chat",
        description: err instanceof Error ? err.message : 'Please try again.',
        color: 'error',
      })
    }
  }
}
