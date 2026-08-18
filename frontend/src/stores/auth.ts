import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export interface AuthUser {
  id: string
  email: string
  displayName: string | null
  role: 'user' | 'admin'
  /** Links to a `PlayerProfile` when this account also has a Pal profile (additive, not exclusive). */
  playerId: string | null
  onboardingComplete: boolean
  coinBalance: number
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => user.value !== null)

  function reset() {
    user.value = null
    loading.value = false
    error.value = null
  }

  return { user, loading, error, isAuthenticated, reset }
})
