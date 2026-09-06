<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import { useAdminStore } from '@/stores/admin'
import type { AdminFlaggedPlayer, FlaggedPlayerStatus } from '@/mocks/admin'
import { resolveAvatarUrl } from '@/utils/avatar'

const adminStore = useAdminStore()
const toast = useToast()

onMounted(() => {
  adminStore.fetchFlaggedPlayers()
})

const viewing = ref<AdminFlaggedPlayer | null>(null)
const search = ref('')
const statusUpdating = ref(false)
const banUpdating = ref(false)

const filters = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'reviewing', label: 'Reviewing' },
  { key: 'actioned', label: 'Actioned' },
  { key: 'dismissed', label: 'Dismissed' },
] as const

const activeFilter = ref<(typeof filters)[number]['key']>('all')

const statusMeta: Record<FlaggedPlayerStatus, { label: string; class: string }> = {
  pending: { label: 'Pending', class: 'text-amber-400' },
  reviewing: { label: 'Reviewing', class: 'text-sky-400' },
  actioned: { label: 'Actioned', class: 'text-red-400' },
  dismissed: { label: 'Dismissed', class: 'text-slate-400' },
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  return adminStore.flaggedPlayers
    .filter((flag) => activeFilter.value === 'all' || flag.status === activeFilter.value)
    .filter((flag) => !query || flag.displayName.toLowerCase().includes(query) || flag.reason.toLowerCase().includes(query))
    .sort((a, b) => new Date(b.reportedAt).getTime() - new Date(a.reportedAt).getTime())
})

async function setStatus(status: FlaggedPlayerStatus) {
  if (!viewing.value || statusUpdating.value) return
  const id = viewing.value.id
  statusUpdating.value = true
  try {
    const updated = await adminStore.updateFlaggedPlayerStatus(id, status)
    viewing.value = updated
  } catch (err) {
    toast.add({
      title: "Couldn't update status",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    statusUpdating.value = false
  }
}

async function toggleBan() {
  if (!viewing.value || banUpdating.value) return
  const { playerId, isBanned } = viewing.value
  banUpdating.value = true
  try {
    const updated = await adminStore.banPlayer(playerId, !isBanned)
    viewing.value = updated ?? { ...viewing.value, isBanned: !isBanned }
  } catch (err) {
    toast.add({
      title: "Couldn't update ban status",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    banUpdating.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div>
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Flagged players</h1>
      <p class="mt-1 text-sm text-slate-400">Review reports and take action on Pal profiles</p>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <UButton
          v-for="filter in filters"
          :key="filter.key"
          :color="activeFilter === filter.key ? 'primary' : 'neutral'"
          :variant="activeFilter === filter.key ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
        </UButton>
      </div>
      <UInput
        v-model="search"
        placeholder="Search flagged players"
        variant="subtle"
        class="w-full rounded-full sm:w-64"
        :ui="{ base: 'rounded-full' }"
      >
        <template #leading>
          <PhMagnifyingGlass :size="16" weight="bold" />
        </template>
      </UInput>
    </div>

    <div v-if="adminStore.flaggedPlayersLoading && adminStore.flaggedPlayers.length === 0" class="py-16 text-center text-sm text-slate-400">
      Loading flagged players...
    </div>

    <UEmpty
      v-else-if="adminStore.flaggedPlayersError"
      title="Couldn't load flagged players"
      :description="adminStore.flaggedPlayersError"
      class="py-16 text-white"
    >
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="adminStore.fetchFlaggedPlayers()">Retry</UButton>
      </template>
    </UEmpty>

    <UEmpty
      v-else-if="rows.length === 0"
      title="No flagged players found"
      description="Try a different filter or search term."
      class="py-16 text-white"
    />

    <div v-else class="overflow-hidden rounded-xl bg-gray-800/70">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-white/10 text-slate-400">
            <th class="px-5 py-3 font-medium">Player</th>
            <th class="px-5 py-3 font-medium">Reason</th>
            <th class="px-5 py-3 font-medium">Reports</th>
            <th class="px-5 py-3 font-medium">Reported</th>
            <th class="px-5 py-3 font-medium">Status</th>
            <th class="px-5 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="flag in rows" :key="flag.id" class="border-b border-white/5 last:border-0">
            <td class="px-5 py-4">
              <div class="flex items-center gap-3">
                <UAvatar :src="resolveAvatarUrl(flag.playerId, flag.avatarUrl)" size="md" class="bg-white/10" />
                <div class="flex items-center gap-2">
                  <p class="font-semibold text-white">{{ flag.displayName }}</p>
                  <span v-if="flag.isBanned" class="rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-400">
                    Banned
                  </span>
                </div>
              </div>
            </td>
            <td class="px-5 py-4 text-slate-300">{{ flag.reason }}</td>
            <td class="px-5 py-4 text-slate-300">{{ flag.reportCount }}</td>
            <td class="px-5 py-4 text-slate-300">{{ formatDate(flag.reportedAt) }}</td>
            <td class="px-5 py-4 font-medium" :class="statusMeta[flag.status].class">
              {{ statusMeta[flag.status].label }}
            </td>
            <td class="px-5 py-4 text-right">
              <button
                type="button"
                class="cursor-pointer font-medium text-brand-400 hover:text-brand-300"
                @click="viewing = flag"
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
            <UAvatar :src="resolveAvatarUrl(viewing.playerId, viewing.avatarUrl)" size="lg" class="bg-white/10" />
            <div>
              <p class="font-semibold text-white">{{ viewing.displayName }}</p>
              <p class="text-slate-400">{{ viewing.reportCount }} report{{ viewing.reportCount > 1 ? 's' : '' }} · reported by {{ viewing.reportedBy }}</p>
            </div>
          </div>

          <div class="flex items-center justify-between border-t border-white/10 pt-3">
            <span class="text-slate-400">Reason</span>
            <span class="font-medium text-white">{{ viewing.reason }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Reported</span>
            <span class="font-medium text-white">{{ formatDate(viewing.reportedAt) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-slate-400">Status</span>
            <span class="font-medium" :class="statusMeta[viewing.status].class">{{ statusMeta[viewing.status].label }}</span>
          </div>

          <p class="rounded-xl bg-gray-800/70 p-4 text-slate-300">{{ viewing.details }}</p>

          <div class="grid grid-cols-3 gap-3 border-t border-white/10 pt-4">
            <UButton
              color="neutral"
              variant="soft"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('dismissed')"
            >
              Dismiss
            </UButton>
            <UButton
              color="primary"
              variant="soft"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('reviewing')"
            >
              Reviewing
            </UButton>
            <UButton
              color="error"
              size="sm"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating"
              @click="setStatus('actioned')"
            >
              Take action
            </UButton>
          </div>

          <div class="flex items-center justify-between gap-3 border-t border-white/10 pt-4">
            <div>
              <p class="font-medium text-white">{{ viewing.isBanned ? 'Player is banned' : 'Ban this player' }}</p>
              <p class="text-slate-400">Hides them from Browse Players and their public profile.</p>
            </div>
            <UButton
              :color="viewing.isBanned ? 'neutral' : 'error'"
              :variant="viewing.isBanned ? 'soft' : 'solid'"
              size="sm"
              class="shrink-0 rounded-full"
              :loading="banUpdating"
              :disabled="banUpdating"
              @click="toggleBan"
            >
              {{ viewing.isBanned ? 'Unban' : 'Ban' }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
