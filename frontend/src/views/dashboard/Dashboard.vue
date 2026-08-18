<template>
  <div class="dashboard-view">
    <div class="bento-grid">
      <!-- 左侧主控模块 (设备管控与 AI 调度) -->
      <section class="main-column">
        <DeviceList />
        <ChatController />
      </section>

      <!-- 右侧凭证与资产模块 (API Key 与 邀请体系) -->
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
.dashboard-view {
  width: 100%;
}

.bento-grid {
  display: grid;
  grid-template-columns: 1.45fr 1fr;
  gap: 20px;
  align-items: start;
}

.main-column,
.side-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (max-width: 960px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
}
</style>
