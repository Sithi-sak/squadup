<script setup lang="ts">
import { ref, watch } from 'vue'
import { PhCamera, PhChatCircle, PhDotsThree, PhFilmSlate, PhHeart, PhSmiley, PhUserCircle } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import CreatePostModal from '@/components/modals/CreatePostModal.vue'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import type { PlayerSummary } from '@/stores/players'
import { formatTimeAgo } from '@/utils/timeAgo'

const props = defineProps<{ player: PlayerSummary; feed: FeedPost[] }>()

const feedStore = useFeedStore()
const toast = useToast()

/** Local copy so a like toggle can patch in place without the parent's `profile.feed` (loaded
 * once via `usePlayerProfileData`) needing its own mutation path. */
const localFeed = ref<FeedPost[]>([...props.feed])
watch(
  () => props.feed,
  (feed) => (localFeed.value = [...feed]),
)

const createPostOpen = ref(false)

async function toggleLike(post: FeedPost) {
  try {
    const updated = await feedStore.toggleLike(post)
    const index = localFeed.value.findIndex((p) => p.id === updated.id)
    if (index !== -1) localFeed.value[index] = updated
  } catch (err) {
    toast.add({
      title: 'Could not update like',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="rounded-xl bg-gray-800/70 p-4">
      <div class="flex items-center gap-3">
        <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
          <PhUserCircle :size="20" />
        </UAvatar>
        <UInput
          placeholder="Share something with your squad..."
          variant="subtle"
          class="w-full rounded-full"
          :ui="{ base: 'rounded-full cursor-pointer' }"
          readonly
          @click="createPostOpen = true"
        />
      </div>
      <div class="mt-3 flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="createPostOpen = true">
            <PhCamera :size="16" weight="bold" />
            Photo
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="createPostOpen = true">
            <PhFilmSlate :size="16" weight="bold" />
            Clip
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full" @click="createPostOpen = true">
            <PhSmiley :size="16" weight="bold" />
            Emoji
          </UButton>
        </div>
        <UButton color="primary" class="rounded-full px-6" @click="createPostOpen = true">Post</UButton>
      </div>
    </div>

    <CreatePostModal v-model:open="createPostOpen" />

    <p v-if="localFeed.length === 0" class="py-10 text-center text-sm text-slate-400">
      {{ player.displayName }} hasn't posted anything yet.
    </p>

    <div v-for="post in localFeed" :key="post.id" class="rounded-xl bg-gray-800/70 p-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-3">
          <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
            <PhUserCircle :size="20" />
          </UAvatar>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-semibold text-white">{{ player.displayName }}</span>
              <UBadge v-if="post.tier" color="neutral" variant="soft" size="sm" class="rounded-full">
                {{ post.tier }}
              </UBadge>
            </div>
            <p class="text-xs text-slate-400">@{{ player.id }} · {{ formatTimeAgo(post.createdAt) }}</p>
          </div>
        </div>
        <UButton color="neutral" variant="ghost" square :ui="{ base: 'rounded-full' }" aria-label="Post options">
          <PhDotsThree :size="18" weight="bold" />
        </UButton>
      </div>

      <p class="mt-3 text-sm leading-relaxed text-slate-200">{{ post.text }}</p>

      <div v-if="post.hasImage" class="mt-3 aspect-video w-full rounded-lg bg-white/5 ring-1 ring-inset ring-white/10" />

      <div class="mt-3 flex items-center gap-4 text-sm text-slate-400">
        <button
          type="button"
          class="flex items-center gap-1.5 transition-colors hover:text-white"
          :class="post.liked && 'text-brand-400'"
          @click="toggleLike(post)"
        >
          <PhHeart :size="18" :weight="post.liked ? 'fill' : 'regular'" />
          {{ post.likes }}
        </button>
        <span class="flex items-center gap-1.5">
          <PhChatCircle :size="18" />
          {{ post.comments }}
        </span>
      </div>
    </div>
  </div>
</template>
