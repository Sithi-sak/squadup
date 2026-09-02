<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

type LegalSection = { id: string; title: string; paragraphs: string[] }
type LegalTab = 'terms' | 'privacy' | 'guidelines'

const tabs: { label: string; value: LegalTab }[] = [
  { label: 'Terms of Service', value: 'terms' },
  { label: 'Privacy Policy', value: 'privacy' },
  { label: 'Community Guidelines', value: 'guidelines' },
]

const route = useRoute()
const validTabs: LegalTab[] = ['terms', 'privacy', 'guidelines']
const initialTab = validTabs.includes(route.query.tab as LegalTab)
  ? (route.query.tab as LegalTab)
  : 'terms'

const activeTab = ref<LegalTab>(initialTab)

const termsSections: LegalSection[] = [
  {
    id: 'introduction',
    title: '1. Introduction',
    paragraphs: [
      'Welcome to SquadUp. These Terms of Service ("Terms") govern your access to and use of the SquadUp website, apps, and services (the "Platform"), operated by SquadUp Inc. By creating an account or using the Platform, you agree to be bound by these Terms.',
      'SquadUp connects players ("Buyers") with gaming companions and coaches ("Pals") for paid gaming and social sessions. SquadUp is a marketplace and is not a party to the agreements formed between Buyers and Pals.',
    ],
  },
  {
    id: 'eligibility',
    title: '2. Eligibility',
    paragraphs: [
      'You must be at least 16 years old to use the Platform, and at least 18 to become a Pal or withdraw earnings. By using SquadUp you represent that you meet these requirements and that the information you provide is accurate and complete.',
    ],
  },
  {
    id: 'your-account',
    title: '3. Your account',
    paragraphs: [
      'You are responsible for maintaining the confidentiality of your login credentials and for all activity that occurs under your account. Notify us immediately of any unauthorized use. We may suspend or terminate accounts that violate these Terms.',
    ],
  },
  {
    id: 'squad-coin',
    title: '4. Squad Coin & payments',
    paragraphs: [
      'Squad Coin ("SC") is a prepaid virtual currency used to pay for services on the Platform. SC has no cash value outside SquadUp except where Pals cash out eligible earnings. Purchases of SC are final, unused SC remains in your wallet and does not expire. Pal earnings are subject to a service fee disclosed at checkout.',
    ],
  },
  {
    id: 'pal-services',
    title: '5. Pal services',
    paragraphs: [
      'Pals set their own prices, availability, and service descriptions. Pals must deliver services as described and comply with our Community Guidelines. SquadUp does not guarantee the quality of any service and is not responsible for interactions that occur off-Platform.',
    ],
  },
  {
    id: 'prohibited-conduct',
    title: '6. Prohibited conduct',
    paragraphs: [
      'You may not use the Platform to harass, threaten, or defraud another user, circumvent Squad Coin to pay off-Platform, share another user\'s private information, or misrepresent your identity, rank, or credentials.',
    ],
  },
  {
    id: 'refunds-disputes',
    title: '7. Refunds & disputes',
    paragraphs: [
      'Orders can be cancelled for a full refund before a Pal accepts. Once a session has started, refunds are handled case by case through Contact Support based on whether the service was delivered as described.',
    ],
  },
  {
    id: 'termination',
    title: '8. Termination',
    paragraphs: [
      'We may suspend or terminate your access to the Platform at any time for violating these Terms or the Community Guidelines. You may close your account at any time from Settings, unused Squad Coin is handled per section 4.',
    ],
  },
  {
    id: 'liability',
    title: '9. Liability',
    paragraphs: [
      'The Platform is provided "as is." To the extent permitted by law, SquadUp is not liable for indirect or consequential damages arising from your use of the Platform or interactions with other users.',
    ],
  },
  {
    id: 'contact-us',
    title: '10. Contact us',
    paragraphs: [
      'Questions about these Terms can be sent to our support team through the Help Center or Contact Support.',
    ],
  },
]

