<template>
  <div class="device-list-card bento-card">
    <div class="card-header">
      <div class="header-title">
        <div class="title-with-icon">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
            <rect x="2" y="7" width="20" height="15" rx="2" />
            <polyline points="17 2 12 7 7 2" />
          </svg>
          <h2>我的设备</h2>
        </div>
        <div class="telemetry-tags">
          <span class="count-tag">
            <span class="online-dot active"></span>
            {{ deviceStore.onlineDevices.length }} 在线
          </span>
          <span class="count-tag total">
            {{ deviceStore.deviceCount }} 台绑定
          </span>
        </div>
      </div>
      <el-button type="primary" size="small" :icon="Plus" @click="bindDialogRef?.open()">
        绑定设备
      </el-button>
    </div>

    <!-- 加载中骨架屏 -->
    <el-skeleton :loading="deviceStore.loading" animated :rows="2">
      <template #default>
        <!-- 设备卡片网格 -->
        <div v-if="deviceStore.devices.length > 0" class="devices-grid">
          <div
            v-for="device in deviceStore.devices"
            :key="device.id || device.device_id"
            class="device-item"
            :class="{
              'is-selected': deviceStore.selectedDeviceId === device.device_id,
              'is-online': device.online
            }"
            @click="handleSelectDevice(device.device_id)"
          >
            <div class="device-main">
              <div class="device-title-row">
                <span class="online-dot" :class="device.online ? 'active' : 'offline'"></span>
                <span class="device-name">{{ device.device_name }}</span>
                <span v-if="device.is_default" class="badge-default">默认</span>
                <span v-if="deviceStore.selectedDeviceId === device.device_id" class="badge-active">🎯 当前目标</span>
              </div>

              <div class="device-meta-row">
                <span class="device-id">
                  <code>{{ device.device_id }}</code>
                </span>
                <span class="status-indicator" :class="{ online: device.online }">
                  {{ device.online ? '在线就绪' : '离线中' }}
                </span>
              </div>
            </div>

            <div class="device-actions" @click.stop>
              <el-tooltip content="解绑此设备" placement="top">
                <button class="unbind-btn" @click="handleUnbind(device)">
                  <el-icon :size="13"><Delete /></el-icon>
                </button>
              </el-tooltip>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <div class="empty-icon-box">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="7" width="20" height="15" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
          </div>
          <p class="empty-text">尚未绑定任何 TVBox 设备</p>
          <p class="empty-sub">绑定后可在电视端输入对应 API Key 进行自动连接与遥控</p>
          <el-button type="primary" size="small" :icon="Plus" @click="bindDialogRef?.open()">
            立即绑定首台设备
          </el-button>
        </div>
      </template>
    </el-skeleton>

    <!-- 绑定设备对话框 -->
    <BindDeviceDialog ref="bindDialogRef" @success="handleBindSuccess" />

    <!-- 首次绑定生成的 API Key 展示框 -->
    <KeyModal ref="keyModalRef" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDeviceStore } from '@/stores'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { DeviceItem, BindDeviceResponse } from '@/types'
import BindDeviceDialog from './BindDeviceDialog.vue'
import KeyModal from './KeyModal.vue'

const deviceStore = useDeviceStore()
const bindDialogRef = ref<InstanceType<typeof BindDeviceDialog>>()
const keyModalRef = ref<InstanceType<typeof KeyModal>>()

function handleSelectDevice(deviceId: string) {
  if (deviceStore.selectedDeviceId === deviceId) {
    deviceStore.setSelectedDeviceId('') // toggle back to auto-route
  } else {
    deviceStore.setSelectedDeviceId(deviceId)
  }
}

function handleBindSuccess(res: BindDeviceResponse) {
  if (res.api_key) {
    keyModalRef.value?.open(res.api_key)
  }
}

async function handleUnbind(device: DeviceItem) {
  try {
    await ElMessageBox.confirm(
      `确定要解绑设备「${device.device_name} (${device.device_id})」吗？解绑后该设备将无法接收控制指令。`,
      '解绑确认',
      {
        confirmButtonText: '确定解绑',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
        type: 'warning'
      }
    )

    await deviceStore.unbindDevice(device.id || device.device_id)
    ElMessage.success('设备已成功解绑')
  } catch (err: any) {
    if (err !== 'cancel') {
      // handled
    }
  }
}
</script>

<style scoped lang="scss">
.device-list-card {
  padding: 18px 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;

  .header-title {
    display: flex;
    align-items: center;
    gap: 12px;

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

    .telemetry-tags {
      display: flex;
      align-items: center;
      gap: 6px;

      .count-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        padding: 2px 7px;
        border-radius: 6px;
        background: var(--app-success-subtle);
        color: var(--app-success);
        font-weight: 600;

        &.total {
          background: var(--app-surface-subtle);
          color: var(--app-text-muted);
          border: 1px solid var(--app-hairline);
        }
      }
    }
  }
}

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 10px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 11px 14px;
  border-radius: var(--app-radius-md);
  background: var(--app-surface);
  border: 1px solid var(--app-hairline);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: var(--app-hairline-strong);
    background: var(--app-surface-hover);
  }

  &.is-selected {
    border-color: var(--app-accent);
    background: var(--app-accent-subtle);
    box-shadow: 0 0 0 1px var(--app-accent);
  }

  .device-main {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;

    .device-title-row {
      display: flex;
      align-items: center;
      gap: 6px;

      .device-name {
        font-weight: 600;
        font-size: 13px;
        color: var(--app-text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .badge-default {
        font-size: 10px;
        padding: 0 5px;
        border-radius: 4px;
        background: var(--app-success-subtle);
        color: var(--app-success);
        font-weight: 600;
      }

      .badge-active {
        font-size: 10px;
        padding: 0 5px;
        border-radius: 4px;
        background: var(--app-accent-subtle);
        color: var(--app-accent);
        font-weight: 600;
      }
    }

    .device-meta-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11.5px;
      color: var(--app-text-muted);

      .device-id code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: var(--app-text-secondary);
      }

      .status-indicator {
        font-size: 11px;
        &.online {
          color: var(--app-success);
          font-weight: 500;
        }
      }
    }
  }

  .device-actions {
    display: flex;
    align-items: center;

    .unbind-btn {
      width: 26px;
      height: 26px;
      display: grid;
      place-items: center;
      border-radius: 6px;
      background: transparent;
      border: 1px solid transparent;
      color: var(--app-text-muted);
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover {
        background: var(--app-danger-subtle);
        color: var(--app-danger);
        border-color: rgba(239, 68, 68, 0.2);
      }
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 30px 16px;

  .empty-icon-box {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);
    display: grid;
    place-items: center;
    color: var(--app-text-muted);
    margin-bottom: 10px;
  }

  .empty-text {
    font-size: 13.5px;
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--app-text-primary);
  }

  .empty-sub {
    font-size: 12px;
    color: var(--app-text-muted);
    margin-bottom: 14px;
  }
}
</style>
