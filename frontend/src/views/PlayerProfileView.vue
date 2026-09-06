<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fallbackServiceDetail } from '@/mocks/playerProfiles'
import { usePlayerProfileData } from '@/composables/usePlayerProfileData'
import ProfileHeader from '@/components/players/ProfileHeader.vue'
import ProfileServiceSidebar from '@/components/players/ProfileServiceSidebar.vue'
import ProfileServicesTab from '@/components/players/ProfileServicesTab.vue'
import ProfileFeedsTab from '@/components/players/ProfileFeedsTab.vue'
import ProfileAlbumTab from '@/components/players/ProfileAlbumTab.vue'
import ProfileWishTab from '@/components/players/ProfileWishTab.vue'

const route = useRoute()

const playerId = computed(() => String(route.params.id))
const { loading, player, profile, isMockProfile } = usePlayerProfileData(playerId)

const tabItems = [
  { label: 'Services', value: 'services' },
  { label: 'Feeds', value: 'feeds' },
  { label: 'Album', value: 'album' },
  { label: 'Wish', value: 'wish' },
]
const activeTab = ref('services')

const selectedServiceId = ref(profile.value.highlightedServiceId)
watch(profile, (p) => (selectedServiceId.value = p.highlightedServiceId))

const selectedService = computed(
  () =>
    profile.value.services.find((s) => s.id === selectedServiceId.value) ??
    profile.value.services[0]!,
)
const selectedDetail = computed(
  () =>
    profile.value.serviceDetails[selectedServiceId.value] ??
    fallbackServiceDetail(
      selectedService.value.name,
      selectedService.value.priceCoins,
      selectedService.value.priceUnit,
      selectedService.value.promoBadge,
    ),
)
const selectedReviews = computed(() => profile.value.reviews[selectedServiceId.value] ?? [])
</script>

<template>
  <div class="mx-auto max-w-4/5 px-4 pt-8 pb-14 md:px-6">
    <div v-if="loading">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex items-start gap-4">
          <USkeleton class="h-20 w-20 shrink-0 rounded-full" />
          <div class="flex flex-col gap-2 pt-1">
            <USkeleton class="h-7 w-40" />
            <USkeleton class="h-4 w-56" />
            <div class="mt-1 flex gap-2">
              <USkeleton class="h-5 w-16 rounded-full" />
              <USkeleton class="h-5 w-12 rounded-full" />
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <USkeleton class="h-9 w-9 rounded-full" />
          <USkeleton class="h-9 w-9 rounded-full" />
          <USkeleton class="h-9 w-9 rounded-full" />
        </div>
      </div>

      <div class="mt-6 flex w-fit gap-6">
        <USkeleton v-for="n in 4" :key="n" class="h-5 w-16" />
      </div>

      <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <div class="rounded-xl bg-gray-800/70 p-3">
          <USkeleton class="h-9 w-full rounded-full" />
          <div class="mt-3 flex flex-col gap-3">
            <div v-for="n in 4" :key="n" class="flex items-center gap-3 p-2">
              <USkeleton class="h-10 w-10 shrink-0 rounded-full" />
              <div class="flex-1 space-y-1.5">
                <USkeleton class="h-4 w-24" />
                <USkeleton class="h-3 w-16" />
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
          <div class="flex flex-col gap-4">
            <div class="rounded-xl bg-gray-800/70 p-5">
              <USkeleton class="h-7 w-48" />
              <USkeleton class="mt-3 h-4 w-32" />
              <USkeleton class="mt-4 h-4 w-full" />
              <USkeleton class="mt-2 h-4 w-3/4" />
              <div class="mt-4 flex flex-col gap-2">
                <USkeleton class="h-4 w-full" />
                <USkeleton class="h-4 w-full" />
              </div>
            </div>
            <div class="rounded-xl bg-gray-800/70 p-5">
              <USkeleton class="h-5 w-36" />
              <USkeleton class="mt-3 h-12 w-full rounded-full" />
            </div>
            <div class="rounded-xl bg-gray-800/70 p-5">
              <USkeleton class="h-5 w-28" />
              <div class="mt-3 flex items-center gap-3">
                <USkeleton class="h-10 w-10 shrink-0 rounded-full" />
                <div class="flex-1 space-y-1.5">
                  <USkeleton class="h-4 w-24" />
                  <USkeleton class="h-3 w-16" />
                </div>
              </div>
            </div>
          </div>
          <div class="flex flex-col gap-4">
            <USkeleton class="aspect-video w-full rounded-xl" />
            <div class="rounded-xl bg-gray-800/70 p-4">
              <USkeleton class="h-11 w-full rounded-full" />
              <USkeleton class="mt-2.5 h-11 w-full rounded-full" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <template v-else>
      <ProfileHeader :player="player" :profile="profile" />

      <UTabs
        v-model="activeTab"
        variant="link"
        :items="tabItems"
        :content="false"
        class="mt-6 w-fit"
        :ui="{ label: 'text-white' }"
      />

      <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <ProfileServiceSidebar
          :services="profile.services"
          :selected-id="selectedServiceId"
          @select="selectedServiceId = $event"
        />

        <ProfileServicesTab
          v-if="activeTab === 'services'"
          :player-id="player.id"
          :player-user-id="profile.userId"
          :service-id="selectedServiceId"
          :detail="selectedDetail"
          :reviews="selectedReviews"
        />
        <ProfileFeedsTab
          v-else-if="activeTab === 'feeds'"
          :player="player"
          :handle="profile.handle"
          :feed="profile.feed"
        />
        <ProfileAlbumTab v-else-if="activeTab === 'album'" :album="profile.album" />
        <ProfileWishTab
          v-else-if="activeTab === 'wish'"
          :player-id="player.id"
          :wish="profile.wish"
          :mock-toggle="isMockProfile"
        />
      </div>
    </template>
  </div>
</template>
