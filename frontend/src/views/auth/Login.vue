<template>
  <div class="login-wrapper">
    <div class="theme-toggle-box">
      <el-button circle size="default" @click="themeStore.toggleTheme">
        <el-icon><Moon v-if="themeStore.isDark" /><Sunny v-else /></el-icon>
      </el-button>
    </div>

    <div class="login-card glass-card">
      <div class="brand-section">
        <div class="logo-box">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="7" width="20" height="15" rx="3" />
            <polyline points="17 2 12 7 7 2" />
          </svg>
        </div>
        <div class="brand-text">
          <h2>TVBox AI 控制中心</h2>
          <p>多租户智能电视遥控与调度平台</p>
        </div>
      </div>

      <!-- 微信扫码核心交互区 -->
      <div class="qr-login-box">
        <div class="qr-header">
          <div class="wx-icon-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.5 2C4.36 2 1 4.91 1 8.5c0 2.01 1.05 3.82 2.72 5.04l-.69 2.46 2.65-1.32c.86.31 1.8.48 2.82.48.24 0 .48-.01.71-.03-.2-.59-.31-1.22-.31-1.88 0-3.45 3.25-6.25 7.25-6.25.43 0 .85.04 1.25.1C16.5 5.07 12.8 2 8.5 2zm-2.25 4a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5zm4.5 0a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5zM15.75 8c-3.45 0-6.25 2.35-6.25 5.25s2.8 5.25 6.25 5.25c.81 0 1.58-.13 2.28-.38l2.09 1.04-.54-1.95c1.32-.96 2.17-2.39 2.17-3.96C22 10.35 19.2 8 15.75 8zm-2 3.25a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm4 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2z" />
            </svg>
          </div>
          <div class="qr-title-group">
            <span class="qr-main-title">微信扫码登录</span>
            <span class="qr-sub-title">打开微信扫一扫 · 快捷授权登录</span>
          </div>
        </div>

        <!-- 二维码显示与状态遮罩容器 -->
        <div class="qr-stage">
          <!-- 1. 加载中状态 -->
          <div v-if="loading" class="qr-status-layer loading-layer">
            <el-icon class="is-loading" :size="38"><Loading /></el-icon>
            <p>正在生成登录二维码...</p>
          </div>

          <!-- 2. 二维码展示及各交互状态 -->
          <div v-else class="qr-canvas-box" :class="{ 'blur-effect': isExpired || isScanned || isAuthorized }">
            <img
              v-if="sessionData?.qrcode"
              :src="sessionData.qrcode"
              alt="微信登录小程序码"
              class="qr-image"
            />
            <div v-else class="qr-placeholder">
              <el-icon :size="48"><PictureRounded /></el-icon>
              <span>暂无二维码</span>
            </div>
          </div>

          <!-- 状态 2: 手机已扫码，等待确认 -->
          <div v-if="isScanned" class="qr-status-layer scanned-layer">
            <div class="scanned-anim-icon">
              <el-icon :size="42"><Iphone /></el-icon>
              <div class="pulse-ring"></div>
            </div>
            <p class="status-tip-bold">已扫码，请在微信中确认</p>
            <p class="status-sub-tip">请在手机端点击【确认登录】</p>
          </div>

          <!-- 状态 3: 授权成功，正在进入 -->
          <div v-if="isAuthorized" class="qr-status-layer success-layer">
            <el-icon :size="46" class="success-icon"><CircleCheckFilled /></el-icon>
            <p class="status-tip-bold">授权成功</p>
            <p class="status-sub-tip">正在同步登录信息，请稍候...</p>
          </div>

          <!-- 状态 4 / 7 / 异常: 已过期或失败 -->
          <div v-if="isExpired" class="qr-status-layer expired-layer" @click="fetchNewSession">
            <el-icon :size="40"><RefreshRight /></el-icon>
            <p class="status-tip-bold">{{ expiredReason }}</p>
            <el-button type="primary" size="small" round class="refresh-btn">
              点击刷新二维码
            </el-button>
          </div>
        </div>

        <!-- 底部状态指示栏 -->
        <div class="qr-footer-status">
          <div class="status-pill" :class="statusPillClass">
            <span class="status-dot"></span>
            <span>{{ statusText }}</span>
          </div>

          <button
            v-if="!loading && !isAuthorized"
            class="manual-refresh-btn"
            title="重新获取二维码"
            @click="fetchNewSession"
          >
            <el-icon><Refresh /></el-icon>
            <span>刷新</span>
          </button>
        </div>

        <!-- 可选邀请码输入（折叠式设计） -->
        <div class="invite-toggle-section">
          <div class="invite-toggle-header" @click="showInvite = !showInvite">
            <el-icon :size="13"><Ticket /></el-icon>
            <span>{{ showInvite ? '收起邀请码设置' : '首次使用有邀请码？（点击展开）' }}</span>
            <el-icon :size="12" class="arrow-icon" :class="{ open: showInvite }"><ArrowDown /></el-icon>
          </div>

          <transition name="el-zoom-in-top">
            <div v-if="showInvite" class="invite-input-body">
              <el-input
                v-model="inviteCode"
                placeholder="请输入邀请码（如 INV-XXXXXXXX）"
                size="default"
                clearable
                :prefix-icon="Ticket"
              />
              <span class="invite-hint">如平台已开启严格邀请注册，首次微信登录需验证有效邀请码。</span>
            </div>
          </transition>
        </div>
      </div>

      <!-- 底部辅助指引 -->
      <div class="helper-steps">
        <div class="step-item">
          <span class="step-num">1</span>
          <span>使用微信扫描上方小程序码</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item">
          <span class="step-num">2</span>
          <span>手机点击授权并自动进入</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, useThemeStore } from '@/stores'
