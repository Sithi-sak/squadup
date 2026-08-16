<script setup lang="ts">
import { useRouter } from 'vue-router'
import { PhX } from '@phosphor-icons/vue'
import brandLogo from '@/assets/brand.svg'
import mascotImage from '@/assets/3d-mascot-image.png'

const router = useRouter()
</script>

<template>
  <div class="grid min-h-screen w-full md:grid-cols-2">
    <!-- Brand panel -->
    <div
      class="relative hidden flex-col overflow-hidden px-10 py-8 md:flex"
      style="background: linear-gradient(160deg, #10b981 0%, #047857 100%)"
    >
      <router-link to="/" class="relative z-10 flex items-center">
        <img :src="brandLogo" alt="SquadUp" class="h-[26px] w-auto" />
      </router-link>

      <h1
        class="relative z-10 mt-16 max-w-lg text-4xl leading-[1.1] font-extrabold text-white italic lg:text-5xl"
      >
        Never Walk Alone
      </h1>

      <div class="relative z-10 flex flex-1 items-center justify-center">
        <div
          class="pointer-events-none absolute inset-0 m-auto size-2/3 rounded-full bg-brand-300/40 blur-3xl"
        />
        <img
          :src="mascotImage"
          alt=""
          class="pointer-events-none relative w-full max-w-xl animate-float object-contain drop-shadow-2xl"
        />
      </div>
    </div>

    <!-- Form panel -->
    <div class="relative flex flex-col bg-squadup-dark px-6 py-8 md:px-16 md:py-10">
      <div class="flex items-center justify-between gap-3">
        <router-link to="/" class="flex items-center md:hidden">
          <img :src="brandLogo" alt="SquadUp" class="h-[24px] w-auto" />
        </router-link>

        <div class="ml-auto flex items-center gap-3">
          <UButton
            to="mailto:support@squadup.gg"
            color="primary"
            class="rounded-full px-5"
          >
            Contact Us
          </UButton>
          <UButton
            color="neutral"
            variant="soft"
            square
            class="rounded-full bg-white/10 text-white hover:bg-white/15"
            aria-label="Close"
            @click="router.push('/')"
          >
            <PhX :size="18" weight="bold" />
          </UButton>
        </div>
      </div>

      <div class="flex flex-1 items-center justify-center py-10">
        <div class="w-full max-w-sm">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
