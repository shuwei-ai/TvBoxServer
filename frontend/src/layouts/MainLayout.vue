<template>
  <div class="app-layout">
    <div class="layout-container">
      <HeaderNav />
      <main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import HeaderNav from '@/components/HeaderNav.vue'
</script>

<style scoped lang="scss">
.app-layout {
  min-height: 100vh;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.layout-container {
  max-width: 1240px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.layout-main {
  width: 100%;
  flex: 1;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 768px) {
  .app-layout {
    padding: 12px;
  }
}
</style>
