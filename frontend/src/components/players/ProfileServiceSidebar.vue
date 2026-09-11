<script setup lang="ts">
import { computed, ref } from 'vue'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'
import type { PlayerServiceListing } from '@/stores/players'

const props = defineProps<{ services: PlayerServiceListing[]; selectedId: string }>()
defineEmits<{ select: [id: string] }>()

const search = ref('')
const expanded = ref(false)
const collapsedCount = 6

const filtered = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return props.services
  return props.services.filter((service) => service.name.toLowerCase().includes(query))
})

const visible = computed(() =>
  expanded.value || search.value ? filtered.value : filtered.value.slice(0, collapsedCount),
)
</script>

<template>
  <div class="rounded-xl bg-gray-800/70 p-3">
    <UInput
      v-model="search"
      placeholder="Search"
      variant="subtle"
      class="w-full rounded-full"
      :ui="{ base: 'rounded-full' }"
    >
      <template #leading>
        <PhMagnifyingGlass :size="16" weight="bold" />
      </template>
    </UInput>

    <div class="mt-3 flex flex-col gap-1">
      <button
        v-for="service in visible"
        :key="service.id"
        type="button"
        class="flex w-full items-center gap-3 rounded-xl p-2 text-left transition-colors"
        :class="
          service.id === selectedId
            ? 'bg-brand-900/30 ring-1 ring-inset ring-brand-500'
            : 'hover:bg-gray-700/50'
        "
        @click="$emit('select', service.id)"
      >
        <div class="h-10 w-10 shrink-0 rounded-full bg-white/10" />
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1.5">
            <span class="truncate text-md font-medium text-white">{{ service.name }}</span>
            <UBadge
              v-if="service.promoBadge"
              color="primary"
              variant="soft"
              size="sm"
              class="shrink-0 rounded-full text-xs text-brand-500"
            >
              {{ service.promoBadge }}
            </UBadge>
          </div>
          <p class="mt-0.5 inline-flex items-center gap-1 text-sm text-slate-400">
            <img :src="coinIcon" alt="" class="h-4 w-4" />
            {{ service.priceCoins }}{{ service.priceUnit }}
          </p>
        </div>
      </button>

      <p v-if="visible.length === 0" class="py-6 text-center text-sm text-slate-400">
        No services match "{{ search }}".
      </p>
    </div>

    <button
      v-if="!expanded && !search && filtered.length > collapsedCount"
      type="button"
      class="mt-2 w-full text-center text-sm font-medium text-brand-400 hover:text-brand-300"
      @click="expanded = true"
    >
      More
    </button>
  </div>
</template>
