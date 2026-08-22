<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import googleIcon from '@/assets/google.svg'
import AuthSplitShell from '@/components/auth/AuthSplitShell.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const identifier = ref('')
const password = ref('')
const loading = ref(false)
const googleLoading = ref(false)

const fieldUi = {
  base: 'bg-white/5 px-5 py-3.5 text-sm ring-1 ring-inset ring-white/10 focus-visible:ring-2 focus-visible:ring-brand-600',
}

function handleLogin() {
  loading.value = true
  // TODO: wire email/password to Supabase Auth (2.5 only wires Google)
  setTimeout(() => {
    loading.value = false
    router.push('/players')
  }, 500)
}

async function handleGoogleLogin() {
  googleLoading.value = true
  await authStore.signInWithGoogle()
  googleLoading.value = false
}
</script>

<template>
  <AuthSplitShell>
    <h2 class="text-3xl font-bold text-white">Log in or sign up</h2>

    <form class="mt-8 flex flex-col gap-4" @submit.prevent="handleLogin">
      <UInput
        v-model="identifier"
        type="text"
        placeholder="Phone/Email"
        autocomplete="username"
        variant="subtle"
        size="xl"
        :ui="fieldUi"
      />

      <div class="flex flex-col gap-2">
        <UInput
          v-model="password"
          type="password"
          placeholder="Password"
          autocomplete="current-password"
          variant="subtle"
          size="xl"
          :ui="fieldUi"
        />
        <router-link to="/forgot-password" class="self-end text-sm text-brand-300 hover:underline">
          Forgot password?
        </router-link>
      </div>

      <UButton
        type="submit"
        color="primary"
        block
        :loading="loading"
        class="justify-center rounded-full py-3.5 text-base"
      >
        Login
      </UButton>
    </form>

    <div class="my-6 flex items-center gap-3">
      <div class="h-px flex-1 bg-white/10" />
      <span class="text-xs text-slate-400">Or continue with</span>
      <div class="h-px flex-1 bg-white/10" />
    </div>

    <UButton
      color="neutral"
      variant="soft"
      block
      :loading="googleLoading"
      class="justify-center gap-2.5 rounded-full bg-white/5 py-3.5 text-base text-white hover:bg-white/10"
      @click="handleGoogleLogin"
    >
      <img :src="googleIcon" alt="" class="h-4.5 w-4.5" />
      Continue with Google
    </UButton>

    <p class="mt-6 text-center text-sm text-slate-400">
      Don't have an account?
      <router-link to="/signup" class="font-medium text-white underline">
        Create one here
      </router-link>
    </p>
  </AuthSplitShell>
</template>
