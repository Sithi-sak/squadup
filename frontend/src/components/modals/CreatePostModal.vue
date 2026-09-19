<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  PhCaretDown,
  PhCrop,
  PhGlobe,
  PhImage,
  PhPencilSimple,
  PhPlus,
  PhUserCircle,
  PhX,
} from '@phosphor-icons/vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import ImageCropper from '@/components/common/ImageCropper.vue'
import { games } from '@/data/games'
import { mockCurrentUser } from '@/mocks/users'
import { useAuthStore } from '@/stores/auth'
import { useFeedStore, type FeedPost } from '@/stores/feed'
import { usePlayersStore } from '@/stores/players'
import { resolveAvatarUrl } from '@/utils/avatar'

/** Passing `post` switches the modal into edit mode: prefilled text and image, no tag/visibility
 * controls (the backend only lets an edit change text/image, category stays fixed same as
 * before), "Save changes" instead of "Post". */
const props = defineProps<{ post?: FeedPost | null }>()
const emit = defineEmits<{ updated: [FeedPost]; created: [FeedPost] }>()

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

/** The picked tag rides along as the post's `tag`, not its `category`: `category` is the fixed
 * `feed_category` enum ('games' | 'chilling' | 'clips'), so a game name in it is rejected by
 * Postgres outright. A post carries one tag, so the row is single-select. Chips start as the
 * Pal's own service names; "Add" appends any game from the catalog not already offered. */
const serviceTags = computed(
  () => myPlayerProfile.value?.services.map((service) => service.name) ?? [],
)
const addedTags = ref<string[]>([])
const availableTags = computed(() => [...serviceTags.value, ...addedTags.value])

const gameOptions = computed(() =>
  games.map((game) => game.name).filter((name) => !availableTags.value.includes(name)),
)

const text = ref('')
const selectedTag = ref<string | null>(null)
// `undefined` rather than `null` for the picker's empty state: USelectMenu's model type is
// `string | undefined`, and `null` trips vue-tsc (the same mismatch StepGames.vue still reports).
const pendingGame = ref<string | undefined>(undefined)

watch(pendingGame, (game) => {
  if (!game) return
  addedTags.value = [...addedTags.value, game]
  selectedTag.value = game
  pendingGame.value = undefined
})
const posting = ref(false)

const MAX_IMAGES = 10

/** One entry per image on the post, in display order. `existing` images came back from the
 * backend and survive an edit by URL (`keepImageUrls`); `new` ones are local picks that upload as
 * files. Cropping an existing image turns it into a `new` one, since what uploads is the cropped
 * output. `original` is kept untouched so re-cropping never compounds quality loss. */
type Attachment =
  | { kind: 'existing'; id: string; url: string }
  | {
      kind: 'new'
      id: string
      file: File
      original: File
      originalUrl: string
      previewUrl: string
    }

const attachments = ref<Attachment[]>([])
const files = ref<File[] | null>(null)
/** Id of the attachment the cropper is open on, or null when it is closed. `autoCropId` marks
 * the one the cropper opened on by itself, which cancelling discards (nothing was ever chosen);
 * cancelling a crop the user asked for just leaves that photo as it was. */
const croppingId = ref<string | null>(null)
const autoCropId = ref<string | null>(null)

let nextId = 0
function makeId() {
  nextId += 1
  return `att-${nextId}`
}

const cropping = computed(() => croppingId.value !== null)
/** Non-null only when exactly one photo is attached, which gets the large single preview. */
const soleAttachment = computed(() =>
  attachments.value.length === 1 ? attachments.value[0]! : null,
)
const croppingAttachment = computed(() => attachments.value.find((a) => a.id === croppingId.value))
const croppingSource = computed(() => {
  const attachment = croppingAttachment.value
  if (!attachment) return null
  return attachment.kind === 'existing' ? attachment.url : attachment.originalUrl
})

function attachmentUrl(attachment: Attachment) {
  return attachment.kind === 'existing' ? attachment.url : attachment.previewUrl
}

function releaseAttachment(attachment: Attachment) {
  if (attachment.kind !== 'new') return
  URL.revokeObjectURL(attachment.originalUrl)
  URL.revokeObjectURL(attachment.previewUrl)
}

function clearAttachments() {
  attachments.value.forEach(releaseAttachment)
  attachments.value = []
  files.value = null
  croppingId.value = null
  autoCropId.value = null
}

function removeAttachment(id: string) {
  const attachment = attachments.value.find((a) => a.id === id)
  if (attachment) releaseAttachment(attachment)
  attachments.value = attachments.value.filter((a) => a.id !== id)
  if (croppingId.value === id) croppingId.value = null
}

