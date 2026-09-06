<script setup lang="ts">
import { PhHeart, PhUserCircle } from '@phosphor-icons/vue'
import type { FeedComment } from '@/stores/feed'
import { formatTimeAgo } from '@/utils/timeAgo'
import { resolveAvatarUrl } from '@/utils/avatar'

const props = defineProps<{
  comment: FeedComment
  nested?: boolean
}>()

const emit = defineEmits<{ 'toggle-like': [comment: FeedComment] }>()
</script>

<template>
  <div>
    <div class="flex items-start gap-3">
      <UAvatar
        :src="resolveAvatarUrl(props.comment.authorId || props.comment.author)"
        size="sm"
        class="shrink-0 bg-white/10 text-slate-300"
      >
        <PhUserCircle :size="18" />
      </UAvatar>
      <div class="min-w-0 flex-1">
        <div class="rounded-2xl px-4 py-2.5" :class="nested ? 'bg-gray-800/40' : 'bg-gray-800/70'">
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-semibold text-white">{{ comment.author }}</span>
            <UBadge v-if="comment.isCreator" color="primary" variant="soft" size="sm" class="rounded-full text-xs">
              Creator
            </UBadge>
            <span class="text-xs text-slate-400">· {{ formatTimeAgo(comment.createdAt) }}</span>
          </div>
          <p class="mt-0.5 text-sm leading-relaxed text-slate-200">{{ comment.text }}</p>
        </div>

        <div class="mt-1.5 flex items-center gap-4 pl-4 text-xs text-slate-400">
          <button
            type="button"
            class="flex items-center gap-1.5 transition-colors hover:text-white"
            :class="comment.liked && 'text-brand-400'"
            @click="emit('toggle-like', comment)"
          >
            <PhHeart :size="16" :weight="comment.liked ? 'fill' : 'regular'" />
            {{ comment.likes }}
          </button>
          <button type="button" class="transition-colors hover:text-white">Reply</button>
          <span>{{ formatTimeAgo(comment.createdAt) }} ago</span>
        </div>
      </div>
    </div>

    <div v-if="comment.replies.length" class="mt-3 ml-11 flex flex-col gap-3">
      <FeedCommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        nested
        @toggle-like="emit('toggle-like', $event)"
      />
    </div>
  </div>
</template>
