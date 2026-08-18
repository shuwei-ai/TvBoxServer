<template>
  <header class="header-nav bento-card">
    <div class="brand" @click="$router.push('/')">
      <div class="logo-box">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="15" rx="3" />
          <polyline points="17 2 12 7 7 2" />
        </svg>
      </div>
      <div class="title-group">
        <div class="main-title-row">
          <h1 class="main-title">TvBoxServer</h1>
          <span class="version-tag">AI v1.0</span>
        </div>
        <div class="sub-title">智能电视调度与控制中心</div>
      </div>
    </div>

    <!-- 中间实时状态指示器 (Live Telemetry) -->
    <div class="live-telemetry">
      <div class="live-pill" :class="{ live: deviceStore.onlineDevices.length > 0 }">
        <span class="online-dot" :class="{ active: deviceStore.onlineDevices.length > 0 }"></span>
        <span>{{ deviceStore.onlineDevices.length }} 台电视在线</span>
      </div>
    </div>

    <div class="actions">
      <!-- 路由导航 (管理员可见) -->
      <nav v-if="userStore.isAdmin" class="nav-segmented">
        <button
          class="nav-tab"
          :class="{ active: route.name === 'Dashboard' }"
          @click="$router.push('/')"
        >
          <el-icon :size="14"><Monitor /></el-icon>
          <span>控制台</span>
        </button>
        <button
          class="nav-tab"
          :class="{ active: route.name === 'AdminConsole' }"
          @click="$router.push('/admin')"
        >
          <el-icon :size="14"><Setting /></el-icon>
          <span>管理运维</span>
        </button>
      </nav>

      <!-- 用户信息胶囊 -->
      <div class="user-capsule">
        <el-avatar :size="26" class="user-avatar">
          {{ userStore.username.charAt(0).toUpperCase() || 'U' }}
        </el-avatar>
        <span class="username">{{ userStore.username }}</span>
        <span class="role-pill" :class="{ admin: userStore.isAdmin }">
          {{ userStore.isAdmin ? 'Admin' : 'User' }}
        </span>
      </div>

      <!-- 工具栏按钮组 -->
      <div class="tool-buttons">
        <el-tooltip :content="themeStore.isDark ? '切换浅色模式' : '切换深色模式'" placement="bottom">
          <button class="icon-btn" @click="themeStore.toggleTheme">
            <el-icon :size="15"><Moon v-if="themeStore.isDark" /><Sunny v-else /></el-icon>
          </button>
        </el-tooltip>

        <el-tooltip content="刷新设备与数据" placement="bottom">
          <button class="icon-btn" :class="{ spinning: refreshing }" @click="handleRefresh">
            <el-icon :size="15"><Refresh /></el-icon>
          </button>
        </el-tooltip>

        <el-tooltip content="退出登录" placement="bottom">
          <button class="icon-btn danger" @click="handleLogout">
            <el-icon :size="15"><SwitchButton /></el-icon>
          </button>
        </el-tooltip>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, useThemeStore, useDeviceStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Setting,
  Refresh,
  SwitchButton,
  Sunny,
  Moon
} from '@element-plus/icons-vue'

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const deviceStore = useDeviceStore()
const refreshing = ref(false)

async function handleRefresh() {
  refreshing.value = true
  try {
    await deviceStore.loadDevices()
    emit('refresh')
    ElMessage.success('已拉取最新设备状态')
  } catch (err: any) {
    ElMessage.error(err.message || '刷新失败')
  } finally {
    refreshing.value = false
  }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出当前账号吗？', '提示', {
    confirmButtonText: '确定退出',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
    ElMessage.success('已安全退出')
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped lang="scss">
.header-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  margin-bottom: 20px;
  border-radius: var(--app-radius-lg);
  background: var(--app-header-bg);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.logo-box {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--app-accent);
  display: grid;
  place-items: center;
  color: #ffffff;
  box-shadow: 0 2px 8px var(--app-accent-glow);
  transition: transform 0.2s ease;

  &:hover {
    transform: scale(1.04);
  }
}

.title-group {
  display: flex;
  flex-direction: column;

  .main-title-row {
    display: flex;
    align-items: center;
    gap: 8px;

    .main-title {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin: 0;
      color: var(--app-text-primary);
      font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .version-tag {
      font-size: 10px;
      font-family: 'JetBrains Mono', monospace;
      padding: 1px 5px;
      border-radius: 4px;
      background: var(--app-accent-subtle);
      color: var(--app-accent);
      font-weight: 600;
    }
  }

  .sub-title {
    font-size: 11px;
    color: var(--app-text-muted);
  }
}

.live-telemetry {
  display: flex;
  align-items: center;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 分段导航 */
.nav-segmented {
  display: flex;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  padding: 3px;
  border-radius: 8px;
  gap: 2px;

  .nav-tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    font-size: 12.5px;
    font-weight: 500;
    color: var(--app-text-secondary);
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      color: var(--app-text-primary);
    }

    &.active {
      background: var(--app-surface);
      color: var(--app-accent);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
      font-weight: 600;
    }
  }
}

/* 用户信息胶囊 */
.user-capsule {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 10px 3px 4px;
  border-radius: 999px;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);

  .user-avatar {
    background: var(--app-accent);
    color: #fff;
    font-weight: 600;
    font-size: 12px;
  }

  .username {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--app-text-primary);
  }

  .role-pill {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 999px;
    background: var(--app-hairline);
    color: var(--app-text-muted);
    font-weight: 600;
    text-transform: uppercase;

    &.admin {
      background: rgba(239, 68, 68, 0.15);
      color: var(--app-danger);
    }
  }
}

/* 紧凑工具按钮 */
.tool-buttons {
  display: flex;
  align-items: center;
  gap: 6px;

  .icon-btn {
    width: 30px;
    height: 30px;
    display: grid;
    place-items: center;
    border-radius: 7px;
    background: var(--app-surface-subtle);
    border: 1px solid var(--app-hairline);
    color: var(--app-text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      background: var(--app-surface-hover);
      color: var(--app-text-primary);
      border-color: var(--app-hairline-strong);
    }

    &.danger:hover {
      background: var(--app-danger-subtle);
      color: var(--app-danger);
      border-color: rgba(239, 68, 68, 0.3);
    }

    &.spinning .el-icon {
      animation: spin 1s linear infinite;
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 860px) {
  .header-nav {
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    align-items: flex-start;
  }

  .actions {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }
}
</style>
