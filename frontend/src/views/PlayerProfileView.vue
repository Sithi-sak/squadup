<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { mockPlayers } from '@/mocks/players'
import { fallbackServiceDetail, getPlayerProfile } from '@/mocks/playerProfiles'
import ProfileHeader from '@/components/players/ProfileHeader.vue'
import ProfileServiceSidebar from '@/components/players/ProfileServiceSidebar.vue'
import ProfileServicesTab from '@/components/players/ProfileServicesTab.vue'
import ProfileFeedsTab from '@/components/players/ProfileFeedsTab.vue'
import ProfileAlbumTab from '@/components/players/ProfileAlbumTab.vue'
import ProfileWishTab from '@/components/players/ProfileWishTab.vue'

const route = useRoute()

const player = computed(
  () => mockPlayers.find((p) => p.id === route.params.id) ?? mockPlayers[0]!,
)
const profile = computed(() => getPlayerProfile(player.value))

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
    profile.value.services.find((s) => s.id === selectedServiceId.value) ?? profile.value.services[0]!,
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
  <div class="mx-auto max-w-(--content-max-width) px-4 pt-8 pb-14 md:px-6">
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
        :service-id="selectedServiceId"
        :detail="selectedDetail"
        :reviews="selectedReviews"
      />
      <ProfileFeedsTab v-else-if="activeTab === 'feeds'" :player="player" :feed="profile.feed" />
      <ProfileAlbumTab v-else-if="activeTab === 'album'" :album="profile.album" />
      <ProfileWishTab v-else-if="activeTab === 'wish'" :player-id="player.id" :wish="profile.wish" />
    </div>
  </div>
</template>
