<script setup lang="ts">
import { reactive } from 'vue'
import { PhHeart, PhUserCircle } from '@phosphor-icons/vue'
import type { FeedComment } from '@/mocks/feed'

defineProps<{
  id: string
  author: string
  timeAgo: string
  text: string
  likes: number
  isCreator?: boolean
  replies?: FeedComment[]
  nested?: boolean
}>()

const liked = reactive<Record<string, boolean>>({})
function toggleLike(id: string) {
  liked[id] = !liked[id]
}
</script>

<template>
  <div>
    <div class="flex items-start gap-3">
      <UAvatar size="sm" class="shrink-0 bg-white/10 text-slate-300">
        <PhUserCircle :size="18" />
      </UAvatar>
      <div class="min-w-0 flex-1">
        <div class="rounded-2xl px-4 py-2.5" :class="nested ? 'bg-gray-800/40' : 'bg-gray-800/70'">
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-semibold text-white">{{ author }}</span>
            <UBadge v-if="isCreator" color="primary" variant="soft" size="sm" class="rounded-full text-xs">
              Creator
            </UBadge>
            <span class="text-xs text-slate-400">· {{ timeAgo }}</span>
          </div>
          <p class="mt-0.5 text-sm leading-relaxed text-slate-200">{{ text }}</p>
        </div>

        <div class="mt-1.5 flex items-center gap-4 pl-4 text-xs text-slate-400">
          <button
            type="button"
            class="flex items-center gap-1.5 transition-colors hover:text-white"
            :class="liked[id] && 'text-brand-400'"
            @click="toggleLike(id)"
          >
            <PhHeart :size="16" :weight="liked[id] ? 'fill' : 'regular'" />
            {{ likes + (liked[id] ? 1 : 0) }}
          </button>
          <button type="button" class="transition-colors hover:text-white">Reply</button>
          <span>{{ timeAgo }} ago</span>
        </div>
      </div>
    </div>

    <div v-if="replies?.length" class="mt-3 ml-11 flex flex-col gap-3">
      <FeedCommentItem
        v-for="reply in replies"
        :key="reply.id"
        :id="reply.id"
        :author="reply.author"
        :time-ago="reply.timeAgo"
        :text="reply.text"
        :likes="reply.likes"
        :is-creator="reply.isCreator"
        nested
      />
    </div>
  </div>
</template>
