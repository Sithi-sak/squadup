<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhArrowLeft } from '@phosphor-icons/vue'
import AuthCardShell from '@/components/auth/AuthCardShell.vue'

const email = ref('')
const sent = ref(false)
const loading = ref(false)

const canSubmit = computed(() => email.value.trim().length > 3)

const fieldUi = {
  base: 'bg-white/5 px-5 py-3 text-sm ring-1 ring-inset ring-white/10 focus-visible:ring-2 focus-visible:ring-brand-600',
}

function handleSubmit() {
  if (!canSubmit.value) return
  loading.value = true
  // TODO: wire to Supabase Auth password recovery in Phase 2
  setTimeout(() => {
    loading.value = false
    sent.value = true
  }, 500)
}
</script>

<template>
  <AuthCardShell>
    <h2 class="text-2xl font-bold text-white">Forgot your password?</h2>
    <p class="mt-2 text-sm text-slate-400">
      Enter the email linked to your account and we'll send you a secure reset link.
    </p>

    <form class="mt-6 flex flex-col gap-2" @submit.prevent="handleSubmit">
      <label for="forgot-email" class="text-sm font-medium text-white">Email</label>
      <UInput
        id="forgot-email"
        v-model="email"
        type="email"
        placeholder="ari@squadup.gg"
        autocomplete="email"
        variant="subtle"
        size="xl"
        :ui="fieldUi"
      />

      <UButton
        type="submit"
        color="primary"
        block
        :loading="loading"
        :disabled="!canSubmit"
        class="mt-4 justify-center rounded-full py-3 text-base"
      >
        {{ sent ? 'Resend link' : 'Send reset link' }}
      </UButton>
    </form>

    <p
      v-if="sent"
      class="mt-3 rounded-full bg-brand-600/10 px-4 py-3 text-center text-sm text-brand-300"
    >
      Check spam if you don't see the link
    </p>

    <router-link
      to="/login"
      class="mt-6 flex items-center justify-center gap-2 text-sm font-medium text-slate-300 hover:text-white"
    >
      <PhArrowLeft :size="16" />
      Back to log in
    </router-link>
  </AuthCardShell>
</template>
