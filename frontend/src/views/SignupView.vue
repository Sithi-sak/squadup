<script setup lang="ts">
import { computed, ref } from 'vue'
import googleIcon from '@/assets/google.svg'
import AuthSplitShell from '@/components/auth/AuthSplitShell.vue'
import PostSignupRoleModal from '@/components/auth/PostSignupRoleModal.vue'

const identifier = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const showRoleModal = ref(false)

const passwordsMatch = computed(
  () => password.value.length > 0 && password.value === confirmPassword.value,
)
const canSubmit = computed(() => identifier.value.trim().length > 0 && passwordsMatch.value)

const fieldUi = {
  base: 'bg-white/5 px-5 py-3.5 text-sm ring-1 ring-inset ring-white/10 focus-visible:ring-2 focus-visible:ring-brand-600',
}

function handleSignup() {
  if (!canSubmit.value) return
  loading.value = true
  // TODO: wire to Supabase Auth in Phase 2
  setTimeout(() => {
    loading.value = false
    showRoleModal.value = true
  }, 500)
}
</script>

<template>
  <AuthSplitShell>
    <h2 class="text-3xl font-bold text-white">Create your account</h2>

    <form class="mt-8 flex flex-col gap-4" @submit.prevent="handleSignup">
      <UInput
        v-model="identifier"
        type="text"
        placeholder="Phone/Email"
        autocomplete="username"
        variant="subtle"
        size="xl"
        :ui="fieldUi"
      />

      <UInput
        v-model="password"
        type="password"
        placeholder="Password"
        autocomplete="new-password"
        variant="subtle"
        size="xl"
        :ui="fieldUi"
      />

      <div class="flex flex-col gap-2">
        <UInput
          v-model="confirmPassword"
          type="password"
          placeholder="Re-enter password"
          autocomplete="new-password"
          variant="subtle"
          size="xl"
          :ui="fieldUi"
        />
        <span v-if="confirmPassword && !passwordsMatch" class="text-xs text-red-400">
          Passwords don't match.
        </span>
      </div>

      <UButton
        type="submit"
        color="primary"
        block
        :loading="loading"
        :disabled="!canSubmit"
        class="justify-center rounded-full py-3.5 text-base"
      >
        Create account
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
      class="justify-center gap-2.5 rounded-full bg-white/5 py-3.5 text-base text-white hover:bg-white/10"
    >
      <img :src="googleIcon" alt="" class="h-4.5 w-4.5" />
      Continue with Google
    </UButton>

    <p class="mt-6 text-center text-sm text-slate-400">
      Already have an account?
      <router-link to="/login" class="font-medium text-white underline">Login here</router-link>
    </p>
  </AuthSplitShell>

  <PostSignupRoleModal v-model:open="showRoleModal" />
</template>
