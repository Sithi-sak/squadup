<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhArrowSquareOut, PhMagnifyingGlass, PhTrash } from '@phosphor-icons/vue'
import ConfirmModal from '@/components/modals/ConfirmModal.vue'
import { useAdminStore } from '@/stores/admin'
import type { AdminPostReport, FlaggedPlayerStatus } from '@/mocks/admin'
import { resolveAvatarUrl } from '@/utils/avatar'

/** Reported posts tab (4.77e). Same queue shape as `AdminFlaggedPlayersPanel`, keyed on posts
 * instead of Pals, with "Remove post" as the action that actually does something. */
const adminStore = useAdminStore()
const toast = useToast()

onMounted(() => {
  adminStore.fetchPostReports()
})

const viewing = ref<AdminPostReport | null>(null)
const search = ref('')
const statusUpdating = ref(false)
const removeConfirmOpen = ref(false)
const removing = ref(false)

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
  return adminStore.postReports
    .filter((report) => activeFilter.value === 'all' || report.status === activeFilter.value)
    .filter(
      (report) =>
        !query ||
        report.authorName.toLowerCase().includes(query) ||
        report.reason.toLowerCase().includes(query) ||
        (report.postText ?? '').toLowerCase().includes(query),
    )
    .sort((a, b) => new Date(b.reportedAt).getTime() - new Date(a.reportedAt).getTime())
})

function authorRoute(report: AdminPostReport) {
  return report.authorId ? { name: 'user-profile', params: { id: report.authorId } } : undefined
}

