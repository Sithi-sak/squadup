<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables/useToast'
import { PhStar, PhTrash } from '@phosphor-icons/vue'
import DashboardLayout from '@/components/dashboard/DashboardLayout.vue'
import ConfirmModal from '@/components/modals/ConfirmModal.vue'
import coinIcon from '@/assets/squadup-coin.svg'
import { usePlayersStore } from '@/stores/players'

const router = useRouter()
const playersStore = usePlayersStore()
const toast = useToast()

onMounted(() => {
  playersStore.fetchMine()
})

const cards = computed(() =>
  (playersStore.mine?.services ?? []).map((service) => ({
    service,
    detail: playersStore.mine!.serviceDetails[service.id],
  })),
)

const togglingId = ref<string | null>(null)

async function toggleActive(serviceId: string, active: boolean) {
  togglingId.value = serviceId
  try {
    await playersStore.updateService(serviceId, { active })
  } catch (err) {
    toast.add({
      title: "Couldn't update service",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    togglingId.value = null
  }
}

const deleteTarget = ref<{ id: string; name: string } | null>(null)
const deleteOpen = ref(false)
const deleting = ref(false)

function askDelete(service: { id: string; name: string }) {
  deleteTarget.value = service
  deleteOpen.value = true
}

async function handleDelete() {
  if (!deleteTarget.value || deleting.value) return
  deleting.value = true
  try {
    await playersStore.deleteService(deleteTarget.value.id)
    deleteOpen.value = false
  } catch (err) {
    toast.add({
      title: "Couldn't delete service",
      description: err instanceof Error ? err.message : 'Please try again.',
      color: 'error',
    })
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <DashboardLayout active="services">
    <div class="flex h-full flex-col gap-5 overflow-y-auto pr-1">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-white sm:text-3xl">My services</h1>
          <p class="mt-1 text-sm text-slate-400">Manage the services buyers can book from you</p>
        </div>
        <UButton color="primary" class="rounded-full" @click="router.push('/dashboard/player/services/new')">
          New Service
        </UButton>
      </div>

      <div v-if="playersStore.mineLoading && !playersStore.mine" class="py-16 text-center text-sm text-slate-400">
        Loading your services...
      </div>

      <UEmpty
        v-else-if="playersStore.mineError"
        title="Couldn't load your services"
        :description="playersStore.mineError"
        class="py-16 text-white"
      >
        <template #actions>
          <UButton color="primary" class="rounded-full" @click="playersStore.fetchMine()">Retry</UButton>
        </template>
      </UEmpty>

      <UEmpty
        v-else-if="!playersStore.mine"
        title="Become a Pal first"
        description="You need a Pal profile before you can list services buyers can book."
        class="py-16 text-white"
      >
        <template #actions>
          <UButton color="primary" class="rounded-full" @click="router.push('/become-player')">
            Become a Player
          </UButton>
        </template>
      </UEmpty>

      <UEmpty
        v-else-if="cards.length === 0"
        title="No services yet"
        description="Create your first service so buyers can book you."
        class="py-16 text-white"
      >
        <template #actions>
          <UButton color="primary" class="rounded-full" @click="router.push('/dashboard/player/services/new')">
            New Service
          </UButton>
        </template>
      </UEmpty>

      <div v-else class="grid grid-cols-1 gap-4 lg:grid-cols-4">
        <div v-for="{ service, detail } in cards" :key="service.id" class="overflow-hidden rounded-xl bg-gray-800/70">
          <div class="relative aspect-21/9 w-full bg-white/5 ring-1 ring-inset ring-white/10">
            <span
              class="absolute top-3 right-3 inline-flex items-center gap-1.5 rounded-full bg-squadup-dark/70 px-2.5 py-1 text-xs font-medium"
              :class="service.active ? 'text-brand-400' : 'text-slate-400'"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="service.active ? 'bg-brand-400' : 'bg-slate-500'" />
              {{ service.active ? 'Active' : 'Paused' }}
            </span>
          </div>
          <div class="p-5">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-lg font-semibold text-white">{{ service.name }}</h2>
              <USwitch
                :model-value="service.active"
                color="primary"
                :disabled="togglingId === service.id"
                @update:model-value="toggleActive(service.id, $event)"
              />
            </div>
            <p class="mt-1 line-clamp-2 text-sm text-slate-400">{{ detail?.description }}</p>
            <div class="mt-4 flex items-center justify-between text-sm">
              <span class="inline-flex items-center gap-1 font-semibold text-white">
                <img :src="coinIcon" alt="" class="h-3.5 w-3.5" />
                {{ service.priceCoins }}{{ service.priceUnit }}
              </span>
              <span class="inline-flex items-center gap-1.5 text-slate-400">
                <PhStar :size="14" weight="fill" class="text-amber-400" />
                {{ detail?.rating?.toFixed(1) ?? '--' }}
                <span>· {{ (detail?.servedCount ?? 0).toLocaleString() }} orders</span>
              </span>
            </div>
            <div class="mt-4 flex items-center gap-2">
              <UButton color="neutral" variant="soft" block class="rounded-full" disabled>Edit</UButton>
              <UButton
                color="neutral"
                variant="soft"
                square
                class="rounded-full"
                :aria-label="`Delete ${service.name}`"
                @click="askDelete({ id: service.id, name: service.name })"
              >
                <PhTrash :size="16" weight="bold" />
              </UButton>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal
      v-model:open="deleteOpen"
      :icon="PhTrash"
      :title="`Delete ${deleteTarget?.name}?`"
      description="Buyers won't be able to find or book this service anymore. This can't be undone."
      confirm-label="Delete"
      destructive
      @confirm="handleDelete"
    />
  </DashboardLayout>
</template>
