<script setup lang="ts">
import { PhBug, PhFlag, PhLockSimple, PhReceipt, PhShieldWarning, PhUserFocus } from '@phosphor-icons/vue'

const categories = [
  {
    icon: PhUserFocus,
    title: 'A Pal or a user',
    body: 'Harassment, a scam, impersonation or anything that made a session feel unsafe. Open their profile and use the Report button so the safety team gets the account with it.',
    action: { label: 'Find the profile', to: '/players' },
  },
  {
    icon: PhReceipt,
    title: 'An order that went wrong',
    body: 'A Pal did not show up, ended early, or the session was not what was sold. Reporting from the order lets us see the booking, the chat and the payment together.',
    action: { label: 'Go to my orders', to: '/bookings' },
  },
  {
    icon: PhFlag,
    title: 'A post or comment',
    body: 'Use the menu on the post itself. Flagged posts are hidden from your feed straight away while a moderator reviews them.',
    action: { label: 'Open the feed', to: '/feed' },
  },
  {
    icon: PhBug,
    title: 'A bug or a payment error',
    body: 'Squad Coin that did not arrive, a screen that will not load, a charge you do not recognise. Include your order number and what you were doing.',
    action: { label: 'support@squadup.gg', href: 'mailto:support@squadup.gg' },
  },
]

const steps = [
  'Your report reaches the safety team, not the person you reported.',
  'We review the account, the session and anything attached to it, usually within 24 hours.',
  'Serious cases get the account suspended while we look, and payments held.',
  'You get the outcome in your notifications once the case closes.',
]
</script>

<template>
  <div class="px-4 py-14 md:px-6 md:py-20">
    <div class="mx-auto max-w-3xl">
      <div class="text-center">
        <span
          class="inline-flex items-center rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300"
        >
          Report
        </span>
        <h1 class="mt-4 text-4xl font-bold text-white">Report a problem</h1>
        <p class="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-300">
          Tell us what happened and we will take it from there. Pick what you are reporting so it
          lands with the right team.
        </p>
      </div>

      <div
        class="mx-auto mt-8 flex max-w-fit items-start gap-2.5 rounded-full bg-brand-900/20 p-4 text-sm text-brand-300"
      >
        <PhLockSimple :size="18" weight="fill" class="mt-0.5 shrink-0" />
        <p>Reports are confidential. The person you report is never told who filed it.</p>
      </div>

      <div class="mt-8 flex flex-col gap-3">
        <div
          v-for="category in categories"
          :key="category.title"
          class="flex flex-col gap-4 rounded-2xl bg-white/5 p-6 sm:flex-row sm:items-center"
        >
          <span
            class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-brand-300"
          >
            <component :is="category.icon" :size="32" weight="fill" />
          </span>
          <div class="flex-1">
            <h2 class="font-semibold text-white">{{ category.title }}</h2>
            <p class="mt-1 text-sm leading-relaxed text-slate-300">{{ category.body }}</p>
          </div>
          <UButton
            v-if="category.action.to"
            :to="category.action.to"
            color="neutral"
            variant="soft"
            class="shrink-0 rounded-full px-5"
          >
            {{ category.action.label }}
          </UButton>
          <UButton
            v-else
            :href="category.action.href"
            color="neutral"
            variant="soft"
            class="shrink-0 rounded-full px-5"
          >
            {{ category.action.label }}
          </UButton>
        </div>
      </div>

      <section class="mt-12">
        <h2 class="text-xl font-bold text-white">What happens after you report</h2>
        <ol class="mt-4 flex flex-col gap-3">
          <li
            v-for="(step, index) in steps"
            :key="step"
            class="flex gap-3 rounded-2xl bg-white/5 p-5"
          >
            <span
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
            >
              {{ index + 1 }}
            </span>
            <p class="text-sm leading-relaxed text-slate-300">{{ step }}</p>
          </li>
        </ol>
      </section>

      <section
        class="mt-12 flex flex-col gap-4 rounded-md bg-amber-900/20 p-6 ring-red-600/50 sm:flex-row sm:items-center"
      >
        <span
          class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-amber-300"
        >
          <PhShieldWarning :size="32" weight="fill" />
        </span>
        <div class="flex-1">
          <h2 class="font-semibold text-white">Someone is in danger</h2>
          <p class="mt-1 text-sm leading-relaxed text-slate-300">
            If there is a risk to someone's safety, contact your local emergency services first,
            then write to us so we can act on the account.
          </p>
        </div>
        <UButton
          href="mailto:safety@squadup.gg"
          color="neutral"
          variant="soft"
          class="shrink-0 rounded-full px-5"
        >
          safety@squadup.gg
        </UButton>
      </section>
    </div>
  </div>
</template>