function newAttachment(file: File): Attachment {
  return {
    kind: 'new',
    id: makeId(),
    file,
    original: file,
    originalUrl: URL.createObjectURL(file),
    previewUrl: URL.createObjectURL(file),
  }
}

/** UFileUpload owns `files`; this mirrors whatever it hands over into `attachments` and then
 * empties it, so the same photo can be picked again later and the dropzone's own list stays out
 * of the way. A lone first pick opens the cropper straight away (one-image posts keep the flow
 * they had); a multi-pick lands as thumbnails to crop individually instead of a modal gauntlet. */
watch(files, (picked) => {
  if (!picked?.length) return
  const room = MAX_IMAGES - attachments.value.length
  const accepted = picked.slice(0, Math.max(0, room))
  if (picked.length > accepted.length) {
    toast.add({
      title: `Up to ${MAX_IMAGES} photos per post`,
      description: 'The extra photos were not attached.',
      color: 'warning',
    })
  }

  const added = accepted.map(newAttachment)
  attachments.value = [...attachments.value, ...added]
  files.value = null
  if (added.length === 1 && attachments.value.length === 1) {
    croppingId.value = added[0]!.id
    autoCropId.value = added[0]!.id
  }
})

function applyCrop(blob: Blob) {
  const attachment = croppingAttachment.value
  if (!attachment) return

  const sourceName = attachment.kind === 'new' ? attachment.original.name : 'photo'
  const extension = blob.type === 'image/png' ? 'png' : blob.type === 'image/webp' ? 'webp' : 'jpg'
  const file = new File([blob], `${sourceName.replace(/\.[^.]+$/, '')}-cropped.${extension}`, {
    type: blob.type,
  })

  const cropped: Attachment =
    attachment.kind === 'new'
      ? { ...attachment, file, previewUrl: URL.createObjectURL(blob) }
      : {
          kind: 'new',
          id: attachment.id,
          file,
          original: file,
          originalUrl: attachment.url,
          previewUrl: URL.createObjectURL(blob),
        }

  if (attachment.kind === 'new') URL.revokeObjectURL(attachment.previewUrl)
  attachments.value = attachments.value.map((a) => (a.id === attachment.id ? cropped : a))
  croppingId.value = null
  autoCropId.value = null
}

function cropFailed(message: string) {
  croppingId.value = null
  autoCropId.value = null
  toast.add({ title: 'Could not crop that photo', description: message, color: 'error' })
}

function cancelCrop() {
  const id = croppingId.value
  croppingId.value = null
  if (id && id === autoCropId.value) removeAttachment(id)
  autoCropId.value = null
}

onBeforeUnmount(() => attachments.value.forEach(releaseAttachment))

watch(open, (isOpen) => {
  if (isOpen) {
    text.value = props.post?.text ?? ''
    clearAttachments()
    attachments.value = (props.post?.imageUrls ?? []).map((url) => ({
      kind: 'existing',
      id: makeId(),
      url,
    }))
    return
  }
  text.value = ''
  selectedTag.value = null
  addedTags.value = []
  pendingGame.value = undefined
  clearAttachments()
  visibility.value = 'Public'
})

function toggleTag(tag: string) {
  selectedTag.value = selectedTag.value === tag ? null : tag
}

const canPost = computed(
  () =>
    !posting.value &&
    !cropping.value &&
    (text.value.trim().length > 0 || attachments.value.length > 0),
)

