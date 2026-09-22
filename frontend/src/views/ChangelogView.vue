<script setup lang="ts">
type Release = {
  version: string
  date: string
  tag: 'New' | 'Improved' | 'Fixed'
  title: string
  changes: string[]
}

const releases: Release[] = [
  {
    version: '1.9.0',
    date: 'September 20, 2026',
    tag: 'New',
    title: 'Admin alerts',
    changes: [
      'Reports, disputes, payout requests and Pal applications now raise an alert in the admin bell instead of waiting to be found.',
      'Each queue shows its own unread count in the sidebar.',
    ],
  },
  {
    version: '1.8.0',
    date: 'September 12, 2026',
    tag: 'Improved',
    title: 'Reviews and tips',
    changes: [
      'A review and its tip are now submitted together, so a tip can no longer go through on a review that failed.',
      'Service thumbnails fall back to a game cover when a Pal has not uploaded one.',
    ],
  },
  {
    version: '1.7.0',
    date: 'September 7, 2026',
    tag: 'New',
    title: 'Bakong KHQR at checkout',
    changes: [
      'Top up Squad Coin by scanning a KHQR code with any Cambodian banking app.',
      'Wallet history now labels each top-up with the method it used.',
    ],
  },
  {
    version: '1.6.0',
    date: 'September 6, 2026',
    tag: 'New',
    title: 'Feed upgrades',
    changes: [
      'Post an image straight from the composer.',
      'Finished sessions can post a short status update to your feed automatically.',
      'Explore and Trending now pull real Pals instead of sample data.',
    ],
  },
  {
    version: '1.5.0',
    date: 'August 25, 2026',
    tag: 'New',
    title: 'Squad Coin wallet',
    changes: [
      'Top up, spend and cash out Squad Coin from one wallet screen.',
      'Pals can request a payout once a session is marked complete.',
    ],
  },
]

const tagClasses: Record<Release['tag'], string> = {
  New: 'bg-brand-900/50 text-brand-300 ring-brand-700',
  Improved: 'bg-sky-900/40 text-sky-300 ring-sky-700',
  Fixed: 'bg-amber-900/40 text-amber-300 ring-amber-700',
}
</script>

<template>
  <div class="px-4 py-14 md:px-6 md:py-20">
    <div class="mx-auto max-w-3xl">
      <div class="text-center">
        <span
          class="inline-flex items-center rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300"
        >
          Update Log
        </span>
        <h1 class="mt-4 text-4xl font-bold text-white">What's new on SquadUp</h1>
        <p class="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-300">
          Every release, in plain language. Newest first.
        </p>
      </div>

      <div class="mt-10 flex flex-col gap-3">
        <article
          v-for="release in releases"
          :key="release.version"
          class="rounded-2xl bg-white/5 p-6"
        >
          <div class="flex flex-wrap items-center gap-3">
            <span
              class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset"
              :class="tagClasses[release.tag]"
            >
              {{ release.tag }}
            </span>
            <span class="text-sm font-semibold text-white">v{{ release.version }}</span>
            <span class="text-xs text-slate-400">{{ release.date }}</span>
          </div>

          <h2 class="mt-3 text-lg font-semibold text-white">{{ release.title }}</h2>
          <ul class="mt-2 flex flex-col gap-1.5">
            <li
              v-for="change in release.changes"
              :key="change"
              class="flex gap-2.5 text-sm leading-relaxed text-slate-300"
            >
              <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
              <span>{{ change }}</span>
            </li>
          </ul>
        </article>
      </div>

      <p class="mt-8 text-center text-sm text-slate-400">
        Spotted something broken in a recent update?
        <router-link to="/report" class="text-brand-300 hover:text-white">Report it</router-link>
        and we will take a look.
      </p>
    </div>
  </div>
</template>