async function setStatus(status: FlaggedPlayerStatus) {
  if (!viewing.value || statusUpdating.value) return
  const id = viewing.value.id
  statusUpdating.value = true
  try {
    viewing.value = await adminStore.updatePostReportStatus(id, status)
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

async function removePost() {
  removeConfirmOpen.value = false
  if (!viewing.value || removing.value) return
  const id = viewing.value.id
  removing.value = true
  try {
    viewing.value = await adminStore.removeReportedPost(id)
    toast.add({
      title: 'Post removed',
      description: 'The author was notified and every open report on it is marked actioned.',
      color: 'success',
    })
  } catch (err) {
    toast.add({
      title: "Couldn't remove the post",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    removing.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div>
      <h1 class="text-2xl font-bold text-white sm:text-3xl">Reported posts</h1>
      <p class="mt-1 text-sm text-slate-400">Review reports on feed posts and remove what breaks the rules</p>
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
        placeholder="Search reported posts"
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
      v-if="adminStore.postReportsLoading && adminStore.postReports.length === 0"
      class="py-16 text-center text-sm text-slate-400"
    >
      Loading reported posts...
    </div>

    <UEmpty
      v-else-if="adminStore.postReportsError"
      title="Couldn't load reported posts"
      :description="adminStore.postReportsError"
      class="py-16 text-white"
    >
      <template #actions>
        <UButton color="primary" class="rounded-full" @click="adminStore.fetchPostReports()">Retry</UButton>
      </template>
    </UEmpty>

    <UEmpty
      v-else-if="rows.length === 0"
      title="No reported posts found"
      description="Try a different filter or search term."
      class="py-16 text-white"
    />

    <div v-else class="overflow-x-auto rounded-xl bg-gray-800/70">
      <table class="w-full text-left text-sm">
        <thead>
          <tr class="border-b border-white/10 text-slate-400">
            <th class="px-5 py-3 font-medium">Post</th>
            <th class="px-5 py-3 font-medium">Reason</th>
            <th class="px-5 py-3 font-medium">Reports</th>
            <th class="px-5 py-3 font-medium">Reported</th>
            <th class="px-5 py-3 font-medium">Status</th>
            <th class="px-5 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="report in rows" :key="report.id" class="border-b border-white/5 last:border-0">
            <td class="px-5 py-4">
              <div class="flex items-center gap-3">
                <UAvatar
                  :src="resolveAvatarUrl(report.authorId ?? report.id, report.authorAvatarUrl)"
                  size="md"
                  class="shrink-0 bg-white/10"
                />
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <p class="font-semibold text-white">{{ report.authorName }}</p>
                    <span
                      v-if="!report.postId"
                      class="rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-400"
                    >
                      Removed
                    </span>
                  </div>
                  <p class="max-w-xs truncate text-slate-400">{{ report.postText || 'No text' }}</p>
                </div>
              </div>
            </td>
            <td class="px-5 py-4 text-slate-300">{{ report.reason }}</td>
            <td class="px-5 py-4 text-slate-300">{{ report.reportCount }}</td>
            <td class="px-5 py-4 text-slate-300">{{ formatDate(report.reportedAt) }}</td>
            <td class="px-5 py-4 font-medium" :class="statusMeta[report.status].class">
              {{ statusMeta[report.status].label }}
            </td>
            <td class="px-5 py-4 text-right">
              <button
                type="button"
                class="cursor-pointer font-medium text-brand-400 hover:text-brand-300"
                @click="viewing = report"
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
      title="Reported post"
      :ui="{ content: 'max-w-lg rounded-3xl' }"
      @update:open="(value: boolean) => { if (!value) viewing = null }"
    >
      <template #body>
        <div v-if="viewing" class="flex flex-col gap-4 text-sm">
          <component
            :is="authorRoute(viewing) ? 'router-link' : 'div'"
            :to="authorRoute(viewing)"
            class="flex w-fit items-center gap-3"
            :class="authorRoute(viewing) && 'hover:underline'"
          >
            <UAvatar
              :src="resolveAvatarUrl(viewing.authorId ?? viewing.id, viewing.authorAvatarUrl)"
              size="lg"
              class="bg-white/10"
            />
            <div>
              <p class="font-semibold text-white">{{ viewing.authorName }}</p>
              <!-- Same as Flagged players: one reporter is worth naming, past that the count is the
                   signal and `reportedBy` only holds whoever filed first. -->
              <p class="text-slate-400">
                {{ viewing.reportCount }} report{{ viewing.reportCount > 1 ? 's' : '' }}
                <template v-if="viewing.reportCount === 1"> · reported by {{ viewing.reportedBy }}</template>
              </p>
            </div>
          </component>

          <div class="flex flex-col gap-3 rounded-xl bg-gray-800/70 p-4">
            <p class="whitespace-pre-line text-slate-200">{{ viewing.postText || 'This post has no text.' }}</p>
            <img
              v-if="viewing.postImageUrl"
              :src="viewing.postImageUrl"
              alt=""
              class="max-h-60 w-full rounded-lg bg-slate-950 object-contain"
            />
            <a
              v-if="viewing.postId"
              :href="`/feed/${viewing.postId}`"
              target="_blank"
              rel="noopener"
              class="flex w-fit items-center gap-1.5 font-medium text-brand-400 hover:text-brand-300"
            >
              Open post
              <PhArrowSquareOut :size="14" weight="bold" />
            </a>
            <p v-else class="font-medium text-red-400">This post has been removed.</p>
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
            <span class="font-medium" :class="statusMeta[viewing.status].class">
              {{ statusMeta[viewing.status].label }}
            </span>
          </div>

          <p v-if="viewing.details" class="rounded-xl bg-gray-800/70 p-4 text-slate-300">{{ viewing.details }}</p>

          <div class="grid grid-cols-3 gap-3 border-t border-white/10 pt-4">
            <UButton
              color="neutral"
              variant="soft"
              size="md"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating || removing"
              @click="setStatus('dismissed')"
            >
              Dismiss
            </UButton>
            <UButton
              color="primary"
              variant="soft"
              size="md"
              block
              class="rounded-full"
              :loading="statusUpdating"
              :disabled="statusUpdating || removing"
              @click="setStatus('reviewing')"
            >
              Reviewing
            </UButton>
            <UButton
              color="error"
              size="md"
              block
              class="rounded-full"
              :loading="removing"
              :disabled="!viewing.postId || statusUpdating || removing"
              @click="removeConfirmOpen = true"
            >
              Remove post
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <ConfirmModal
      v-model:open="removeConfirmOpen"
      :icon="PhTrash"
      title="Remove this post?"
      description="The post, its comments and its likes are deleted for everyone, and the author gets a moderation notice. This can't be undone."
      confirm-label="Remove"
      destructive
      @confirm="removePost"
    />
  </div>
</template>