async function submitPost() {
  if (!canPost.value) return

  posting.value = true
  try {
    if (isEditing.value && props.post) {
      const updated = await feedStore.updatePost(props.post.id, {
        text: text.value.trim(),
        keepImageUrls: attachments.value.flatMap((a) => (a.kind === 'existing' ? [a.url] : [])),
        images: attachments.value.flatMap((a) => (a.kind === 'new' ? [a.file] : [])),
      })
      emit('updated', updated)
    } else {
      emit(
        'created',
        await feedStore.createPost({
          text: text.value.trim(),
          images: attachments.value.flatMap((a) => (a.kind === 'new' ? [a.file] : [])),
          tag: selectedTag.value ?? undefined,
        }),
      )
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
    :title="cropping ? 'Crop photo' : isEditing ? 'Edit post' : 'Create post'"
    :ui="{
      content: 'max-w-2xl rounded-3xl',
      header: 'px-6 py-5',
      body: 'flex flex-col gap-6 px-6 py-6',
    }"
  >
    <template #body>
      <ImageCropper
        v-if="croppingSource"
        :src="croppingSource"
        :type="croppingAttachment?.kind === 'new' ? croppingAttachment.original.type : undefined"
        @cancel="cancelCrop"
        @apply="applyCrop"
        @error="cropFailed"
      />

      <template v-else>
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
          autoresize
          :rows="1"
          :maxrows="14"
          class="w-full"
          :ui="{
            base: 'resize-none rounded-2xl bg-gray-800/70 px-4 py-3.5 text-sm leading-relaxed ring-0 hover:bg-gray-800',
          }"
        />

        <!-- One image reads better big; several tile like the feed card they will become. -->
        <div v-if="soleAttachment" class="relative">
          <img
            :src="attachmentUrl(soleAttachment)"
            alt="Selected photo"
            class="max-h-80 w-full rounded-2xl bg-black/40 object-contain ring-1 ring-inset ring-white/10"
          />
          <div class="absolute top-2 right-2 flex items-center gap-2">
            <UButton
              color="neutral"
              variant="solid"
              size="xs"
              class="rounded-full bg-black/60 text-white hover:bg-black/80"
              @click="croppingId = soleAttachment.id"
            >
              <PhCrop :size="14" weight="bold" />
              Crop
            </UButton>
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
              aria-label="Remove photo"
              @click="removeAttachment(soleAttachment.id)"
            >
              <PhX :size="16" weight="bold" />
            </button>
          </div>
        </div>

        <div v-else-if="attachments.length" class="grid grid-cols-3 gap-2">
          <div
            v-for="attachment in attachments"
            :key="attachment.id"
            class="group relative aspect-square overflow-hidden rounded-xl bg-black/40 ring-1 ring-inset ring-white/10"
          >
            <img
              :src="attachmentUrl(attachment)"
              alt="Selected photo"
              class="h-full w-full object-cover"
            />
            <div class="absolute top-1.5 right-1.5 flex items-center gap-1.5">
              <button
                type="button"
                class="flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
                aria-label="Crop photo"
                @click="croppingId = attachment.id"
              >
                <PhCrop :size="14" weight="bold" />
              </button>
              <button
                type="button"
                class="flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
                aria-label="Remove photo"
                @click="removeAttachment(attachment.id)"
              >
                <PhX :size="14" weight="bold" />
              </button>
            </div>
          </div>
        </div>

        <UFileUpload
          v-if="attachments.length < MAX_IMAGES"
          v-model="files"
          multiple
          accept="image/png,image/jpeg,image/webp"
          layout="list"
          class="w-full"
          :ui="{
            base: attachments.length
              ? 'rounded-2xl border-white/15 bg-gray-800/40 py-5'
              : 'rounded-2xl border-white/15 bg-gray-800/40 py-10',
            label: 'text-white',
            description: 'text-slate-400',
          }"
        >
          <template #leading>
            <span
              class="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-slate-300"
            >
              <PhImage :size="20" />
            </span>
          </template>
          <template #label>{{ attachments.length ? 'Add more photos' : 'Add a photo' }}</template>
          <template #description>
            or drag and drop · PNG, JPG, WEBP up to 8MB · {{ MAX_IMAGES }} photos max
          </template>
        </UFileUpload>

        <div v-if="!isEditing" class="flex flex-col gap-2">
          <p class="text-sm text-slate-300">Tag a game or service</p>
          <div class="flex flex-wrap items-center gap-2">
            <button
              v-for="tag in availableTags"
              :key="tag"
              type="button"
              class="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              :class="
                selectedTag === tag
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-800/70 text-slate-300 hover:bg-gray-800'
              "
              @click="toggleTag(tag)"
            >
              {{ tag }}
            </button>
            <USelectMenu
              v-if="gameOptions.length"
              v-model="pendingGame"
              :items="gameOptions"
              placeholder="Add a game"
              variant="none"
              :ui="{
                base: 'gap-1.5 rounded-full bg-gray-800/70 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-gray-800',
              }"
            >
              <template #default>
                <span class="flex items-center gap-1.5">
                  <PhPlus :size="14" weight="bold" />
                  Add
                </span>
              </template>
            </USelectMenu>
          </div>
        </div>

        <div class="flex items-center justify-between gap-3 border-t border-white/10 pt-4">
          <p class="text-xs text-slate-400">
            {{
              isEditing
                ? "Editing won't repost this to your followers."
                : 'Posts are visible to your followers.'
            }}
          </p>
          <div class="flex items-center gap-3">
            <UButton color="neutral" variant="soft" class="rounded-full" @click="open = false"
              >Cancel</UButton
            >
            <UButton
              color="primary"
              class="rounded-full"
              :loading="posting"
              :disabled="!canPost"
              @click="submitPost"
            >
              <PhPencilSimple :size="16" weight="bold" />
              {{ isEditing ? 'Save changes' : 'Post' }}
            </UButton>
          </div>
        </div>
      </template>
    </template>
  </UModal>
</template>
