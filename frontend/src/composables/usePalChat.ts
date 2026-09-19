import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { useAuthStore } from '@/stores/auth'

/** "Chat" button behaviour, shared by every place that offers one (a Pal's profile, a service
 * page, an order): sign-in redirect, the seed-Pal case where there is no `users.id` to message,
 * and otherwise straight to Messages.
 *
 * Deliberately does no network work. It used to create the thread and load its messages before
 * navigating, which left the user on the old page through two round trips (and then landed them
 * on whichever conversation happened to be first in the inbox). `MessagesPanel` takes `?with=`
 * and does the find-or-create itself, under its own loading state. */
export function usePalChat() {
  const router = useRouter()
  const authStore = useAuthStore()
  const toast = useToast()

  return function startChat(palUserId: string | null | undefined) {
    if (!authStore.isAuthenticated) {
      router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      return
    }
    if (!palUserId) {
      toast.add({ title: "Can't message this Pal yet", color: 'error' })
      return
    }
    router.push({ path: '/messages', query: { with: palUserId } })
  }
}
