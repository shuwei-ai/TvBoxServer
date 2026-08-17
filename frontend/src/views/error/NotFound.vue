<template>
  <div class="not-found-wrapper">
    <div class="not-found-card glass-card">
      <div class="code">404</div>
      <h2>页面未找到</h2>
      <p>抱歉，您访问的页面不存在或已被移除。</p>
      <el-button type="primary" size="large" @click="$router.push('/')">
        返回首页控制台
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.not-found-wrapper {
  min-height: 80vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.not-found-card {
  text-align: center;
  padding: 48px 40px;
  max-width: 440px;
  width: 100%;

  .code {
    font-size: 64px;
    font-weight: 900;
    color: var(--app-accent);
    line-height: 1;
    margin-bottom: 12px;
    letter-spacing: 2px;
  }

  h2 {
    font-size: 20px;
    margin-bottom: 8px;
  }

  p {
    font-size: 14px;
    color: var(--app-text-muted);
    margin-bottom: 24px;
  }
}
</style>
