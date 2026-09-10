<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  PhClock,
  PhUsersThree,
  PhGameController,
  PhCake,
  PhMicrophone,
  PhSparkle,
} from '@phosphor-icons/vue'
import coinIcon from '@/assets/squadup-coin.svg'

const router = useRouter()

const perks = [
  {
    icon: 'coin',
    title: 'High income',
    description: 'Earn 1,000+ USD a month while gaming. Cash out your Squad Coins anytime.',
  },
  {
    icon: PhClock,
    title: 'Flexible',
    description: 'Work anytime, anywhere. You choose the games, hours, and rates.',
  },
  {
    icon: PhUsersThree,
    title: 'Make Friends',
    description: 'Meet gamers from all over the world and build your own community.',
  },
]

const requirements = [
  {
    icon: PhCake,
    title: '18+ years old',
    description: 'You must be at least 18 to apply and get paid.',
  },
  {
    icon: PhGameController,
    title: 'A game you love',
    description: 'Be skilled or simply fun in any supported title.',
  },
  {
    icon: PhMicrophone,
    title: 'Mic & stable net',
    description: 'A working mic and a steady connection.',
  },
  {
    icon: PhSparkle,
    title: 'Good vibes',
    description: 'Friendly, respectful and reliable teammates.',
  },
]

function goToApplication() {
  router.push('/become-player')
}
</script>

<template>
  <div class="flex flex-col">
    <section class="relative overflow-hidden px-4 py-16 text-center md:px-6 md:py-20"
      style="background: linear-gradient(120deg, var(--color-brand-700), var(--color-brand-500))">
      <img :src="coinIcon" alt="" class="absolute top-10 right-[12%] h-7 w-7 opacity-70" />
      <img :src="coinIcon" alt="" class="absolute top-24 right-[22%] h-5 w-5 opacity-60" />
      <img :src="coinIcon" alt="" class="absolute top-32 right-[8%] h-6 w-6 opacity-50" />

      <h1 class="text-3xl font-extrabold tracking-tight text-white md:text-4xl">
        BECOME A SQUADUP PAL NOW!
      </h1>
      <p class="mt-3 text-sm font-medium text-white/90 md:text-base">
        High income · Flexible · Make Friends
      </p>
      <UButton color="neutral" variant="solid" size="xl"
        class="mt-6 rounded-full bg-squadup-dark px-6 text-white hover:bg-squadup-dark/80" @click="goToApplication">
        Apply for Free
      </UButton>
    </section>

    <section class="px-4 py-16 md:px-6">
      <div class="mx-auto flex max-w-(--content-max-width) flex-col justify-center gap-8 md:flex-row">
        <div class="flex shrink-0 items-start justify-center">
          <PhGameController :size="44" weight="fill" class="text-white" />
        </div>
        <div>
          <h2 class="text-2xl font-bold text-white">What's a SquadUp Pal?</h2>
          <p class="mt-3 max-w-xl text-[15px] leading-relaxed text-slate-300">
            SquadUp Pals are freelancers who provide gaming or social companionship. Being a Pal
            is an emerging profession, hundreds of thousands of gamers have joined, enhancing the
            experience for millions of players. Play the games you love, meet people, and get paid
            in Squad Coin.
          </p>
        </div>
      </div>
    </section>

    <section class="px-4 py-14 md:px-6">
      <div class="mx-auto max-w-4/5">
        <h2 class="text-center text-2xl font-bold text-white">Why become a Pal</h2>
        <div class="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div v-for="perk in perks" :key="perk.title" class="flex flex-col items-center text-center">
            <div class="flex size-16 items-center justify-center rounded-full">
              <img v-if="perk.icon === 'coin'" :src="coinIcon" alt="" class="h-8 w-8" />
              <component :is="perk.icon" v-else :size="36" weight="fill" class="text-brand-400" />
            </div>
            <h3 class="mt-4 text-[15px] font-semibold text-white">{{ perk.title }}</h3>
            <p class="mt-2 max-w-56 text-sm leading-relaxed text-slate-400">{{ perk.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="px-4 py-14 md:px-6">
      <div class="mx-auto max-w-(--content-max-width)">
        <h2 class="text-center text-2xl font-bold text-white">Who can be a Pal?</h2>
        <div class="mx-auto mt-10 grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2">
          <div v-for="item in requirements" :key="item.title" class="rounded-2xl bg-white/5 p-5">
            <div class="flex gap-3 items-center mb-4">
              <div class="flex">
                <component :is="item.icon" :size="24" weight="fill" class="text-brand-300" />
              </div>
              <h3 class="text-md font-medium text-white">{{ item.title }}</h3>
            </div>
            <p class="mt-1 text-sm text-slate-400">{{ item.description }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
