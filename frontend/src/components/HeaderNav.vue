<template>
  <header class="header-nav glass-card">
    <div class="brand" @click="$router.push('/')">
      <div class="logo-box">TV</div>
      <div class="title-group">
        <h1 class="main-title">TVBox AI 控制中心</h1>
        <div class="sub-title">多租户智能遥控与管理平台</div>
      </div>
    </div>

    <div class="actions">
      <!-- 路由切换 (如果是管理员) -->
      <div v-if="userStore.isAdmin" class="nav-links">
        <el-button
          :type="route.name === 'Dashboard' ? 'primary' : 'default'"
          size="small"
          round
          @click="$router.push('/')"
        >
          <el-icon><Monitor /></el-icon>
          <span>设备与对话</span>
        </el-button>
        <el-button
          :type="route.name === 'AdminConsole' ? 'primary' : 'default'"
          size="small"
          round
          @click="$router.push('/admin')"
        >
          <el-icon><Setting /></el-icon>
          <span>管理员后台</span>
        </el-button>
      </div>

      <!-- 用户信息徽标 -->
      <div class="user-info">
        <el-avatar :size="32" class="user-avatar">
          {{ userStore.username.charAt(0).toUpperCase() || 'U' }}
        </el-avatar>
        <div class="user-meta">
          <span class="username">{{ userStore.username }}</span>
          <el-tag
            :type="userStore.isAdmin ? 'danger' : 'info'"
            size="small"
            effect="dark"
            round
          >
            {{ userStore.role }}
          </el-tag>
        </div>
      </div>

      <!-- 主题切换 -->
      <el-tooltip :content="themeStore.isDark ? '切换浅色模式' : '切换深色模式'" placement="bottom">
        <el-button circle size="default" @click="themeStore.toggleTheme">
          <el-icon><Moon v-if="themeStore.isDark" /><Sunny v-else /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- 刷新数据 -->
      <el-tooltip content="刷新数据" placement="bottom">
        <el-button circle size="default" :loading="refreshing" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- 退出登录 -->
      <el-tooltip content="退出登录" placement="bottom">
        <el-button circle type="danger" plain size="default" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </el-tooltip>
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
    ElMessage.success('数据已刷新')
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
  padding: 12px 24px;
  margin-bottom: 20px;
  border-radius: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  user-select: none;
}

.logo-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--app-accent), var(--app-blue));
  display: grid;
  place-items: center;
  color: #04202b;
  font-weight: 900;
  font-size: 18px;
  box-shadow: 0 4px 14px var(--app-accent-glow);
}

.title-group {
  display: flex;
  flex-direction: column;

  .main-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0;
    line-height: 1.3;
  }

  .sub-title {
    font-size: 12px;
    color: var(--app-text-muted);
  }
}

.actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px 4px 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.1);

  .user-avatar {
    background: linear-gradient(135deg, var(--app-blue), #8b5cf6);
    color: #fff;
    font-weight: 700;
    font-size: 14px;
  }

  .user-meta {
    display: flex;
    align-items: center;
    gap: 6px;

    .username {
      font-size: 13px;
      font-weight: 600;
    }
  }
}

@media (max-width: 768px) {
  .header-nav {
    flex-direction: column;
    gap: 14px;
    padding: 16px;
  }

  .actions {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
