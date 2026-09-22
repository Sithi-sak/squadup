<script setup lang="ts">
import {
  PhChatCircleDots,
  PhClockCountdown,
  PhEnvelopeSimple,
  PhLifebuoy,
  PhReceipt,
  PhWallet,
} from '@phosphor-icons/vue'

const channels = [
  {
    icon: PhChatCircleDots,
    title: 'Message us in the app',
    body: 'The fastest route for anything tied to a booking. Open the order and use Get help, so the agent can see the session straight away.',
    action: { label: 'Go to my orders', to: '/bookings' },
  },
  {
    icon: PhEnvelopeSimple,
    title: 'Email support',
    body: 'For account, payment or privacy questions. Write from the address on your account and include your order number if there is one.',
    action: { label: 'support@squadup.gg', href: 'mailto:support@squadup.gg' },
  },
  {
    icon: PhLifebuoy,
    title: 'Help Center',
    body: 'Step-by-step guides for booking, refunds, Squad Coin and becoming a Pal. Most questions are answered here in under a minute.',
    action: { label: 'Browse guides', to: '/help' },
  },
]

const quickLinks = [
  { icon: PhReceipt, label: 'Cancel or refund an order', to: '/bookings' },
  { icon: PhWallet, label: 'Squad Coin and payouts', to: { path: '/faq', query: { category: 'Squad Coin' } } },
  { icon: PhClockCountdown, label: 'A Pal did not show up', to: '/bookings' },
  { icon: PhLifebuoy, label: 'Something else', to: '/help' },
]

const hours = [
  { label: 'Live chat', value: 'Every day, 9:00 to 23:00 (ICT)' },
  { label: 'Email', value: 'Answered within 24 hours' },
  { label: 'Payment and payout issues', value: 'Answered within 12 hours' },
]
</script>

<template>
  <div class="px-4 py-14 md:px-6 md:py-20">
    <div class="mx-auto max-w-3xl">
      <div class="text-center">
        <span
          class="inline-flex items-center rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300"
        >
          Customer Service
        </span>
        <h1 class="mt-4 text-4xl font-bold text-white">Talk to a human</h1>
        <p class="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-300">
          Pick the route that matches your problem and we will pick it up from there.
        </p>
      </div>

      <div class="mt-10 flex flex-col gap-3">
        <div
          v-for="channel in channels"
          :key="channel.title"
          class="flex flex-col gap-4 rounded-2xl bg-white/5 p-6 sm:flex-row sm:items-center"
        >
          <span
            class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-brand-300"
          >
            <component :is="channel.icon" :size="32" weight="fill" />
          </span>
          <div class="flex-1">
            <h2 class="font-semibold text-white">{{ channel.title }}</h2>
            <p class="mt-1 text-sm leading-relaxed text-slate-300">{{ channel.body }}</p>
          </div>
          <UButton
            v-if="channel.action.to"
            :to="channel.action.to"
            color="neutral"
            variant="soft"
            class="shrink-0 rounded-full px-5"
          >
            {{ channel.action.label }}
          </UButton>
          <UButton
            v-else
            :href="channel.action.href"
            color="neutral"
            variant="soft"
            class="shrink-0 rounded-full px-5"
          >
            {{ channel.action.label }}
          </UButton>
        </div>
      </div>

      <section class="mt-12">
        <h2 class="text-xl font-bold text-white">Common requests</h2>
        <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <router-link
            v-for="link in quickLinks"
            :key="link.label"
            :to="link.to"
            class="flex items-center gap-3 rounded-xl bg-white/5 px-5 py-4 text-sm text-white transition-colors hover:bg-white/10"
          >
            <component :is="link.icon" :size="24" class="shrink-0 text-brand-300" />
            {{ link.label }}
          </router-link>
        </div>
      </section>

      <section class="mt-12 rounded-2xl bg-white/5 p-6">
        <h2 class="font-semibold text-white">When to expect a reply</h2>
        <dl class="mt-3 flex flex-col gap-2">
          <div
            v-for="row in hours"
            :key="row.label"
            class="flex flex-col gap-0.5 border-b border-white/5 pb-2 last:border-0 last:pb-0 sm:flex-row sm:justify-between"
          >
            <dt class="text-sm text-slate-300">{{ row.label }}</dt>
            <dd class="text-sm font-medium text-white">{{ row.value }}</dd>
          </div>
        </dl>
      </section>

      <p class="mt-8 text-center text-sm text-slate-400">
        Reporting harassment, a scam or a safety concern?
        <router-link to="/report" class="text-brand-300 hover:text-white">
          Use the report page
        </router-link>
        instead, it goes straight to the safety team.
      </p>
    </div>
  </div>
</template>
