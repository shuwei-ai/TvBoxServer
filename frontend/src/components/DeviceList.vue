<template>
  <div class="device-list-card glass-card">
    <div class="card-header">
      <div class="header-title">
        <h2>我的设备</h2>
        <span class="count-badge">{{ deviceStore.onlineDevices.length }} 在线 / {{ deviceStore.deviceCount }} 总数</span>
      </div>
      <el-button type="primary" :icon="Plus" round @click="bindDialogRef?.open()">
        绑定设备
      </el-button>
    </div>

    <!-- 加载中骨架屏 -->
    <el-skeleton :loading="deviceStore.loading" animated :rows="3">
      <template #default>
        <!-- 设备列表 -->
        <div v-if="deviceStore.devices.length > 0" class="devices-grid">
          <div
            v-for="device in deviceStore.devices"
            :key="device.id"
            class="device-item"
            :class="{ 'is-selected': deviceStore.selectedDeviceId === device.device_id }"
            @click="handleSelectDevice(device.device_id)"
          >
            <div class="device-main">
              <div class="device-title-row">
                <span class="online-dot" :class="{ active: device.online }"></span>
                <span class="device-name">{{ device.device_name }}</span>
                <el-tag v-if="device.is_default" size="small" type="success" effect="plain" round>
                  默认
                </el-tag>
              </div>

              <div class="device-id-row">
                <code>{{ device.device_id }}</code>
                <span class="status-text">{{ device.online ? '在线' : '离线' }}</span>
              </div>
            </div>

            <div class="device-ops" @click.stop>
              <el-button
                type="danger"
                size="small"
                plain
                circle
                :icon="Delete"
                @click="handleUnbind(device)"
              />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-else
          description="尚未绑定任何 TVBox 设备"
          :image-size="80"
        >
          <el-button type="primary" :icon="Plus" @click="bindDialogRef?.open()">
            立即绑定首台设备
          </el-button>
        </el-empty>
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
    deviceStore.setSelectedDeviceId('') // toggle to auto-route
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
      // 错误由 axios 拦截器提示
    }
  }
}
</script>

<style scoped lang="scss">
.device-list-card {
  padding: 22px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;

  .header-title {
    display: flex;
    align-items: baseline;
    gap: 10px;

    h2 {
      font-size: 17px;
      font-weight: 700;
      margin: 0;
    }

    .count-badge {
      font-size: 12px;
      color: var(--app-text-muted);
    }
  }
}

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(148, 163, 184, 0.05);
  border: 1px solid var(--app-card-border);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--app-accent);
    background: rgba(94, 234, 212, 0.05);
  }

  &.is-selected {
    border-color: var(--app-accent);
    box-shadow: 0 0 0 1px var(--app-accent);
    background: rgba(94, 234, 212, 0.08);
  }

  .device-main {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .device-title-row {
      display: flex;
      align-items: center;
      gap: 6px;

      .device-name {
        font-weight: 600;
        font-size: 14px;
      }
    }

    .device-id-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--app-text-muted);

      code {
        font-family: ui-monospace, monospace;
        font-size: 11px;
      }
    }
  }
}
</style>
