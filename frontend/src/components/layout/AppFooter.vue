<script setup lang="ts">
import brandLogo from '@/assets/brand.svg'

const year = new Date().getFullYear()

type FooterLink = { label: string; to?: string | { path: string; query?: Record<string, string> } }

const columns: { heading: string; links: FooterLink[] }[] = [
  {
    heading: 'Support',
    links: [
      { label: 'FAQ', to: '/faq' },
      { label: 'Help Center', to: '/help' },
      { label: 'Report' },
      { label: 'Customer Service' },
    ],
  },
  {
    heading: 'Company',
    links: [{ label: 'About Us' }, { label: 'Update Log' }, { label: 'Business Inquiry' }],
  },
  {
    heading: 'Legal',
    links: [
      { label: 'Terms of Service', to: '/terms' },
      { label: 'Privacy Policy', to: { path: '/terms', query: { tab: 'privacy' } } },
      { label: 'Community Guidelines', to: { path: '/terms', query: { tab: 'guidelines' } } },
    ],
  },
]

const bottomLinks: FooterLink[] = [
  { label: 'Terms', to: '/terms' },
  { label: 'Privacy', to: { path: '/terms', query: { tab: 'privacy' } } },
  { label: 'Guidelines', to: { path: '/terms', query: { tab: 'guidelines' } } },
  { label: 'English (US)' },
]
</script>

<template>
  <footer class="bg-squadup-dark text-slate-400">
    <div
      class="mx-auto grid max-w-(--content-max-width) grid-cols-1 gap-8 px-4 pt-12 pb-8 md:grid-cols-[2fr_1fr_1fr_1fr]"
    >
      <div>
        <router-link to="/" class="inline-flex items-center">
          <img :src="brandLogo" alt="SquadUp" class="h-[26px] w-auto" />
        </router-link>
        <p class="mt-3 max-w-80 text-sm leading-relaxed">
          Team up, make friends, and have fun. A gateway to gamers everywhere — never battle
          alone.
        </p>
      </div>

      <div v-for="col in columns" :key="col.heading" class="flex flex-col gap-3">
        <h4 class="text-sm font-semibold text-white">{{ col.heading }}</h4>
        <template v-for="link in col.links" :key="link.label">
          <router-link v-if="link.to" :to="link.to" class="text-sm hover:text-white">
            {{ link.label }}
          </router-link>
          <span v-else class="text-sm">{{ link.label }}</span>
        </template>
      </div>
    </div>

    <div
      class="mx-auto flex max-w-(--content-max-width) flex-col gap-3 border-t border-white/10 px-4 py-5 text-xs md:flex-row md:items-center md:justify-between"
    >
      <span>© {{ year }} SquadUp. All rights reserved.</span>
      <nav class="flex gap-4">
        <template v-for="link in bottomLinks" :key="link.label">
          <router-link v-if="link.to" :to="link.to" class="hover:text-white">
            {{ link.label }}
          </router-link>
          <span v-else>{{ link.label }}</span>
        </template>
      </nav>
    </div>
  </footer>
</template>
