<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  PhMagnifyingGlass,
  PhRocketLaunch,
  PhFileText,
  PhGear,
  PhShieldCheck,
  PhStar,
} from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'

const router = useRouter()

const popularSearches = [
  { label: 'Squad Coin', category: 'Squad Coin' },
  { label: 'Refunds', category: 'Booking & orders' },
  { label: 'Become a Pal', category: 'Becoming a Pal' },
  { label: 'Cancel an order', category: 'Booking & orders' },
]

const topics = [
  {
    icon: PhRocketLaunch,
    title: 'Getting started',
    description: 'Create an account, find a Pal, and place your first order.',
    articles: 12,
    category: 'Getting started',
  },
  {
    icon: PhFileText,
    title: 'Orders & payments',
    description: 'Booking, checkout, refunds, and disputes.',
    articles: 18,
    category: 'Booking & orders',
  },
  {
    icon: 'coin',
    title: 'Squad Coin',
    description: 'Top up, spend, cash out, and coin bonuses.',
    articles: 9,
    category: 'Squad Coin',
  },
  {
    icon: PhStar,
    title: 'Becoming a Pal',
    description: 'Apply, set up services, and start earning.',
    articles: 15,
    category: 'Becoming a Pal',
  },
  {
    icon: PhShieldCheck,
    title: 'Safety & trust',
    description: 'Verification, reporting, and community rules.',
    articles: 11,
    category: 'Safety',
  },
  {
    icon: PhGear,
    title: 'Account & settings',
    description: 'Profile, security, notifications, and privacy.',
    articles: 10,
    category: 'Getting started',
  },
]

const popularQuestions = [
  {
    question: 'What is Squad Coin and how do I get it?',
    answer:
      'Squad Coin (SC) is the in-app currency used to pay Pals. 99 SC is about $1. Top up from your Wallet with card, Apple Pay, or Google Pay, bonus coins are added on larger packs. Coins never expire and can be cashed out by Pals.',
  },
  {
    question: 'How do refunds work?',
    answer:
      'If a Pal cancels or a session does not happen as booked, open the order from My Bookings and contact support. Refunds are issued back to your Squad Coin balance.',
  },
  {
    question: 'How do I become a Pal and get paid?',
    answer:
      'Apply from the Become a Pal page with your main game, rank, and a short bio. Once approved, set up services and rates, then get paid in Squad Coin as orders come in.',
  },
  {
    question: 'Is my payment information secure?',
    answer:
      'Card details are handled by our payment partners and never stored on SquadUp servers. You can review saved cards and active sessions any time from Settings.',
  },
  {
    question: 'Can I cancel an order after booking?',
    answer:
      'Yes, cancel from My Bookings before a Pal accepts for a full refund. Once accepted, cancellations follow the refund policy for that service.',
  },
]

const accordionItems = computed(() =>
  popularQuestions.map((item) => ({ label: item.question, content: item.answer })),
)

function goToTopic(category: string) {
  router.push({ path: '/faq', query: { category } })
}
</script>

<template>
  <div class="flex flex-col">
    <section
      class="px-4 py-16 text-center md:px-6 md:py-20"
      style="
        background: radial-gradient(
            ellipse 70% 60% at 50% 0%,
            color-mix(in srgb, var(--color-brand-600) 25%, transparent),
            transparent
          ),
          var(--color-squadup-bg);
      "
    >
      <h1 class="text-4xl font-bold text-white">How can we help?</h1>

      <div class="mx-auto mt-6 flex max-w-xl items-center gap-2 rounded-full border border-white/10 bg-white/5 py-1.5 pr-1.5 pl-5">
        <PhMagnifyingGlass :size="18" class="shrink-0 text-slate-400" />
        <input
          type="text"
          placeholder="Search for answers..."
          class="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-400"
        />
        <UButton color="primary" class="rounded-full px-5">Search</UButton>
      </div>

      <div class="mt-4 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-sm text-slate-400">
        <span>Popular:</span>
        <button
          v-for="term in popularSearches"
          :key="term.label"
          type="button"
          class="cursor-pointer text-white underline-offset-2 hover:underline"
          @click="goToTopic(term.category)"
        >
          {{ term.label }}
        </button>
      </div>
    </section>

    <section class="px-4 py-14 md:px-6">
      <div class="mx-auto max-w-2/3">
        <h2 class="text-center text-2xl font-bold text-white">Browse by topic</h2>

        <div class="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <button
            v-for="topic in topics"
            :key="topic.title"
            type="button"
            class="cursor-pointer rounded-2xl bg-white/5 p-6 text-left transition-colors hover:bg-white/10"
            @click="goToTopic(topic.category)"
          >
            <div class="flex gap-2 mb-4">
              <div class="flex items-center">
                <img v-if="topic.icon === 'coin'" :src="coinIcon" alt="" class="h-5.5 w-5.5" />
                <component :is="topic.icon" v-else :size="24" weight="fill" class="text-brand-300" />
              </div>
              <h3 class="text-md font-medium text-white">{{ topic.title }}</h3>
            </div>
            <p class="mt-1 text-sm leading-relaxed text-slate-400">{{ topic.description }}</p>
            <span class="mt-3 inline-block text-sm font-medium text-brand-400">
              {{ topic.articles }} articles
            </span>
          </button>
        </div>
      </div>
    </section>

    <section class="px-4 pb-14 md:px-6">
      <div class="mx-auto max-w-3xl">
        <h2 class="text-center text-2xl font-bold text-white">Popular questions</h2>

        <UAccordion
          :items="accordionItems"
          default-value="0"
          class="mt-8"
          :ui="{
            root: 'flex flex-col gap-3',
            item: 'rounded-2xl border-0 bg-white/5 px-5',
            trigger: 'py-4 text-[15px] font-medium text-white',
            body: 'pb-4 text-sm leading-relaxed text-slate-300',
          }"
        />

        <div
          class="mt-8 flex flex-col items-center justify-between gap-4 rounded-2xl bg-white/5 p-6 text-center sm:flex-row sm:text-left"
        >
          <div>
            <h3 class="text-lg font-bold text-white">Still need help?</h3>
            <p class="mt-1 text-sm text-slate-400">Our support team replies within a few hours, every day.</p>
          </div>
          <div class="flex shrink-0 gap-2">
            <UButton color="neutral" variant="soft" class="rounded-full px-5">Community</UButton>
            <UButton color="primary" class="rounded-full px-5">Contact support</UButton>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
