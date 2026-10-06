<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  PhCaretDown,
  PhCrop,
  PhFilmSlate,
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
const ACCEPTED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp']
/** Mirrors `core/video.py`'s `MAX_UPLOAD_BYTES`/`MAX_DURATION_SECONDS`, checked here first so a
 * clip that's too long fails before it uploads rather than after. */
const MAX_VIDEO_MB = 200
const MAX_VIDEO_SECONDS = 60

/** Set by the Feed's "Clip" buttons: the dropzone then takes a video only. Cleared on close, so
 * the next plain open takes either again. */
const clipOnly = defineModel<boolean>('clip', { default: false })

/** A picked clip (4.61), one per post and never alongside photos. It skips the cropper and
 * uploads as-is; the server re-encodes it to 720p after the post is created. */
const clip = ref<{ file: File; url: string } | null>(null)

function setClip(file: File | null) {
  if (clip.value) URL.revokeObjectURL(clip.value.url)
  clip.value = file ? { file, url: URL.createObjectURL(file) } : null
}

/** Reads a clip's length from its metadata. Resolves null when this browser can't parse the
 * file (some HEVC .mov files outside Safari); the server checks again, so those still go up. */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const element = document.createElement('video')
    const url = URL.createObjectURL(file)
    const done = (duration: number | null) => {
      URL.revokeObjectURL(url)
      resolve(duration)
    }
    element.preload = 'metadata'
    element.onloadedmetadata = () =>
      done(Number.isFinite(element.duration) ? element.duration : null)
    element.onerror = () => done(null)
    element.src = url
  })
}

async function pickClip(file: File) {
  if (file.size > MAX_VIDEO_MB * 1024 * 1024) {
    toast.add({
      title: 'That clip is too large',
      description: `Videos can be up to ${MAX_VIDEO_MB}MB.`,
      color: 'warning',
    })
    return
  }
  const duration = await readDuration(file)
  if (duration !== null && duration > MAX_VIDEO_SECONDS + 0.5) {
    toast.add({
      title: 'That clip is too long',
      description: `Clips can be up to ${MAX_VIDEO_SECONDS} seconds. Trim it and try again.`,
      color: 'warning',
    })
    return
  }
  if (open.value) setClip(file)
}

/** Clips go up only on a new post; an edit keeps whatever media the post already has. */
const acceptsClip = computed(() => !isEditing.value && !attachments.value.length)
/** The clip shown in the composer: a fresh pick, or the one an edited clip post already has
 * (`src` is null while its encode is still running). */
const clipPreview = computed(() => {
  if (clip.value) return { src: clip.value.url as string | null, poster: undefined }
  if (isEditing.value && props.post?.videoStatus) {
    return { src: props.post.videoUrl, poster: props.post.videoPosterUrl ?? undefined }
  }
  return null
})
const uploadAccept = computed(() => {
  if (clipOnly.value) return 'video/*'
  return acceptsClip.value
    ? [...ACCEPTED_IMAGE_TYPES, 'video/*'].join(',')
    : ACCEPTED_IMAGE_TYPES.join(',')
})

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
  setClip(null)
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
watch(files, (selected) => {
  if (!selected?.length) return
  files.value = null
  // `accept` only filters the OS picker; a drop or the picker's "All files" option still lets
  // anything through, so every file is sorted by type here. A video must never reach the
  // cropper, which would show it as a blank image.
  const videos = acceptsClip.value ? selected.filter((file) => file.type.startsWith('video/')) : []
  const picked = clipOnly.value
    ? []
    : selected.filter((file) => ACCEPTED_IMAGE_TYPES.includes(file.type))
  if (videos.length + picked.length < selected.length) {
    toast.add({
      title: "Some files weren't attached",
      description: clipOnly.value
        ? 'Pick a video clip here. Photos go in through the Photo button.'
        : acceptsClip.value
          ? 'Posts take PNG, JPG and WEBP photos or one video clip.'
          : 'Posts take PNG, JPG and WEBP photos.',
      color: 'warning',
    })
  }
  if (videos.length) {
    if (videos.length === 1 && !picked.length && !attachments.value.length) {
      void pickClip(videos[0]!)
      return
    }
    toast.add({
      title: 'One clip per post',
      description: 'A post can have photos or a single clip, not both.',
      color: 'warning',
    })
  }
  if (!picked.length) return
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

onBeforeUnmount(() => {
  attachments.value.forEach(releaseAttachment)
  setClip(null)
})

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
  clipOnly.value = false
})

function toggleTag(tag: string) {
  selectedTag.value = selectedTag.value === tag ? null : tag
}

const canPost = computed(
  () =>
    !posting.value &&
    !cropping.value &&
    (text.value.trim().length > 0 || attachments.value.length > 0 || !!clipPreview.value),
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
      const created = await feedStore.createPost({
        text: text.value.trim(),
        images: attachments.value.flatMap((a) => (a.kind === 'new' ? [a.file] : [])),
        video: clip.value?.file,
        tag: selectedTag.value ?? undefined,
      })
      emit('created', created)
      if (created.videoStatus === 'processing') {
        toast.add({
          title: 'Clip uploaded',
          description: "It's being processed and will show in the feed once it's ready.",
          color: 'success',
        })
      }
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

        <div v-if="clipPreview" class="relative">
          <video
            v-if="clipPreview.src"
            :src="clipPreview.src"
            :poster="clipPreview.poster"
            controls
            playsinline
            preload="metadata"
            class="max-h-80 w-full rounded-2xl bg-black/40 ring-1 ring-inset ring-white/10"
          />
          <div
            v-else
            class="flex h-48 w-full flex-col items-center justify-center gap-2 rounded-2xl bg-black/40 text-sm text-slate-400 ring-1 ring-inset ring-white/10"
          >
            <PhFilmSlate :size="28" />
            Your clip is still processing.
          </div>
          <button
            v-if="clip"
            type="button"
            class="absolute top-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
            aria-label="Remove clip"
            @click="setClip(null)"
          >
            <PhX :size="16" weight="bold" />
          </button>
        </div>

        <UFileUpload
          v-else-if="attachments.length < MAX_IMAGES"
          v-model="files"
          multiple
          :accept="uploadAccept"
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
              <PhFilmSlate v-if="clipOnly" :size="20" />
              <PhImage v-else :size="20" />
            </span>
          </template>
          <template #label>
            {{
              clipOnly
                ? 'Add a clip'
                : attachments.length
                  ? 'Add more photos'
                  : acceptsClip
                    ? 'Add photos or a clip'
                    : 'Add a photo'
            }}
          </template>
          <template #description>
            <template v-if="clipOnly">
              or drag and drop · MP4, MOV or WEBM up to {{ MAX_VIDEO_SECONDS }} seconds
            </template>
            <template v-else-if="acceptsClip">
              or drag and drop · up to {{ MAX_IMAGES }} photos, or one clip up to
              {{ MAX_VIDEO_SECONDS }} seconds
            </template>
            <template v-else>
              or drag and drop · PNG, JPG, WEBP up to 8MB · {{ MAX_IMAGES }} photos max
            </template>
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
                content: 'w-72',
              }"
              :content="{ align: 'start' }"
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
