<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { PhCaretLeft, PhUserCircle } from '@phosphor-icons/vue'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FollowUser } from '@/stores/feed'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{ userId: string; initialTab?: 'followers' | 'following' }>()
const emit = defineEmits<{ back: [] }>()

const authStore = useAuthStore()
const feedStore = useFeedStore()

const tabs = [
  { key: 'followers', label: 'Followers' },
  { key: 'following', label: 'Following' },
] as const

type TabKey = (typeof tabs)[number]['key']

const activeTab = ref<TabKey>(props.initialTab ?? 'followers')
const usersByTab = ref<Record<TabKey, FollowUser[] | null>>({ followers: null, following: null })
const loading = ref(false)
const pendingIds = reactive(new Set<string>())

const list = computed(() => usersByTab.value[activeTab.value])

async function loadTab(tab: TabKey) {
  loading.value = true
  try {
    usersByTab.value[tab] =
      tab === 'followers' ? await feedStore.fetchFollowers(props.userId) : await feedStore.fetchFollowingUsers(props.userId)
  } catch {
    usersByTab.value[tab] = []
  } finally {
    loading.value = false
  }
}

onMounted(() => loadTab(activeTab.value))
watch(activeTab, (tab) => {
  if (!usersByTab.value[tab]) loadTab(tab)
})

async function toggleFollow(user: FollowUser) {
  if (pendingIds.has(user.id)) return
  pendingIds.add(user.id)
  try {
    const result = await feedStore.toggleFollow(user.id, user.following)
    user.following = result.following
    // Own Following list: dropping someone from it should make them disappear immediately
    // rather than sit there showing a stale "Follow" button.
    if (activeTab.value === 'following' && props.userId === authStore.user?.id && !result.following) {
      usersByTab.value.following = (usersByTab.value.following ?? []).filter((u) => u.id !== user.id)
    }
  } finally {
    pendingIds.delete(user.id)
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <button
      type="button"
      class="flex w-fit items-center gap-1 text-sm text-slate-400 transition-colors hover:text-white"
      @click="emit('back')"
    >
      <PhCaretLeft :size="16" weight="bold" />
      Back to profile
    </button>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <div class="flex items-center gap-2">
        <UButton
          v-for="tab in tabs"
          :key="tab.key"
          :color="activeTab === tab.key ? 'primary' : 'neutral'"
          :variant="activeTab === tab.key ? 'solid' : 'soft'"
          size="sm"
          class="rounded-full"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </UButton>
      </div>

      <div class="mt-4 flex flex-col divide-y divide-white/10">
        <template v-if="loading && !list">
          <div v-for="n in 4" :key="n" class="flex items-center gap-3 py-3">
            <USkeleton class="h-10 w-10 shrink-0 rounded-full" />
            <div class="flex-1 space-y-1.5">
              <USkeleton class="h-3.5 w-32" />
              <USkeleton class="h-3 w-20" />
            </div>
          </div>
        </template>

        <p v-else-if="list && list.length === 0" class="py-10 text-center text-sm text-slate-400">
          {{ activeTab === 'followers' ? 'No followers yet.' : 'Not following anyone yet.' }}
        </p>

        <template v-else>
          <div v-for="user in list" :key="user.id" class="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
            <UAvatar :src="resolveAvatarUrl(user.id, user.avatarUrl)" size="md" class="shrink-0 bg-white/10 text-slate-300">
              <PhUserCircle :size="20" />
            </UAvatar>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <p class="truncate text-sm font-medium text-white">{{ user.displayName }}</p>
                <UBadge v-if="user.tier" color="neutral" variant="soft" size="sm" class="rounded-full text-xs">
                  {{ user.tier }}
                </UBadge>
              </div>
              <p v-if="user.handle" class="truncate text-xs text-slate-400">{{ user.handle }}</p>
            </div>
            <UButton
              v-if="user.id !== authStore.user?.id"
              :color="user.following ? 'neutral' : 'primary'"
              :variant="user.following ? 'soft' : 'solid'"
              size="sm"
              class="shrink-0 rounded-full"
              :loading="pendingIds.has(user.id)"
              @click="toggleFollow(user)"
            >
              {{ user.following ? 'Following' : 'Follow' }}
            </UButton>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
