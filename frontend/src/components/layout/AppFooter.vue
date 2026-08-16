<script setup lang="ts">
import brandLogo from '@/assets/brand.svg'

const year = new Date().getFullYear()

const columns = [
  {
    heading: 'Support',
    links: ['FAQ', 'Help Center', 'Report', 'Customer Service'],
  },
  {
    heading: 'Company',
    links: ['About Us', 'Update Log', 'Business Inquiry'],
  },
  {
    heading: 'Legal',
    links: ['Terms of Service', 'Privacy Policy', 'Community Guidelines'],
  },
]

const bottomLinks = ['Terms', 'Privacy', 'Guidelines', 'English (US)']
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
        <span v-for="link in col.links" :key="link" class="text-sm">{{ link }}</span>
      </div>
    </div>

    <div
      class="mx-auto flex max-w-(--content-max-width) flex-col gap-3 border-t border-white/10 px-4 py-5 text-xs md:flex-row md:items-center md:justify-between"
    >
      <span>© {{ year }} SquadUp. All rights reserved.</span>
      <nav class="flex gap-4">
        <span v-for="link in bottomLinks" :key="link">{{ link }}</span>
      </nav>
    </div>
  </footer>
</template>
