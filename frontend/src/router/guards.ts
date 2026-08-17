import type { Router } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

export function setupRouterGuards(router: Router) {
  router.beforeEach(async (to, _from, next) => {
    const userStore = useUserStore()

    // 动态更新页面标题
    if (to.meta.title) {
      document.title = to.meta.title as string
    }

    const token = userStore.token

    // 如果已登录但尚未获取/恢复 userInfo
    if (token && !userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch {
        // token 无效
        userStore.logout()
        return next({ name: 'Login', query: { redirect: to.fullPath } })
      }
    }

    // 游客路由拦截（如已登录访问 /login -> 跳转 /）
    if (to.meta.guestOnly && token) {
      return next({ name: 'Dashboard' })
    }

    // 鉴权拦截
    if (to.meta.requiresAuth && !token) {
      ElMessage.warning('请先登录后访问')
      return next({ name: 'Login', query: { redirect: to.fullPath } })
    }

    // 管理员权限拦截
    if (to.meta.requiresAdmin && !userStore.isAdmin) {
      ElMessage.error('权限不足，仅管理员可访问控制台')
      return next({ name: 'Dashboard' })
    }

    next()
  })
}
