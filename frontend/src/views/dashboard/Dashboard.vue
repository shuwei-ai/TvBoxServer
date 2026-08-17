<template>
  <div class="dashboard-view">
    <div class="dashboard-grid">
      <!-- 左侧主控区域 (设备管理 + AI 对话控制) -->
      <section class="main-column">
        <DeviceList />
        <ChatController />
      </section>

      <!-- 右侧辅助卡片 (API Key + 我的邀请码) -->
      <aside class="side-column">
        <ApiKeyCard />
        <InviteCodesCard />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useDeviceStore } from '@/stores'
import DeviceList from '@/components/DeviceList.vue'
import ChatController from '@/components/ChatController.vue'
import ApiKeyCard from '@/components/ApiKeyCard.vue'
import InviteCodesCard from '@/components/InviteCodesCard.vue'

const deviceStore = useDeviceStore()

onMounted(() => {
  deviceStore.loadDevices()
})
</script>

<style scoped lang="scss">
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  gap: 20px;
  align-items: start;
}

.main-column,
.side-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
