<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import { useAdminStore } from '@/stores/admin'
import type { AdminPalApplication, PalApplicationStatus } from '@/mocks/admin'
import { resolveAvatarUrl } from '@/utils/avatar'

const adminStore = useAdminStore()
const toast = useToast()

onMounted(() => {
  adminStore.fetchPalApplications()
})

const viewing = ref<AdminPalApplication | null>(null)
const search = ref('')
const statusUpdating = ref(false)

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return adminStore.palApplications
    .filter(
      (application) =>
        !query ||
        application.displayName.toLowerCase().includes(query) ||
        application.email.toLowerCase().includes(query) ||
        application.games.some((game) => game.toLowerCase().includes(query)),
    )
    .sort((a, b) => new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime())
})

async function setStatus(status: PalApplicationStatus) {
  if (!viewing.value || statusUpdating.value) return
  const id = viewing.value.id
  statusUpdating.value = true
  try {
    await adminStore.updatePalApplicationStatus(id, status)
    viewing.value = null
  } catch (err) {
    toast.add({
      title: "Couldn't update application",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    statusUpdating.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div>
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Pal applications</h1>
      <p class="mt-1 text-sm text-slate-400">Review and approve people who want to become a Pal</p>
    </div>

    <div class="flex flex-wrap items-center justify-end gap-3">
      <UInput
        v-model="search"
        placeholder="Search applications"
        variant="subtle"
        class="w-full rounded-full sm:w-64"
        :ui="{ base: 'rounded-full' }"
      >
        <template #leading>
          <PhMagnifyingGlass :size="16" weight="bold" />
        </template>
      </UInput>
    </div>

    <div
      v-if="adminStore.palApplicationsLoading && adminStore.palApplications.length === 0"
      class="py-16 text-center text-sm text-slate-400"
    >
      Loading pal applications...
    </div>

    <UEmpty
      v-else-if="adminStore.palApplicationsError"
      title="Couldn't load pal applications"
      :description="adminStore.palApplicationsError"
      class="py-16 text-white"
    >
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="adminStore.fetchPalApplications()">Retry</UButton>
      </template>
    </UEmpty>

    <UEmpty
      v-else-if="rows.length === 0"
      title="No pending applications"
      description="New Pal applications will show up here for review."
      class="py-16 text-white"
    />

    <div v-else class="overflow-hidden rounded-xl bg-gray-800/70">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-white/10 text-slate-400">
            <th class="px-5 py-3 font-medium">Applicant</th>
            <th class="px-5 py-3 font-medium">Games</th>
            <th class="px-5 py-3 font-medium">Rank / Role</th>
            <th class="px-5 py-3 font-medium">Submitted</th>
            <th class="px-5 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="application in rows" :key="application.id" class="border-b border-white/5 last:border-0">
            <td class="px-5 py-4">
              <div class="flex items-center gap-3">
                <UAvatar :src="resolveAvatarUrl(application.id, application.avatarUrl)" size="md" class="bg-white/10" />
                <div class="min-w-0">
                  <p class="font-semibold text-white">{{ application.displayName }}</p>
                  <p class="truncate text-xs text-slate-400">{{ application.email }}</p>
                </div>
              </div>
            </td>
            <td class="px-5 py-4 text-slate-300">{{ application.games.join(', ') || '-' }}</td>
            <td class="px-5 py-4 text-slate-300">
              {{ [application.rank, application.role].filter(Boolean).join(' · ') || '-' }}
            </td>
            <td class="px-5 py-4 text-slate-300">{{ formatDate(application.submittedAt) }}</td>
            <td class="px-5 py-4 text-right">
              <button
                type="button"
                class="cursor-pointer font-medium text-brand-400 hover:text-brand-300"
                @click="viewing = application"
              >
                Review
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UModal
      :open="!!viewing"
      :title="viewing?.displayName"
      :ui="{ content: 'max-w-lg rounded-3xl' }"
      @update:open="(value: boolean) => { if (!value) viewing = null }"
    >
      <template #body>
        <div v-if="viewing" class="flex flex-col gap-4 text-sm">
          <div class="flex items-center gap-3">
            <UAvatar :src="resolveAvatarUrl(viewing.id, viewing.avatarUrl)" size="lg" class="bg-white/10" />
            <div>
              <p class="font-semibold text-white">{{ viewing.displayName }}</p>
              <p class="text-slate-400">{{ viewing.email }}</p>
            </div>
          </div>

          <p v-if="viewing.tagline" class="rounded-xl bg-gray-800/70 p-4 text-slate-300">{{ viewing.tagline }}</p>

          <div class="flex items-center justify-between border-t border-white/10 pt-3">
            <span class="text-slate-400">Games</span>
            <span class="font-medium text-white">{{ viewing.games.join(', ') || '-' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Rank / Role</span>
            <span class="font-medium text-white">
              {{ [viewing.rank, viewing.role].filter(Boolean).join(' · ') || '-' }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Languages</span>
            <span class="font-medium text-white">{{ viewing.languages.join(', ') || '-' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Payout schedule</span>
            <span class="font-medium text-white">{{ viewing.payoutSchedule }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Submitted</span>
            <span class="font-medium text-white">{{ formatDate(viewing.submittedAt) }}</span>
          </div>

          <div v-if="viewing.idFrontUrl || viewing.idBackUrl" class="flex flex-wrap gap-3 border-t border-white/10 pt-3">
            <a
              v-if="viewing.idFrontUrl"
              :href="viewing.idFrontUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="font-medium text-brand-400 hover:text-brand-300"
            >
              View ID (front)
            </a>
            <a
              v-if="viewing.idBackUrl"
              :href="viewing.idBackUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="font-medium text-brand-400 hover:text-brand-300"
            >
              View ID (back)
            </a>
          </div>

          <div class="grid grid-cols-2 gap-3 border-t border-white/10 pt-4">
            <UButton
              color="error"
              variant="soft"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('rejected')"
            >
              Reject
            </UButton>
            <UButton
              color="primary"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('approved')"
            >
              Approve
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
