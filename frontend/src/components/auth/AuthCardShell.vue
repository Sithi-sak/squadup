<script setup lang="ts">
import brandLogo from '@/assets/brand.svg'
</script>

<template>
  <div class="flex min-h-screen w-full flex-col bg-squadup-dark px-6 py-8">
    <router-link to="/" class="flex items-center">
      <img :src="brandLogo" alt="SquadUp" class="h-[26px] w-auto" />
    </router-link>

    <div class="flex flex-1 items-center justify-center py-10">
      <div class="w-full max-w-md rounded-2xl bg-white/[0.03] p-8">
        <slot />
      </div>
    </div>
  </div>
</template>