import { createWxSessionApi, checkWxStatusApi } from '@/api/auth'
import type { WxSessionData } from '@/types'
import { ElMessage } from 'element-plus'
import {
  Sunny,
  Moon,
  Loading,
  PictureRounded,
  Iphone,
  CircleCheckFilled,
  RefreshRight,
  Refresh,
  Ticket,
  ArrowDown
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()

// 状态管理
const loading = ref(true)
const sessionData = ref<WxSessionData | null>(null)
const scanStatus = ref<number>(1) // 1: waiting, 2: scanned, 3: authorized, 4: canceled, 6: consumed, 7: expired
const expiredReason = ref('二维码已失效')
const showInvite = ref(false)
const inviteCode = ref('')

let pollTimer: ReturnType<typeof setInterval> | null = null
const isCompleting = ref(false)

const isScanned = computed(() => scanStatus.value === 2)
const isAuthorized = computed(() => scanStatus.value === 3 || scanStatus.value === 6 || isCompleting.value)
const isExpired = computed(() => scanStatus.value === 4 || scanStatus.value === 7)

const statusText = computed(() => {
  if (loading.value) return '正在连接授权服务...'
  if (isAuthorized.value) return '授权已通过，正在登录...'
  if (isScanned.value) return '已成功扫码，请在手机微信确认'
  if (isExpired.value) return expiredReason.value
  return '等待微信扫码...'
})

const statusPillClass = computed(() => {
  if (isAuthorized.value) return 'success'
  if (isScanned.value) return 'warning'
  if (isExpired.value) return 'danger'
  return 'waiting'
})

// 创建新的微信扫码会话
async function fetchNewSession() {
  stopPolling()
  loading.value = true
  scanStatus.value = 1
  isCompleting.value = false

  try {
    const res = await createWxSessionApi({
      biz_state: 'tvbox-web-login',
      expire_seconds: 300
    })
    sessionData.value = res
    scanStatus.value = 1
    startPolling(res.session_no)
  } catch (err: any) {
    const msg = err.message || '获取微信扫码会话失败，请检查 DreamAuth 配置'
    ElMessage.error(msg)
    scanStatus.value = 7
    expiredReason.value = msg.includes('AK/SK') ? 'DreamAuth 未配置' : '网络连接失败，请重试'
  } finally {
    loading.value = false
  }
}

// 轮询检查扫码状态
function startPolling(sessionNo: string) {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (!sessionNo || isCompleting.value) return

    try {
      const res = await checkWxStatusApi(sessionNo)
      const currentStatus = res.status

      if (currentStatus !== scanStatus.value) {
        scanStatus.value = currentStatus
      }

      // 状态 2: 用户已扫码
      if (currentStatus === 2) {
        // 继续等待授权
      }

      // 状态 3: 授权成功，触发登录完成
      if (currentStatus === 3) {
        stopPolling()
        await handleAuthComplete(sessionNo)
      }

      // 状态 4: 用户取消授权
      if (currentStatus === 4) {
        stopPolling()
        expiredReason.value = '您已在手机端取消授权'
      }

      // 状态 7: 会话过期
      if (currentStatus === 7) {
        stopPolling()
        expiredReason.value = '二维码已过期，请刷新'
      }
    } catch {
      // 轮询偶发异常不中断，等待下一次周期
    }
  }, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 完成登录
async function handleAuthComplete(sessionNo: string) {
  if (isCompleting.value) return
  isCompleting.value = true

  try {
    await userStore.loginWithWechat({
      session_no: sessionNo,
      invite_code: inviteCode.value.trim() || undefined
    })
    ElMessage.success('微信登录成功，欢迎使用！')
    const redirectPath = (route.query.redirect as string) || '/'
    router.push(redirectPath)
  } catch (err: any) {
    ElMessage.error(err.message || '登录验证失败，请重新扫码')
    scanStatus.value = 7
    expiredReason.value = err.message || '登录验证失败'
    isCompleting.value = false
  }
}

onMounted(() => {
  fetchNewSession()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.login-wrapper {
  position: relative;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px 16px;
  background: radial-gradient(circle at 50% 10%, var(--app-surface-hover) 0%, transparent 60%);
}

.theme-toggle-box {
  position: absolute;
  top: 24px;
  right: 24px;
}

.login-card {
  width: 100%;
  max-width: 440px;
  padding: 36px 32px;
  border-radius: 24px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(16px);
  border: 1px solid var(--app-hairline-strong);
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;

  .logo-box {
    width: 46px;
    height: 46px;
    border-radius: 13px;
    background: linear-gradient(135deg, var(--app-accent), var(--app-blue));
    display: grid;
    place-items: center;
    color: #ffffff;
    font-weight: 800;
    box-shadow: 0 4px 16px var(--app-accent-glow);
  }

  .brand-text {
    h2 {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin: 0 0 3px;
      color: var(--app-text-primary);
    }

    p {
      font-size: 12.5px;
      color: var(--app-text-muted);
      margin: 0;
    }
  }
}

.qr-login-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-hairline);
  border-radius: 18px;
  padding: 24px 20px;
  margin-bottom: 20px;
}

.qr-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  width: 100%;
  justify-content: center;

  .wx-icon-badge {
    color: #07c160;
    display: flex;
    align-items: center;
  }

  .qr-title-group {
    display: flex;
    flex-direction: column;

    .qr-main-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--app-text-primary);
    }

    .qr-sub-title {
      font-size: 11.5px;
      color: var(--app-text-muted);
    }
  }
}

