<script setup lang="ts">
import { ref } from 'vue'
import { PhList } from '@phosphor-icons/vue'
import brandLogo from '@/assets/brand.svg'

const mobileMenuOpen = ref(false)
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-white/10 bg-squadup-bg">
    <div class="mx-auto flex h-16 max-w-(--content-max-width) items-center gap-6 px-4">
      <router-link to="/" class="flex items-center">
        <img :src="brandLogo" alt="SquadUp" class="h-[26px] w-auto" />
      </router-link>

      <div class="ml-auto hidden items-center gap-5 md:flex">
        <router-link to="/login" class="text-sm text-slate-300 hover:text-white">
          Sign in
        </router-link>
        <UButton to="/become-player" color="primary" class="rounded-full px-5">
          Become a Pal
        </UButton>
      </div>

      <UButton
        class="ml-auto md:hidden"
        color="neutral"
        variant="ghost"
        square
        aria-label="Open menu"
        @click="mobileMenuOpen = true"
      >
        <PhList :size="22" />
      </UButton>
    </div>

    <USlideover v-model:open="mobileMenuOpen" side="right" title="Menu">
      <template #body>
        <nav class="flex flex-col gap-4" @click="mobileMenuOpen = false">
          <router-link to="/players" class="text-base text-white">Browse Players</router-link>
          <router-link to="/login" class="text-base text-white">Sign in</router-link>
          <USeparator />
          <router-link to="/become-player" class="text-base text-white">
            Become a Pal
          </router-link>
        </nav>
      </template>
    </USlideover>
  </header>
</template>
