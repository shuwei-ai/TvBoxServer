<template>
  <div class="login-wrapper">
    <div class="theme-toggle-box">
      <el-button circle size="default" @click="themeStore.toggleTheme">
        <el-icon><Moon v-if="themeStore.isDark" /><Sunny v-else /></el-icon>
      </el-button>
    </div>

    <div class="login-card glass-card">
      <div class="brand-section">
        <div class="logo-box">TV</div>
        <div class="brand-text">
          <h2>TVBox AI 控制中心</h2>
          <p>多租户智能遥控与管理平台</p>
        </div>
      </div>

      <div class="tabs-section">
        <el-segmented
          v-model="mode"
          :options="[
            { label: '账号登录', value: 'login' },
            { label: '注册新账号', value: 'register' }
          ]"
          block
          size="large"
        />
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-position="top"
        class="auth-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名（至少 3 位）"
            size="large"
            clearable
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（至少 8 位）"
            size="large"
            show-password
            :prefix-icon="Lock"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            @keydown.enter="handleSubmit"
          />
        </el-form-item>

        <el-form-item
          v-if="mode === 'register'"
          label="邀请码 (可选/必填)"
          prop="invite_code"
        >
          <el-input
            v-model="formData.invite_code"
            placeholder="INV-XXXXXXXX"
            size="large"
            clearable
            :prefix-icon="Ticket"
          />
        </el-form-item>

        <div class="submit-section">
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            class="submit-btn"
            @click="handleSubmit"
          >
            {{ mode === 'login' ? '立即登录' : '立即注册' }}
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, useThemeStore } from '@/stores'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { User, Lock, Ticket, Sunny, Moon } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()

const mode = ref<'login' | 'register'>('login')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  username: '',
  password: '',
  invite_code: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少需要 3 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少需要 8 个字符', trigger: 'blur' }
  ]
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (mode.value === 'login') {
        await userStore.login({
          username: formData.username,
          password: formData.password
        })
        ElMessage.success('登录成功，欢迎回来！')
      } else {
        await userStore.register({
          username: formData.username,
          password: formData.password,
          invite_code: formData.invite_code || undefined
        })
        ElMessage.success('注册成功，已自动登录！')
      }

      const redirectPath = (route.query.redirect as string) || '/'
      router.push(redirectPath)
    } catch {
      // 错误已由 axios 拦截器统一捕获并弹出提示
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-wrapper {
  position: relative;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
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
  border-radius: 20px;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 26px;

  .logo-box {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--app-accent), var(--app-blue));
    display: grid;
    place-items: center;
    color: #04202b;
    font-weight: 900;
    font-size: 20px;
    box-shadow: 0 4px 16px var(--app-accent-glow);
  }

  .brand-text {
    h2 {
      font-size: 19px;
      font-weight: 700;
      margin: 0 0 4px;
    }

    p {
      font-size: 13px;
      color: var(--app-text-muted);
      margin: 0;
    }
  }
}

.tabs-section {
  margin-bottom: 22px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.submit-section {
  margin-top: 14px;

  .submit-btn {
    width: 100%;
    font-weight: 600;
    letter-spacing: 1px;
    border-radius: 10px;
  }
}
</style>
