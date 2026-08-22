<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { PhMagnifyingGlass } from '@phosphor-icons/vue'

const route = useRoute()

const categories = [
  'All',
  'Getting started',
  'Booking & orders',
  'Squad Coin',
  'Becoming a Pal',
  'Safety',
]

const activeCategory = ref('All')

watchEffect(() => {
  const category = route.query.category
  if (typeof category === 'string' && categories.includes(category)) {
    activeCategory.value = category
  }
})

const searchQuery = ref('')

const faqs = [
  {
    question: 'What is SquadUp?',
    category: 'Getting started',
    answer:
      'SquadUp is a marketplace where you can book top-tier gaming companions, we call them Pals, for ranked duos, coaching, and casual play. Browse Pals by game, rank, and price, then book in seconds and never play solo again.',
  },
  {
    question: 'How do I book a Pal?',
    category: 'Booking & orders',
    answer:
      'Browse Pals from the Discover or Games page, open a profile, and pick a service. Choose a quantity and any add-ons, then continue to checkout to confirm your order.',
  },
  {
    question: 'What is Squad Coin (SC)?',
    category: 'Squad Coin',
    answer:
      'Squad Coin (SC) is the in-app currency used to pay Pals. 99 SC is about $1. Top up your Wallet with a card, Apple Pay, or Google Pay. Coins never expire and can be cashed out by Pals.',
  },
  {
    question: 'Is my first order really free?',
    category: 'Booking & orders',
    answer:
      'New accounts get a first order discount shown on select services as a promo badge. The discount applies automatically at checkout, no promo code needed.',
  },
  {
    question: 'How do payouts work for Pals?',
    category: 'Becoming a Pal',
    answer:
      'Pals earn Squad Coin for every completed order. Earnings are tracked on the Player Dashboard and can be cashed out to a linked payout method once a session is marked complete.',
  },
  {
    question: 'How does SquadUp keep me safe?',
    category: 'Safety',
    answer:
      'All Pals go through an application and verification step before they can accept orders. Payments stay inside SquadUp until a session is complete, and you can report or block anyone from a profile or chat.',
  },
  {
    question: 'Can I get a refund?',
    category: 'Booking & orders',
    answer:
      'If a Pal cancels or a session does not happen as booked, open the order from My Bookings and contact support. Refunds are issued back to your Squad Coin balance.',
  },
  {
    question: 'How do I become a Pal?',
    category: 'Becoming a Pal',
    answer:
      'Apply from the Become a Pal page with your main game, rank, and a short bio. Applications are reviewed in 24 to 48 hours, then you can set up services and start earning.',
  },
]

const filteredFaqs = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return faqs.filter((faq) => {
    const matchesCategory = activeCategory.value === 'All' || faq.category === activeCategory.value
    const matchesQuery =
      !query ||
      faq.question.toLowerCase().includes(query) ||
      faq.answer.toLowerCase().includes(query)
    return matchesCategory && matchesQuery
  })
})

const accordionItems = computed(() =>
  filteredFaqs.value.map((faq) => ({ label: faq.question, content: faq.answer })),
)
</script>

<template>
  <div class="px-4 py-14 md:px-6 md:py-20">
    <div class="mx-auto max-w-3xl">
      <div class="text-center">
        <span
          class="inline-flex items-center rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300 ring-1 ring-inset ring-brand-700"
        >
          Help Center
        </span>
        <h1 class="mt-4 text-4xl font-bold text-white">How can we help?</h1>
        <p class="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-300">
          Answers to the most common questions about booking Pals, Squad Coin, payouts, and
          staying safe on SquadUp.
        </p>
      </div>

      <div class="mx-auto mt-8 flex max-w-xl items-center gap-2 rounded-full border border-white/10 bg-white/5 py-1.5 pr-1.5 pl-5">
        <PhMagnifyingGlass :size="18" class="shrink-0 text-slate-400" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search for a question..."
          class="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-400"
        />
        <UButton color="primary" class="rounded-full px-5">Search</UButton>
      </div>

      <div class="mt-5 flex flex-wrap justify-center gap-2">
        <button
          v-for="category in categories"
          :key="category"
          type="button"
          class="cursor-pointer rounded-full px-4 py-1.5 text-[13px] transition-colors"
          :class="
            activeCategory === category
              ? 'bg-brand-600 text-white'
              : 'bg-white/5 text-slate-300 hover:text-white'
          "
          @click="activeCategory = category"
        >
          {{ category }}
        </button>
      </div>

      <UAccordion
        v-if="accordionItems.length"
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
      <p v-else class="mt-8 text-center text-sm text-slate-400">
        No questions match your search yet. Try a different keyword or category.
      </p>

      <div
        class="mt-8 flex flex-col items-center justify-between gap-4 rounded-2xl bg-linear-to-r from-brand-900/60 to-brand-700/30 p-6 text-center ring-1 ring-inset ring-brand-700/40 sm:flex-row sm:text-left"
      >
        <div>
          <h3 class="text-lg font-bold text-white">Still have questions?</h3>
          <p class="mt-1 text-sm text-slate-300">Our support team replies in under 10 minutes, 24/7.</p>
        </div>
        <UButton to="/help" color="primary" class="shrink-0 rounded-full px-5">
          Contact support
        </UButton>
      </div>
    </div>
  </div>
</template>