.qr-stage {
  position: relative;
  width: 204px;
  height: 204px;
  border-radius: 16px;
  background: #ffffff;
  padding: 8px;
  display: grid;
  place-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--app-hairline-strong);
  overflow: hidden;

  .qr-canvas-box {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: filter 0.3s ease;

    &.blur-effect {
      filter: blur(5px) grayscale(40%);
      opacity: 0.35;
    }

    .qr-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 10px;
    }

    .qr-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      color: #999;
      font-size: 12px;
    }
  }
}

.qr-status-layer {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 16px;
  gap: 8px;
  z-index: 5;

  &.loading-layer {
    background: rgba(255, 255, 255, 0.95);
    color: var(--app-accent);

    p {
      font-size: 12px;
      color: #666;
      margin: 0;
    }
  }

  &.scanned-layer {
    background: rgba(255, 255, 255, 0.92);
    color: var(--app-accent);

    .scanned-anim-icon {
      position: relative;
      display: grid;
      place-items: center;
      color: #07c160;
    }

    .status-tip-bold {
      font-size: 13.5px;
      font-weight: 700;
      color: #111;
      margin: 4px 0 0;
    }

    .status-sub-tip {
      font-size: 11.5px;
      color: #666;
      margin: 0;
    }
  }

  &.success-layer {
    background: rgba(255, 255, 255, 0.95);
    color: #07c160;

    .success-icon {
      animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .status-tip-bold {
      font-size: 14px;
      font-weight: 700;
      color: #07c160;
      margin: 4px 0 0;
    }

    .status-sub-tip {
      font-size: 11px;
      color: #666;
      margin: 0;
    }
  }

  &.expired-layer {
    background: rgba(255, 255, 255, 0.94);
    cursor: pointer;
    color: var(--app-danger);

    .status-tip-bold {
      font-size: 12.5px;
      font-weight: 600;
      color: #333;
      margin: 2px 0 4px;
    }

    .refresh-btn {
      font-size: 11.5px;
      padding: 6px 14px;
    }
  }
}

.qr-footer-status {
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 4px;

  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
    background: var(--app-surface);
    border: 1px solid var(--app-hairline);
    color: var(--app-text-secondary);

    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #999;
    }

    &.waiting {
      .status-dot {
        background: var(--app-accent);
        animation: pulse 1.5s infinite;
      }
    }

    &.warning {
      color: #d97706;
      .status-dot {
        background: #f59e0b;
        animation: pulse 1s infinite;
      }
    }

    &.success {
      color: #059669;
      .status-dot {
        background: #10b981;
      }
    }

    &.danger {
      color: var(--app-danger);
      .status-dot {
        background: var(--app-danger);
      }
    }
  }

  .manual-refresh-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: transparent;
    border: none;
    color: var(--app-text-muted);
    font-size: 12px;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 6px;
    transition: all 0.15s ease;

    &:hover {
      color: var(--app-accent);
      background: var(--app-surface-hover);
    }
  }
}

.invite-toggle-section {
  width: 100%;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--app-hairline);

  .invite-toggle-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    color: var(--app-text-muted);
    cursor: pointer;
    user-select: none;
    transition: color 0.15s ease;

    &:hover {
      color: var(--app-accent);
    }

    .arrow-icon {
      margin-left: auto;
      transition: transform 0.2s ease;

      &.open {
        transform: rotate(180deg);
      }
    }
  }

  .invite-input-body {
    margin-top: 10px;

    .invite-hint {
      display: block;
      font-size: 11px;
      color: var(--app-text-muted);
      margin-top: 4px;
      line-height: 1.4;
    }
  }
}

.helper-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  background: var(--app-surface-subtle);
  border-radius: 12px;
  border: 1px solid var(--app-hairline);

  .step-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--app-text-muted);

    .step-num {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: var(--app-hairline-strong);
      color: var(--app-text-secondary);
      font-size: 10px;
      font-weight: 700;
      display: grid;
      place-items: center;
    }
  }

  .step-divider {
    width: 1px;
    height: 16px;
    background: var(--app-hairline);
  }
}

@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

@keyframes popIn {
  0% { transform: scale(0.5); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
</style>
