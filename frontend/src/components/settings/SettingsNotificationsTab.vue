<script setup lang="ts">
import { ref } from 'vue'
import SettingsToggleRow from './SettingsToggleRow.vue'
import SettingsSelectRow from './SettingsSelectRow.vue'

const newOrders = ref(true)
const messages = ref(true)
const orderUpdates = ref(true)
const reviews = ref(true)
const promotions = ref(false)

const weeklySummary = ref(true)
const payoutReceipts = ref(true)
const productNews = ref(false)

const notificationSound = ref('Default')
const quietHours = ref('10:00 PM – 8:00 AM')

const soundOptions = ['Default', 'Chime', 'Ping', 'Silent']
const quietHoursOptions = ['Off', '10:00 PM – 8:00 AM', '11:00 PM – 7:00 AM', 'Midnight – 8:00 AM']
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Push notifications</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsToggleRow v-model="newOrders" label="New orders" description="When a buyer books one of your services." />
        <SettingsToggleRow v-model="messages" label="Messages" description="New direct messages from buyers." />
        <SettingsToggleRow v-model="orderUpdates" label="Order updates" description="Accepts, reschedules and completions." />
        <SettingsToggleRow v-model="reviews" label="Reviews" description="When someone rates a session." />
        <SettingsToggleRow v-model="promotions" label="Promotions & tips" description="Offers and product suggestions." />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Email notifications</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsToggleRow v-model="weeklySummary" label="Weekly summary" description="Your earnings and stats each Monday." />
        <SettingsToggleRow v-model="payoutReceipts" label="Payout receipts" description="A receipt every time you get paid." />
        <SettingsToggleRow v-model="productNews" label="Product news" description="Feature launches and announcements." />
      </div>
    </div>

    <div class="rounded-xl bg-gray-800/70 p-5">
      <h2 class="text-lg font-semibold text-white">Preferences</h2>
      <div class="flex flex-col divide-y divide-white/10">
        <SettingsSelectRow v-model="notificationSound" label="Notification sound" :items="soundOptions" />
        <SettingsSelectRow v-model="quietHours" label="Quiet hours" :items="quietHoursOptions" />
      </div>
    </div>
  </div>
</template>
