<template>
  <div class="device-monitor-card bento-card">
    <div class="card-header">
      <div class="header-left">
        <div class="title-with-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
            <rect x="2" y="7" width="20" height="15" rx="2" />
            <polyline points="17 2 12 7 7 2" />
          </svg>
          <h2>全局设备监控</h2>
        </div>
        <span class="sub-text">实时监控系统内全量 TVBox 在线与长连接拓扑</span>
      </div>
      <button class="refresh-icon-btn" :class="{ spinning: loading }" @click="loadDevices">
        <el-icon :size="13"><Refresh /></el-icon>
      </button>
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
            <span class="online-dot" :class="d.online ? 'active' : 'offline'"></span>
            <strong class="dev-name">{{ d.device_name }}</strong>
            <span class="online-tag" :class="d.online ? 'online' : 'offline'">
              {{ d.online ? 'ONLINE' : 'OFFLINE' }}
            </span>
          </div>
          <div class="chip-bottom">
            <span class="owner">归属: <strong>{{ d.owner_username || '未知' }}</strong></span>
            <el-tooltip :content="d.device_id" placement="top" :show-after="300">
              <code class="dev-id">{{ d.device_id }}</code>
            </el-tooltip>
          </div>
        </div>
      </div>

      <div v-else class="empty-box">
        <p>暂无 TVBox 设备接入系统</p>
      </div>
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
  padding: 18px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .header-left {
    .title-with-icon {
      display: flex;
      align-items: center;
      gap: 7px;

      .header-icon {
        color: var(--app-accent);
      }

      h2 {
        font-size: 14.5px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.01em;
      }
    }

    .sub-text {
      font-size: 11.5px;
      color: var(--app-text-muted);
    }
  }
}

.refresh-icon-btn {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  color: var(--app-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--app-surface-hover);
    color: var(--app-text-primary);
  }

  &.spinning .el-icon {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  max-height: 250px;
  overflow-y: auto;
  padding: 2px;
}

.device-chip {
  padding: 10px 12px;
  border-radius: var(--app-radius-md);
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  overflow: hidden;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--app-hairline-strong);
  }

  &.online {
    border-color: rgba(16, 185, 129, 0.25);
    background: var(--app-success-subtle);
  }

  .chip-top {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;

    .dev-name {
      font-size: 12.5px;
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .online-tag {
      font-size: 9px;
      font-family: 'JetBrains Mono', monospace;
      padding: 0 4px;
      border-radius: 3px;
      font-weight: 700;
      flex-shrink: 0;

      &.online {
        color: var(--app-success);
      }

      &.offline {
        color: var(--app-text-muted);
      }
    }
  }

  .chip-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    color: var(--app-text-muted);
    min-width: 0;

    .owner {
      flex-shrink: 0;
      white-space: nowrap;

      strong {
        color: var(--app-text-secondary);
      }
    }

    .dev-id {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10.5px;
      color: var(--app-accent);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 120px;
      text-align: right;
    }
  }
}

.empty-box {
  padding: 24px;
  text-align: center;
  color: var(--app-text-muted);
  font-size: 12px;
}
</style>