const privacySections: LegalSection[] = [
  {
    id: 'information-we-collect',
    title: '1. Information we collect',
    paragraphs: [
      'We collect the information you provide when creating an account or a Pal profile (name, email, phone, payout details), plus usage data like bookings, messages, and device information needed to operate the Platform.',
    ],
  },
  {
    id: 'how-we-use-it',
    title: '2. How we use it',
    paragraphs: [
      'We use your information to run bookings and payments, match Buyers with Pals, keep the Platform safe, and communicate updates about your orders and account.',
    ],
  },
  {
    id: 'sharing',
    title: '3. Sharing',
    paragraphs: [
      'We share the minimum information needed with payment processors to complete a transaction, and with the other party to a booking so a session can happen. We do not sell your personal information.',
    ],
  },
  {
    id: 'your-rights',
    title: '4. Your rights',
    paragraphs: [
      'You can review and update most of your information from Settings at any time, and request account deletion from the Account tab. Some records may be kept as required by law.',
    ],
  },
  {
    id: 'privacy-contact',
    title: '5. Contact us',
    paragraphs: [
      'Privacy questions can be sent to our support team through the Help Center or Contact Support.',
    ],
  },
]

const guidelinesSections: LegalSection[] = [
  {
    id: 'respect',
    title: '1. Respectful conduct',
    paragraphs: [
      'Treat every Buyer and Pal the way you would want to be treated. Harassment, hate speech, and discrimination are not tolerated, in sessions, in chat, or on Feed posts.',
    ],
  },
  {
    id: 'honest-profiles',
    title: '2. Honest profiles',
    paragraphs: [
      'Represent your rank, skills, and services accurately. Misleading listings or fake reviews can lead to a suspension.',
    ],
  },
  {
    id: 'fair-play',
    title: '3. Fair play & payments',
    paragraphs: [
      'Keep all payments on SquadUp so both sides stay protected. Asking to pay or be paid off-Platform is against the Community Guidelines.',
    ],
  },
  {
    id: 'reporting',
    title: '4. Reporting',
    paragraphs: [
      'Report a user from their profile or a chat thread if something feels wrong. Our team reviews reports and can warn, suspend, or remove an account.',
    ],
  },
  {
    id: 'enforcement',
    title: '5. Enforcement',
    paragraphs: [
      'Violations are reviewed case by case. Depending on severity, outcomes range from a warning to a permanent ban from the Platform.',
    ],
  },
]

const sectionsByTab: Record<LegalTab, LegalSection[]> = {
  terms: termsSections,
  privacy: privacySections,
  guidelines: guidelinesSections,
}

const activeSections = computed(() => sectionsByTab[activeTab.value])
const activeSectionId = ref(sectionsByTab[initialTab][0]!.id)

function selectTab(tab: LegalTab) {
  activeTab.value = tab
  activeSectionId.value = sectionsByTab[tab][0]!.id
}

function selectSection(id: string) {
  activeSectionId.value = id
}
</script>

<template>
  <div class="px-4 py-10 md:px-6 md:py-14">
    <div class="mx-auto max-w-4/5">
      <h1 class="text-4xl font-bold text-white">Terms of Service</h1>
      <p class="mt-2 text-sm text-slate-400">Last updated July 1, 2026</p>

      <nav class="mt-6 flex gap-6 border-b border-white/10">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="cursor-pointer border-b-2 pb-3 text-sm transition-colors"
          :class="
            activeTab === tab.value
              ? 'border-brand-500 font-semibold text-white'
              : 'border-transparent text-slate-400 hover:text-white'
          "
          @click="selectTab(tab.value)"
        >
          {{ tab.label }}
        </button>
      </nav>

      <div class="mt-10 grid grid-cols-1 gap-10 lg:grid-cols-[220px_1fr]">
        <aside class="hidden lg:block">
          <p class="mb-3 text-xs font-semibold tracking-wide text-slate-500">ON THIS PAGE</p>
          <nav class="flex flex-col gap-1">
            <a
              v-for="section in activeSections"
              :key="section.id"
              :href="`#${section.id}`"
              class="rounded-full px-3 py-2 text-sm transition-colors"
              :class="
                activeSectionId === section.id
                  ? 'bg-brand-900/50 text-brand-300'
                  : 'text-slate-400 hover:text-white'
              "
              @click="selectSection(section.id)"
            >
              {{ section.title }}
            </a>
          </nav>
        </aside>

        <div class="flex flex-col gap-8">
          <section v-for="section in activeSections" :id="section.id" :key="section.id" class="scroll-mt-24">
            <h2 class="text-xl font-bold text-white">{{ section.title }}</h2>
            <p
              v-for="(paragraph, index) in section.paragraphs"
              :key="index"
              class="mt-3 text-[15px] leading-relaxed text-slate-300"
            >
              {{ paragraph }}
            </p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>
