import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { User } from '@supabase/supabase-js'
import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import { useSettingsStore } from '@/stores/settings'

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

/** Loads the `public.users` row a signed-in Supabase user is backed by (populated by the
 * `handle_new_user` trigger on signup, see supabase/migrations), plus `playerId` — the
 * `players` row's id if this account has also completed Become a Player (3.1), else `null`. */
async function loadAuthUser(supabaseUser: User): Promise<AuthUser> {
  const [{ data }, { data: player }] = await Promise.all([
    supabase
      .from('users')
      .select('display_name, role, onboarding_complete, coin_balance')
      .eq('id', supabaseUser.id)
      .maybeSingle(),
    supabase.from('players').select('id').eq('user_id', supabaseUser.id).maybeSingle(),
  ])

  return {
    id: supabaseUser.id,
    email: supabaseUser.email ?? '',
    displayName: data?.display_name ?? null,
    role: (data?.role as AuthUser['role']) ?? 'user',
    playerId: player?.id ?? null,
    onboardingComplete: data?.onboarding_complete ?? false,
    coinBalance: data?.coin_balance ?? 0,
  }
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

  /** Restores any persisted session and starts listening for sign-in/out. Memoized: `main.ts`
   * calls this once before mounting, and the router guard also awaits it on every navigation to
   * a `requiresAuth` route (getting the same promise back once it settles) rather than trusting
   * that `app.use(router)`'s own initial navigation runs after this resolves — it doesn't, so a
   * guard that skipped this await could see a stale, unauthenticated store on first load. */
  let initPromise: Promise<void> | null = null
  function init() {
    if (initPromise) return initPromise
    initPromise = (async () => {
      loading.value = true
      const {
        data: { session },
      } = await supabase.auth.getSession()
      user.value = session ? await loadAuthUser(session.user) : null
      loading.value = false
      if (user.value) useSettingsStore().touchSession()

      supabase.auth.onAuthStateChange(async (_event, session) => {
        user.value = session ? await loadAuthUser(session.user) : null
      })
    })()
    return initPromise
  }

  async function signInWithGoogle() {
    error.value = null
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/home` },
    })
    if (oauthError) error.value = oauthError.message
  }

  async function signOut() {
    await supabase.auth.signOut()
    reset()
  }

  /** Settings' "Delete account" flow: `DELETE /users/me` cascades the whole account graph
   * server-side (3.13c), then clears the local Supabase session same as `signOut()` since the
   * account (and its refresh token) no longer exists. */
  async function deleteAccount() {
    await api.delete('/users/me')
    await supabase.auth.signOut()
    reset()
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    reset,
    init,
    signInWithGoogle,
    signOut,
    deleteAccount,
  }
})
