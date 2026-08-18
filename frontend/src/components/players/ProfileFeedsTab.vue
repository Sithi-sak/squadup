<script setup lang="ts">
import { reactive } from 'vue'
import { PhCamera, PhChatCircle, PhDotsThree, PhFilmSlate, PhHeart, PhSmiley, PhUserCircle } from '@phosphor-icons/vue'
import type { FeedPost, PlayerSummary } from '@/stores/players'

defineProps<{ player: PlayerSummary; feed: FeedPost[] }>()

const liked = reactive<Record<string, boolean>>({})

function toggleLike(id: string) {
  liked[id] = !liked[id]
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
          :ui="{ base: 'rounded-full' }"
        />
      </div>
      <div class="mt-3 flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhCamera :size="16" weight="bold" />
            Photo
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhFilmSlate :size="16" weight="bold" />
            Clip
          </UButton>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhSmiley :size="16" weight="bold" />
            Emoji
          </UButton>
        </div>
        <UButton color="primary" class="rounded-full px-6">Post</UButton>
      </div>
    </div>

    <p v-if="feed.length === 0" class="py-10 text-center text-sm text-slate-400">
      {{ player.displayName }} hasn't posted anything yet.
    </p>

    <div v-for="post in feed" :key="post.id" class="rounded-xl bg-gray-800/70 p-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-3">
          <UAvatar size="md" class="shrink-0 bg-white/10 text-slate-300">
            <PhUserCircle :size="20" />
          </UAvatar>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-semibold text-white">{{ player.displayName }}</span>
              <UBadge color="neutral" variant="soft" size="sm" class="rounded-full">Pal 2</UBadge>
            </div>
            <p class="text-xs text-slate-400">@{{ player.id }} · {{ post.timeAgo }}</p>
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
          :class="liked[post.id] && 'text-brand-400'"
          @click="toggleLike(post.id)"
        >
          <PhHeart :size="18" :weight="liked[post.id] ? 'fill' : 'regular'" />
          {{ post.likes + (liked[post.id] ? 1 : 0) }}
        </button>
        <span class="flex items-center gap-1.5">
          <PhChatCircle :size="18" />
          {{ post.comments }}
        </span>
      </div>
    </div>
  </div>
</template>
