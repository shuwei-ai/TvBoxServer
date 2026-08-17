import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录 / 注册 - TVBox AI 控制中心',
      requiresAuth: false,
      guestOnly: true
    }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: {
          title: '控制台 - TVBox AI 控制中心',
          requiresAuth: true
        }
      },
      {
        path: 'admin',
        name: 'AdminConsole',
        component: () => import('@/views/admin/AdminConsole.vue'),
        meta: {
          title: '管理员控制台 - TVBox AI 控制中心',
          requiresAuth: true,
          requiresAdmin: true
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]
