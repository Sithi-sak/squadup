<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthCardShell from '@/components/auth/AuthCardShell.vue'

const router = useRouter()

const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const strength = computed(() => {
  const value = password.value
  let score = 0
  if (value.length >= 8) score++
  if (/[0-9]/.test(value)) score++
  if (/[^A-Za-z0-9]/.test(value)) score++
  if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score++
  return score
})

const strengthLabel = computed(
  () => ['Too weak', 'Weak', 'Fair', 'Good', 'Strong'][strength.value],
)

const passwordsMatch = computed(
  () => password.value.length > 0 && password.value === confirmPassword.value,
)

const canSubmit = computed(() => passwordsMatch.value && strength.value >= 2)

const fieldUi = {
  base: 'bg-white/5 px-5 py-3 text-sm ring-1 ring-inset ring-white/10 focus-visible:ring-2 focus-visible:ring-brand-600',
}

function handleSubmit() {
  if (!canSubmit.value) return
  loading.value = true
  // TODO: wire to Supabase Auth password update in Phase 2
  setTimeout(() => {
    loading.value = false
    router.push('/login')
  }, 500)
}
</script>

<template>
  <AuthCardShell>
    <h2 class="text-2xl font-bold text-white">Set a new password</h2>
    <p class="mt-2 text-sm text-slate-400">Choose a strong password you don't use anywhere else.</p>

    <form class="mt-6 flex flex-col gap-5" @submit.prevent="handleSubmit">
      <div class="flex flex-col gap-2">
        <label for="new-password" class="text-sm font-medium text-white">New password</label>
        <UInput
          id="new-password"
          v-model="password"
          type="password"
          autocomplete="new-password"
          variant="subtle"
          size="xl"
          :ui="fieldUi"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label for="confirm-password" class="text-sm font-medium text-white">Confirm password</label>
        <UInput
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          variant="subtle"
          size="xl"
          :ui="fieldUi"
        />

        <div v-if="password" class="mt-1 flex gap-1.5">
          <div
            v-for="segment in 4"
            :key="segment"
            class="h-1 flex-1 rounded-full"
            :class="segment <= strength ? 'bg-brand-500' : 'bg-white/10'"
          />
        </div>
        <p v-if="password" class="text-xs text-slate-400">
          {{ strengthLabel }} · use 8+ characters with a number and symbol.
        </p>
        <p v-if="confirmPassword && !passwordsMatch" class="text-xs text-red-400">
          Passwords don't match.
        </p>
      </div>

      <UButton
        type="submit"
        color="primary"
        block
        :loading="loading"
        :disabled="!canSubmit"
        class="justify-center rounded-full py-3 text-base"
      >
        Update password
      </UButton>
    </form>
  </AuthCardShell>
</template>
