<template>
  <div class="device-monitor-card glass-card">
    <div class="card-header">
      <div class="header-left">
        <h2>全局设备监控</h2>
        <span class="sub-text">实时监控系统内全部用户绑定的电视设备在线状态</span>
      </div>
      <el-button :icon="Refresh" circle size="small" @click="loadDevices" />
    </div>

    <div v-loading="loading" class="devices-container">
      <div v-if="devices.length > 0" class="devices-grid">
        <div
          v-for="d in devices"
          :key="d.id || d.device_id"
          class="device-chip"
          :class="{ online: d.online }"
        >
          <div class="chip-top">
            <span class="online-dot" :class="{ active: d.online }"></span>
            <strong class="dev-name">{{ d.device_name }}</strong>
          </div>
          <div class="chip-bottom">
            <span class="owner">归属: {{ d.owner_username || '未知' }}</span>
            <code class="dev-id">{{ d.device_id }}</code>
          </div>
        </div>
      </div>

      <el-empty v-else description="暂无设备接入" :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAdminDevicesApi } from '@/api/admin'
import type { DeviceItem } from '@/types'
import { Refresh } from '@element-plus/icons-vue'

const devices = ref<DeviceItem[]>([])
const loading = ref(false)

async function loadDevices() {
  loading.value = true
  try {
    const res = await getAdminDevicesApi()
    devices.value = res || []
  } catch {
    // handled
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDevices()
})

defineExpose({
  loadDevices
})
</script>

<style scoped lang="scss">
.device-monitor-card {
  padding: 22px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .header-left {
      h2 {
        font-size: 16px;
        font-weight: 700;
        margin: 0 0 4px;
      }

      .sub-text {
        font-size: 12px;
        color: var(--app-text-muted);
      }
    }
  }

  .devices-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
    max-height: 260px;
    overflow-y: auto;
    padding: 2px;
  }

  .device-chip {
    padding: 12px 14px;
    border-radius: 12px;
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--app-card-border);
    display: flex;
    flex-direction: column;
    gap: 6px;

    &.online {
      border-color: rgba(52, 211, 153, 0.3);
      background: rgba(52, 211, 153, 0.05);
    }

    .chip-top {
      display: flex;
      align-items: center;
      gap: 6px;

      .dev-name {
        font-size: 13px;
      }
    }

    .chip-bottom {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--app-text-muted);

      .dev-id {
        font-family: ui-monospace, monospace;
        font-size: 11px;
      }
    }
  }
}
</style>
