import { ref } from 'vue'
import { defineStore } from 'pinia'

/** Mock-only credential, known solely to the admin, standing in until real admin auth ships
 * (Phase 2 Supabase auth + the 3.8 admin endpoints). There is exactly one admin account and no
 * signup flow for it, so `/admin` gates on this instead of the regular `useAuthStore` user. */
const ADMIN_EMAIL = 'admin@squadup.gg'
const ADMIN_PASSWORD = 'SquadUp-Admin-26'

const SESSION_KEY = 'squadup-admin-session'

export const useAdminStore = defineStore('admin', () => {
  const isAuthenticated = ref(sessionStorage.getItem(SESSION_KEY) === '1')
  const error = ref<string | null>(null)

  function login(email: string, password: string) {
    const matches = email.trim().toLowerCase() === ADMIN_EMAIL && password === ADMIN_PASSWORD
    if (matches) {
      isAuthenticated.value = true
      error.value = null
      sessionStorage.setItem(SESSION_KEY, '1')
    } else {
      error.value = 'Incorrect email or password.'
    }
    return matches
  }

  function logout() {
    isAuthenticated.value = false
    sessionStorage.removeItem(SESSION_KEY)
  }

  return { isAuthenticated, error, login, logout }
})
