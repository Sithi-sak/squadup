import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', () => {
  const isMobileNavOpen = ref(false)
  const isGlobalLoading = ref(false)

  function toggleMobileNav(value?: boolean) {
    isMobileNavOpen.value = value ?? !isMobileNavOpen.value
  }

  return { isMobileNavOpen, isGlobalLoading, toggleMobileNav }
})
