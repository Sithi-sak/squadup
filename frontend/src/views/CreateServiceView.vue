<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PhCaretLeft, PhLightning, PhPlus, PhStar, PhTrophy, PhUserCircle, PhX } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { usePlayersStore } from '@/stores/players'

const router = useRouter()
const playersStore = usePlayersStore()

onMounted(() => {
  if (!playersStore.mine) playersStore.fetchMine()
})

const categoryOptions = ['Game', 'Coaching', 'Chat', 'Watch Party']
const gameOptions = [
  'Valorant',
  'League of Legends',
  'Mobile Legends: Bang Bang',
  'Dota 2',
  'Counter-Strike 2',
  'Overwatch 2',
  'Apex Legends',
  'PUBG Mobile',
  'Free Fire',
  'Honor of Kings',
]
const unitOptions = ['/game', '/hour', '/session', '/15min']

const category = ref(categoryOptions[0]!)
const game = ref(gameOptions[0]!)
const title = ref('')
const description = ref('')

const coverInput = ref<HTMLInputElement | null>(null)
const coverPreviewUrl = ref<string | null>(null)
const coverFile = ref<File | null>(null)

function openCoverPicker() {
  coverInput.value?.click()
}

function onCoverSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (coverPreviewUrl.value) URL.revokeObjectURL(coverPreviewUrl.value)
  coverPreviewUrl.value = URL.createObjectURL(file)
  coverFile.value = file
}

function removeCover() {
  if (coverPreviewUrl.value) URL.revokeObjectURL(coverPreviewUrl.value)
  coverPreviewUrl.value = null
  coverFile.value = null
  if (coverInput.value) coverInput.value.value = ''
}

onBeforeUnmount(() => {
  if (coverPreviewUrl.value) URL.revokeObjectURL(coverPreviewUrl.value)
})

interface ServiceTypeRow {
  id: number
  label: string
  priceCoins: number | null
  priceUnit: string
}

let nextRowId = 1
function createRow(label = ''): ServiceTypeRow {
  return { id: nextRowId++, label, priceCoins: null, priceUnit: unitOptions[0]! }
}

const serviceTypes = ref<ServiceTypeRow[]>([createRow()])

function addServiceType() {
  serviceTypes.value.push(createRow())
}

function removeServiceType(id: number) {
  serviceTypes.value = serviceTypes.value.filter((row) => row.id !== id)
}

const firstOrderFree = ref(true)
const percentageDiscount = ref(false)
const discountPct = ref(15)

const primaryType = computed(() => serviceTypes.value.find((row) => row.priceCoins !== null) ?? serviceTypes.value[0])

const previewTags = computed(() => [game.value, category.value].filter(Boolean))

const previewPromoBadge = computed(() => {
  if (firstOrderFree.value) return '1st Order Free'
  if (percentageDiscount.value) return `${discountPct.value}% Off`
  return null
})

const canPublish = computed(
  () =>
    title.value.trim().length > 0 &&
    serviceTypes.value.length > 0 &&
    serviceTypes.value.every((row) => row.label.trim().length > 0 && row.priceCoins !== null && row.priceCoins >= 0),
)

const fieldUi = { base: 'bg-gray-800/70 px-5 py-3.5 text-sm ring-0 hover:bg-gray-800' }
const selectUi = { base: 'bg-gray-800/70 px-5 py-3.5 text-sm ring-0 hover:bg-gray-800' }

function goBack() {
  router.push('/dashboard/player/services')
}

function saveDraft() {
  goBack()
}

const submitting = ref(false)
const submitError = ref<string | null>(null)

