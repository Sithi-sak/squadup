<script setup lang="ts">
import { ref } from 'vue'
import { PhGameController, PhList } from '@phosphor-icons/vue'

const navLinks = [
  { label: 'Browse Players', to: '/players' },
  { label: 'Become a Player', to: '/become-player' },
]

const mobileMenuOpen = ref(false)
</script>

<template>
  <header class="app-header">
    <div class="app-header__inner">
      <router-link to="/" class="app-header__brand">
        <PhGameController :size="24" weight="fill" />
        <span>SquadUp</span>
      </router-link>

      <nav class="app-header__nav">
        <router-link v-for="link in navLinks" :key="link.to" :to="link.to">
          {{ link.label }}
        </router-link>
      </nav>

      <div class="app-header__actions">
        <el-button text @click="$router.push('/login')">Log In</el-button>
        <el-button type="primary" @click="$router.push('/signup')">Sign Up</el-button>
      </div>

      <el-button
        class="app-header__menu-toggle"
        text
        :icon="PhList"
        aria-label="Open menu"
        @click="mobileMenuOpen = true"
      />
    </div>

    <el-drawer v-model="mobileMenuOpen" direction="rtl" size="70%" :with-header="false">
      <nav class="app-header__mobile-nav" @click="mobileMenuOpen = false">
        <router-link v-for="link in navLinks" :key="link.to" :to="link.to">
          {{ link.label }}
        </router-link>
        <el-divider />
        <router-link to="/login">Log In</router-link>
        <router-link to="/signup">Sign Up</router-link>
      </nav>
    </el-drawer>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
}

.app-header__inner {
  max-width: var(--content-max-width);
  margin: 0 auto;
  height: 64px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.app-header__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
  color: var(--el-text-color-primary);
  text-decoration: none;
  white-space: nowrap;
}

.app-header__nav {
  display: none;
  align-items: center;
  gap: 20px;
  flex: 1;
}

.app-header__nav a {
  color: var(--el-text-color-regular);
  text-decoration: none;
  font-size: 14px;
}

.app-header__nav a:hover {
  color: var(--el-color-primary);
}

.app-header__actions {
  display: none;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.app-header__menu-toggle {
  margin-left: auto;
  font-size: 22px;
}

.app-header__mobile-nav {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.app-header__mobile-nav a {
  color: var(--el-text-color-primary);
  text-decoration: none;
  font-size: 16px;
}

@media (min-width: 768px) {
  .app-header__nav {
    display: flex;
  }

  .app-header__actions {
    display: flex;
  }

  .app-header__menu-toggle {
    display: none;
  }
}
</style>
