<script setup lang="ts">
import { PhArrowRight } from '@phosphor-icons/vue'
import gamesTileImage from '@/assets/game.jpg'
import chillingTileImage from '@/assets/chilling.jpg'
import hobbiesImage from '@/assets/hobbies.jpg'
import echatImage from '@/assets/echat.jpg'
import watchTogetherImage from '@/assets/watch_together.jpg'
import valorantCover from '@/assets/game_cover/valorant.png'

const categoryTiles = [
  { label: 'Games', to: '/players', image: gamesTileImage },
  { label: 'Chilling', to: '/players', image: chillingTileImage },
]

const serviceCards = [
  { label: 'Hobbies Talk', to: '/players', image: hobbiesImage },
  { label: 'E-Chat', to: '/players', image: echatImage },
  { label: 'Watch Together', to: '/players', image: watchTogetherImage },
  { label: 'Valorant', to: { path: '/players', query: { game: 'Valorant' } }, image: valorantCover },
]
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] px-4 pt-14 pb-8 md:px-6 md:pt-16">
    <div class="mx-auto max-w-5xl">
      <div class="mx-auto max-w-8xl">
        <h1 class="mb-6 text-3xl font-bold text-white">All Services</h1>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <router-link
            v-for="tile in categoryTiles"
            :key="tile.label"
            :to="tile.to"
            class="relative flex h-28 items-center justify-between overflow-hidden rounded-xl bg-cover bg-center px-6 py-4 md:h-36"
            :style="{ backgroundImage: `url(${tile.image})` }"
          >
            <div class="absolute inset-0 bg-squadup-dark/60 transition-colors hover:bg-squadup-dark/20" />
            <span class="relative text-lg font-semibold text-white">{{ tile.label }}</span>
            <PhArrowRight :size="20" class="relative text-white" weight="bold" />
          </router-link>
        </div>

        <div class="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <router-link
            v-for="card in serviceCards"
            :key="card.label"
            :to="card.to"
            class="relative flex aspect-10/16 flex-col justify-end overflow-hidden rounded-xl bg-gray-800/70"
          >
            <template v-if="card.image">
              <img :src="card.image" :alt="card.label" class="absolute inset-0 h-full w-full object-cover" />
              <div
                class="absolute inset-0 bg-linear-to-t from-squadup-dark via-squadup-dark/15 to-transparent"
              />
            </template>
            <span class="relative px-4 pb-4 font-semibold text-white">{{ card.label }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
