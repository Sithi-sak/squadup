<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { PhCaretDown, PhGlobe, PhImage, PhPencilSimple, PhPlus, PhUserCircle, PhX } from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

/** Passing `post` switches the modal into edit mode: prefilled text and image, no tag/visibility
 * controls (the backend only lets an edit change text/image, category stays fixed same as
 * before), "Save changes" instead of "Post". */
const props = defineProps<{ post?: FeedPost | null }>()
const emit = defineEmits<{ updated: [FeedPost] }>()

const open = defineModel<boolean>('open', { required: true })

const authStore = useAuthStore()
const feedStore = useFeedStore()
const playersStore = usePlayersStore()
const toast = useToast()

const isEditing = computed(() => !!props.post)

const displayName = computed(() => authStore.user?.displayName ?? mockCurrentUser.displayName)
const myPlayerProfile = computed(() => playersStore.mine)
const avatarUrl = computed(() =>
  resolveAvatarUrl(authStore.user?.id ?? mockCurrentUser.id, myPlayerProfile.value?.avatarUrl),
)

const visibilityOptions = ['Public', 'Followers only', 'Only me'] as const
const visibility = ref<(typeof visibilityOptions)[number]>('Public')
const visibilityItems = computed(() =>
  visibilityOptions.map((label) => ({ label, onSelect: () => (visibility.value = label) })),
)

const availableTags = computed(() => myPlayerProfile.value?.services.map((service) => service.name) ?? [])

const text = ref('')
const selectedTags = ref<string[]>([])
const files = ref<File | null>(null)
const posting = ref(false)

/** Edit mode's existing image, shown as a preview instead of the upload dropzone until removed
 * or replaced. `imageRemoved` tracks an explicit removal with no replacement picked yet - the
 * dropzone reappears so a new image can be attached instead. */
const existingImageUrl = ref<string | null>(null)
const imageRemoved = ref(false)

watch(open, (isOpen) => {
  if (isOpen) {
    text.value = props.post?.text ?? ''
    existingImageUrl.value = props.post?.imageUrl ?? null
    imageRemoved.value = false
    return
  }
  text.value = ''
  selectedTags.value = []
  files.value = null
  existingImageUrl.value = null
  imageRemoved.value = false
  visibility.value = 'Public'
})

function removeExistingImage() {
  existingImageUrl.value = null
  imageRemoved.value = true
}

function toggleTag(tag: string) {
  selectedTags.value = selectedTags.value.includes(tag)
    ? selectedTags.value.filter((t) => t !== tag)
    : [...selectedTags.value, tag]
}

const canPost = computed(() => {
  if (posting.value) return false
  if (isEditing.value) return text.value.trim().length > 0 || !!existingImageUrl.value || files.value !== null
  return text.value.trim().length > 0 || files.value !== null
})

async function submitPost() {
  if (!canPost.value) return

  posting.value = true
  try {
    if (isEditing.value && props.post) {
      const updated = await feedStore.updatePost(props.post.id, {
        text: text.value.trim(),
        image: files.value ?? undefined,
        removeImage: imageRemoved.value,
      })
      emit('updated', updated)
    } else {
      await feedStore.createPost({ text: text.value.trim(), image: files.value ?? undefined })
    }
    open.value = false
  } catch (err) {
    toast.add({
      title: isEditing.value ? 'Could not save changes' : 'Could not create post',
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    posting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="isEditing ? 'Edit post' : 'Create post'"
    :ui="{ content: 'max-w-2xl rounded-3xl', header: 'px-6 py-5', body: 'flex flex-col gap-6 px-6 py-6' }"
  >
    <template #body>
      <div class="flex items-center gap-3">
        <UAvatar :src="avatarUrl" size="lg" class="bg-white/10 text-slate-300">
          <PhUserCircle :size="26" />
        </UAvatar>
        <div>
          <p class="font-semibold text-white">{{ displayName }}</p>
          <UDropdownMenu v-if="!isEditing" :items="visibilityItems">
            <button
              type="button"
              class="mt-1 flex items-center gap-1.5 rounded-full bg-gray-800/70 px-3 py-1 text-xs text-slate-300 hover:bg-gray-800"
            >
              <PhGlobe :size="14" />
              {{ visibility }}
              <PhCaretDown :size="12" />
            </button>
          </UDropdownMenu>
        </div>
      </div>

      <UTextarea
        v-model="text"
        placeholder="Share something with your squad, what did you play today?"
        variant="subtle"
        :rows="5"
        class="w-full"
        :ui="{ base: 'rounded-2xl bg-gray-800/70 px-4 py-3.5 text-sm leading-relaxed ring-0 hover:bg-gray-800' }"
      />

      <div v-if="isEditing && existingImageUrl" class="relative">
        <img
          :src="existingImageUrl"
          alt=""
          class="aspect-video w-full rounded-2xl object-cover ring-1 ring-inset ring-white/10"
        />
        <button
          type="button"
          class="absolute top-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
          aria-label="Remove image"
          @click="removeExistingImage"
        >
          <PhX :size="16" weight="bold" />
        </button>
      </div>

      <UFileUpload
        v-else
        v-model="files"
        accept="image/png,image/jpeg,image/webp"
        layout="list"
        class="w-full"
        :ui="{
          base: 'rounded-2xl border-white/15 bg-gray-800/40 py-10',
          label: 'text-white',
          description: 'text-slate-400',
        }"
      >
        <template #leading>
          <span class="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-slate-300">
            <PhImage :size="20" />
          </span>
        </template>
        <template #label>Add a photo</template>
        <template #description>or drag and drop · PNG, JPG, WEBP up to 8MB</template>
      </UFileUpload>

      <div v-if="!isEditing && availableTags.length" class="flex flex-col gap-2">
        <p class="text-sm text-slate-300">Tag a game or service</p>
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-for="tag in availableTags"
            :key="tag"
            type="button"
            class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
            :class="
              selectedTags.includes(tag)
                ? 'bg-brand-600 text-white'
                : 'bg-gray-800/70 text-slate-300 hover:bg-gray-800'
            "
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </button>
          <UButton color="neutral" variant="soft" size="sm" class="rounded-full">
            <PhPlus :size="14" weight="bold" />
            Add
          </UButton>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 border-t border-white/10 pt-4">
        <p class="text-xs text-slate-400">
          {{ isEditing ? "Editing won't repost this to your followers." : 'Posts are visible to your followers.' }}
        </p>
        <div class="flex items-center gap-3">
          <UButton color="neutral" variant="soft" class="rounded-full" @click="open = false">Cancel</UButton>
          <UButton color="primary" class="rounded-full" :loading="posting" :disabled="!canPost" @click="submitPost">
            <PhPencilSimple :size="16" weight="bold" />
            {{ isEditing ? 'Save changes' : 'Post' }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
