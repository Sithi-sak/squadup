<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <div class="app-footer__inner">
      <span>© {{ year }} SquadUp</span>
      <nav class="app-footer__links">
        <router-link to="/players">Browse Players</router-link>
        <router-link to="/become-player">Become a Player</router-link>
      </nav>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  border-top: 1px solid var(--el-border-color);
  background-color: var(--el-bg-color);
}

.app-footer__inner {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.app-footer__links {
  display: flex;
  gap: 16px;
}

.app-footer__links a {
  color: var(--el-text-color-secondary);
  text-decoration: none;
}

.app-footer__links a:hover {
  color: var(--el-color-primary);
}

@media (min-width: 640px) {
  .app-footer__inner {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
