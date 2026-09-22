<script setup lang="ts">
import { PhGameController, PhHandshake, PhShieldCheck, PhUsersThree } from '@phosphor-icons/vue'

const stats = [
  { value: '12k+', label: 'Players matched' },
  { value: '1,400', label: 'Verified Pals' },
  { value: '30+', label: 'Games covered' },
  { value: '4.8/5', label: 'Average session rating' },
]

const values = [
  {
    icon: PhUsersThree,
    title: 'Nobody plays alone',
    body: 'Queueing solo is the fastest way to fall out of love with a game. SquadUp exists so there is always someone good to play with, whatever the hour.',
  },
  {
    icon: PhShieldCheck,
    title: 'Safety before growth',
    body: 'Every Pal is reviewed before going live, reports reach a human, and payments sit with SquadUp until a session is marked complete.',
  },
  {
    icon: PhHandshake,
    title: 'Pals get paid fairly',
    body: 'Pals set their own rates and keep the large majority of every booking. Earnings show up in the dashboard the moment a session closes.',
  },
  {
    icon: PhGameController,
    title: 'Built by players',
    body: 'The team behind SquadUp sits in the same lobbies. Every feature starts as something we wanted while waiting in a queue.',
  },
]

const milestones = [
  {
    year: '2024',
    title: 'The idea',
    body: 'Four friends in Phnom Penh got tired of losing ranked games to silent teammates and started sketching a way to book good ones instead.',
  },
  {
    year: '2025',
    title: 'First Pals',
    body: 'A closed beta opened with 40 hand-picked Pals across Valorant, League of Legends and Mobile Legends.',
  },
  {
    year: '2026',
    title: 'SquadUp today',
    body: 'Squad Coin, the Pal dashboard, the feed and in-app payments now run the whole loop, from finding a Pal to paying one.',
  },
]
</script>

<template>
  <div class="px-4 py-14 md:px-6 md:py-20">
    <div class="mx-auto max-w-4xl">
      <div class="text-center">
        <span
          class="inline-flex items-center rounded-full bg-brand-900/60 px-3 py-1 text-xs font-medium text-brand-300"
        >
          About Us
        </span>
        <h1 class="mt-4 text-4xl font-bold text-white">Never battle alone</h1>
        <p class="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-slate-300">
          SquadUp is a marketplace for gaming company. Book a Pal for ranked duos, coaching or a
          quiet late-night chat, and turn an empty lobby into a good night.
        </p>
      </div>

      <div class="mt-10 grid grid-cols-2 gap-3 md:grid-cols-4">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="rounded-2xl bg-white/5 p-5 text-center"
        >
          <p class="text-2xl font-bold text-white">{{ stat.value }}</p>
          <p class="mt-1 text-xs text-slate-400">{{ stat.label }}</p>
        </div>
      </div>

      <section class="mt-14">
        <h2 class="text-xl font-bold text-white">What we care about</h2>
        <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div
            v-for="value in values"
            :key="value.title"
            class="rounded-2xl bg-white/5 p-5"
          >
            <span
              class="inline-flex h-10 w-10 items-center justify-center rounded-full text-brand-300"
            >
              <component :is="value.icon" :size="32" weight="fill" />
            </span>
            <h3 class="mt-3 font-semibold text-white">{{ value.title }}</h3>
            <p class="mt-1.5 text-sm leading-relaxed text-slate-300">{{ value.body }}</p>
          </div>
        </div>
      </section>

      <section class="mt-14">
        <h2 class="text-xl font-bold text-white">How we got here</h2>
        <div class="mt-4 flex flex-col gap-3">
          <div
            v-for="milestone in milestones"
            :key="milestone.year"
            class="flex flex-col gap-1 rounded-2xl bg-white/5 p-5 sm:flex-row sm:gap-6"
          >
            <span class="text-sm font-semibold text-brand-300 sm:w-16 sm:shrink-0">
              {{ milestone.year }}
            </span>
            <div>
              <h3 class="font-semibold text-white">{{ milestone.title }}</h3>
              <p class="mt-1 text-sm leading-relaxed text-slate-300">{{ milestone.body }}</p>
            </div>
          </div>
        </div>
      </section>

      <section
        class="mt-14 rounded-3xl p-8 text-center"
      >
        <h2 class="text-2xl font-bold text-white">Want to play for a living?</h2>
        <p class="mx-auto mt-2 max-w-md text-sm leading-relaxed text-slate-300">
          Pals set their own games, hours and rates. If you are good company and good at the game,
          there is a seat here.
        </p>
        <div class="mt-5 flex flex-wrap justify-center gap-3">
          <UButton to="/become-a-pal" color="primary" size="lg" class="rounded-full px-6">
            Become a Pal
          </UButton>
          <UButton to="/players" color="neutral" variant="soft" size="lg" class="rounded-full px-6">
            Browse Pals
          </UButton>
        </div>
      </section>
    </div>
  </div>
</template>