async function publish() {
  if (!canPublish.value || submitting.value) return
  submitting.value = true
  submitError.value = null

  const types = serviceTypes.value.filter((row) => row.label.trim().length > 0)

  const formData = new FormData()
  formData.append('name', title.value.trim())
  if (description.value.trim()) formData.append('description', description.value.trim())
  formData.append('platforms', game.value)
  formData.append(
    'pricing_options',
    JSON.stringify(
      types.map((row) => ({ label: row.label.trim(), price_coins: row.priceCoins ?? 0, price_unit: row.priceUnit })),
    ),
  )
  formData.append('first_order_free', String(firstOrderFree.value))
  if (percentageDiscount.value) formData.append('percent_off', String(discountPct.value))
  if (coverFile.value) formData.append('cover', coverFile.value)

  try {
    await playersStore.createService(formData)
    goBack()
  } catch (err) {
    submitError.value = err instanceof Error ? err.message : 'Failed to publish service'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="h-[calc(100vh-65px)] overflow-y-auto px-4 py-6 md:px-6">
    <div class="mx-auto max-w-2/3">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            type="button"
            aria-label="Back to my services"
            class="flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-full bg-gray-800/70 text-white hover:bg-gray-800"
            @click="goBack"
          >
            <PhCaretLeft :size="18" weight="bold" />
          </button>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">Create a service</h1>
        </div>
        <div class="flex items-center gap-3">
          <UButton color="neutral" variant="soft" class="rounded-full" @click="saveDraft">Save draft</UButton>
          <UButton
            color="primary"
            class="rounded-full"
            :disabled="!canPublish"
            :loading="submitting"
            @click="publish"
          >
            Publish
          </UButton>
        </div>
      </div>

      <p v-if="submitError" class="mt-3 text-sm text-red-400">{{ submitError }}</p>

      <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div class="flex flex-col gap-5">
          <div class="rounded-2xl bg-gray-900/60 p-6">
            <h2 class="text-lg font-bold text-white">Basics</h2>

            <div class="mt-5 grid gap-5 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <label for="service-category" class="text-sm font-medium text-slate-300">Category</label>
                <USelect
                  id="service-category"
                  v-model="category"
                  :items="categoryOptions"
                  variant="subtle"
                  size="md"
                  class="w-full sm:w-auto"
                  :ui="selectUi"
                />
              </div>
              <div class="flex flex-col gap-2">
                <label for="service-game" class="text-sm font-medium text-slate-300">Game</label>
                <USelect
                  id="service-game"
                  v-model="game"
                  :items="gameOptions"
                  variant="subtle"
                  size="md"
                  class="w-full sm:w-auto"
                  :ui="selectUi"
                />
              </div>
            </div>

            <div class="mt-5 flex flex-col gap-2">
              <label for="service-title" class="text-sm font-medium text-slate-300">Service title</label>
              <UInput
                id="service-title"
                v-model="title"
                placeholder="e.g. Valorant Duo — Immortal carry"
                variant="subtle"
                size="lg"
                :ui="fieldUi"
              />
            </div>

            <div class="mt-5 flex flex-col gap-2">
              <label class="text-sm font-medium text-slate-300">Cover image</label>
              <button
                type="button"
                class="relative flex w-full cursor-pointer flex-col items-center justify-center gap-2 overflow-hidden rounded-2xl border-2 border-dashed border-gray-700 bg-gray-800/40 py-10 text-center transition-colors hover:border-gray-600"
                :class="{ 'border-solid border-transparent p-0': coverPreviewUrl }"
                @click="openCoverPicker"
              >
                <template v-if="coverPreviewUrl">
                  <img :src="coverPreviewUrl" alt="Cover preview" class="aspect-21/9 w-full object-cover" />
                  <span
                    role="button"
                    tabindex="0"
                    aria-label="Remove cover image"
                    class="absolute top-3 right-3 flex size-8 items-center justify-center rounded-full bg-squadup-dark/70 text-white hover:bg-squadup-dark"
                    @click.stop="removeCover"
                    @keydown.enter.stop="removeCover"
                  >
                    <PhX :size="16" weight="bold" />
                  </span>
                </template>
                <template v-else>
                  <span class="flex size-9 items-center justify-center rounded-full bg-brand-600/15 text-brand-400">
                    <PhPlus :size="18" weight="bold" />
                  </span>
                  <p class="text-sm text-slate-400">Upload cover · 3:4 · PNG/JPG up to 5MB</p>
                </template>
              </button>
              <input ref="coverInput" type="file" accept="image/png,image/jpeg" class="hidden" @change="onCoverSelected" />
            </div>

            <div class="mt-5 flex flex-col gap-2">
              <label for="service-description" class="text-sm font-medium text-slate-300">Description</label>
              <UTextarea
                id="service-description"
                v-model="description"
                placeholder="Describe your service, playstyle, and what buyers get..."
                variant="subtle"
                :rows="4"
                :ui="{ base: 'bg-gray-800/70 px-5 py-3.5 text-sm ring-0 hover:bg-gray-800' }"
              />
            </div>
          </div>

          <div class="rounded-2xl bg-gray-900/60 p-6">
            <h2 class="text-lg font-bold text-white">Service types &amp; pricing</h2>

            <div class="mt-5 flex flex-col gap-3">
              <div
                v-for="row in serviceTypes"
                :key="row.id"
                class="flex flex-wrap items-center gap-3 rounded-full bg-gray-800/70 px-5 py-2 sm:flex-nowrap"
              >
                <UInput
                  v-model="row.label"
                  placeholder="Service type name"
                  variant="none"
                  size="md"
                  class="min-w-0 flex-1"
                  :ui="{ base: 'bg-transparent px-1 text-md font-medium text-white ring-0 focus-visible:ring-0' }"
                />
                <div class="flex shrink-0 items-center gap-1.5">
                  <img :src="coinIcon" alt="" class="h-4 w-4" />
                  <UInputNumber
                    v-model="row.priceCoins"
                    :min="0"
                    placeholder="0"
                    variant="subtle"
                    size="md"
                    class="w-20"
                    :ui="{ base: 'bg-transparent px-1 text-right text-sm ring-0 focus-visible:ring-0' }"
                  />
                </div>
                <USelect
                  v-model="row.priceUnit"
                  :items="unitOptions"
                  variant="subtle"
                  size="md"
                  class="w-24 shrink-0"
                  :ui="{ base: 'bg-transparent px-2 text-md ring-0 hover:bg-white/5' }"
                />
                <button
                  type="button"
                  class="shrink-0 cursor-pointer text-slate-500 hover:text-slate-300"
                  :aria-label="`Remove ${row.label || 'service type'}`"
                  @click="removeServiceType(row.id)"
                >
                  <PhX :size="16" weight="bold" />
                </button>
              </div>

              <button
                type="button"
                class="w-full cursor-pointer rounded-full bg-gray-800/40 py-3 text-sm font-medium text-brand-400 hover:bg-gray-800/70 hover:text-brand-300"
                @click="addServiceType"
              >
                + Add service type
              </button>
            </div>
          </div>

          <div class="rounded-2xl bg-gray-900/60 p-6">
            <h2 class="text-lg font-bold text-white">Promotions</h2>

            <div class="mt-4 flex flex-col divide-y divide-white/10">
              <div class="flex items-center justify-between gap-4 py-4">
                <div class="min-w-0">
                  <p class="font-medium text-white">1st order free</p>
                  <p class="text-sm text-slate-400">New buyers get their first order free</p>
                </div>
                <USwitch v-model="firstOrderFree" color="primary" class="shrink-0" />
              </div>
              <div class="flex items-center justify-between gap-4 py-4">
                <div class="min-w-0">
                  <p class="font-medium text-white">Percentage discount</p>
                  <p class="text-sm text-slate-400">Apply X% off your base price</p>
                </div>
                <div class="flex shrink-0 items-center gap-3">
                  <UInputNumber
                    v-if="percentageDiscount"
                    v-model="discountPct"
                    :min="1"
                    :max="90"
                    size="sm"
                    variant="subtle"
                    class="w-16"
                    :ui="{ base: 'bg-gray-800/70 px-2 text-right text-sm ring-0' }"
                  />
                  <USwitch v-model="percentageDiscount" color="primary" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-3 lg:sticky lg:top-6 lg:self-start">
          <p class="text-sm font-medium text-slate-300">Live preview</p>

          <div class="rounded-2xl bg-gray-800/70 p-5">
            <div class="flex items-start justify-between gap-3">
              <div class="relative shrink-0">
                <UAvatar size="lg" class="bg-white/10 text-slate-300">
                  <PhUserCircle :size="26" />
                </UAvatar>
                <span class="absolute right-0 bottom-0 h-2.5 w-2.5 rounded-full bg-brand-400 ring-2 ring-gray-800" />
              </div>
            </div>

            <div class="mt-3 flex items-center gap-1.5">
              <span class="font-semibold text-white">{{ playersStore.mine?.displayName ?? 'You' }}</span>
              <PhTrophy :size="14" weight="fill" class="shrink-0 text-amber-400" />
            </div>
            <p class="mt-0.5 inline-flex items-center gap-1 text-xs text-slate-400">
              <PhStar :size="12" weight="fill" class="text-amber-400" />
              New · 0 orders
            </p>

            <div v-if="previewTags.length" class="mt-3 flex flex-wrap gap-1.5">
              <UBadge v-for="tag in previewTags" :key="tag" color="neutral" variant="soft" size="md" class="rounded-full">
                {{ tag }}
              </UBadge>
            </div>

            <p class="mt-3 line-clamp-2 text-sm text-slate-400">
              {{ description || "Don't be shy~ let's play!" }}
            </p>

            <div class="mt-4 flex items-center justify-between gap-2">
              <UBadge v-if="previewPromoBadge" color="primary" variant="solid" size="md" class="gap-1 rounded-full">
                <PhLightning :size="12" weight="fill" />
                {{ previewPromoBadge }}
              </UBadge>
              <span v-else />
              <span class="inline-flex items-center gap-1 text-lg font-bold text-white">
                <img :src="coinIcon" alt="" class="h-4 w-4" />
                {{ primaryType?.priceCoins ?? '--' }}{{ primaryType?.priceUnit ?? '/game' }}
              </span>
            </div>
          </div>

          <p class="text-xs text-slate-500">Your service is reviewed within a few minutes before going live.</p>
        </div>
      </div>
    </div>
  </div>
</template>
