<script setup lang="ts">
import { computed } from 'vue'
import { PhFlag, PhScales, PhCurrencyCircleDollar, PhUserPlus } from '@phosphor-icons/vue'
import { formatNotificationTime } from '@/utils/notifications'
import { useAdminStore } from '@/stores/admin'
import type { AdminNotification, AdminNotificationType, AdminTabKey } from '@/mocks/admin'

const props = defineProps<{ close?: () => void }>()
const emit = defineEmits<{ 'open-tab': [AdminTabKey] }>()

const adminStore = useAdminStore()

/** Same colour language as the user-facing bell (`utils/notifications.ts`): money green,
 * anything needing a call amber or red. Full class strings, Tailwind only sees literals. */
const icon: Record<AdminNotificationType, typeof PhFlag> = {
  report: PhFlag,
  dispute: PhScales,
  payout: PhCurrencyCircleDollar,
  application: PhUserPlus,
}

const tone: Record<AdminNotificationType, string> = {
  report: 'bg-red-500/15 text-red-300',
  dispute: 'bg-amber-500/15 text-amber-300',
  payout: 'bg-emerald-500/15 text-emerald-300',
  application: 'bg-sky-500/15 text-sky-300',
}

const rows = computed(() => adminStore.notifications.slice(0, 8))
const hiddenCount = computed(() => adminStore.notifications.length - rows.value.length)

/** A click opens the queue that resolves the alert, which is also what retires it - deciding
 * the item removes it from the feed on the next fetch. */
function handleClick(alert: AdminNotification) {
  adminStore.markNotificationRead(alert.id)
  emit('open-tab', alert.tab)
  props.close?.()
}
</script>

<template>
  <div class="flex w-80 flex-col sm:w-96">
    <div class="flex items-center justify-between gap-3 px-4 pt-4">
      <h3 class="flex items-center gap-2 text-lg font-bold text-white">
        Alerts
        <span
          v-if="adminStore.unreadNotificationCount > 0"
          class="flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-500 px-1.5 text-[11px] font-semibold text-white"
        >
          {{ adminStore.unreadNotificationCount }}
        </span>
      </h3>
      <button
        type="button"
        class="cursor-pointer text-sm font-medium text-brand-400 hover:text-brand-300 disabled:cursor-not-allowed disabled:text-slate-500 disabled:hover:text-slate-500"
        :disabled="adminStore.unreadNotificationCount === 0"
        @click="adminStore.markAllNotificationsRead()"
      >
        Mark all read
      </button>
    </div>

    <p class="px-4 pt-1 text-xs text-slate-400">Everything waiting on a decision</p>

    <div class="mt-3 max-h-96 overflow-y-auto border-t border-white/10">
      <div
        v-if="adminStore.notificationsLoading && rows.length === 0"
        class="divide-y divide-white/5"
      >
        <div v-for="n in 3" :key="n" class="flex items-start gap-3 px-4 py-3">
          <USkeleton class="h-9 w-9 shrink-0 rounded-full" />
          <div class="min-w-0 flex-1 space-y-2">
            <USkeleton class="h-3.5 w-4/5" />
            <USkeleton class="h-3 w-16" />
          </div>
        </div>
      </div>

      <p v-else-if="rows.length === 0" class="px-4 py-8 text-center text-sm text-slate-400">
        Nothing needs attention right now.
      </p>

      <template v-else>
        <div
          v-for="alert in rows"
          :key="alert.id"
          class="relative border-b border-white/5 last:border-b-0"
          :class="
            adminStore.isNotificationRead(alert.id)
              ? 'hover:bg-white/5'
              : 'bg-brand-500/[0.07] hover:bg-brand-500/10'
          "
        >
          <span
            v-if="!adminStore.isNotificationRead(alert.id)"
            class="absolute inset-y-0 left-0 w-0.5 bg-brand-400"
            aria-hidden="true"
          />
          <button
            type="button"
            class="flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left"
            @click="handleClick(alert)"
          >
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
              :class="tone[alert.type]"
            >
              <component :is="icon[alert.type]" :size="18" weight="bold" />
            </span>
            <span class="min-w-0 flex-1">
              <span
                class="block text-sm"
                :class="
                  adminStore.isNotificationRead(alert.id)
                    ? 'text-slate-300'
                    : 'font-medium text-white'
                "
              >
                {{ alert.title }}
              </span>
              <span class="mt-0.5 line-clamp-2 block text-sm text-slate-400">{{
                alert.message
              }}</span>
              <span class="mt-0.5 block text-xs text-slate-500">{{
                formatNotificationTime(alert.createdAt)
              }}</span>
            </span>
          </button>
        </div>
      </template>
    </div>

    <div
      v-if="hiddenCount > 0"
      class="border-t border-white/10 px-4 py-3 text-center text-sm text-slate-400"
    >
      {{ hiddenCount }} more waiting in the tabs
    </div>
  </div>
</template>
