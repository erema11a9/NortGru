import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },

  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },

  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'warehouse', component: () => import('@/views/Warehouse.vue') },
      { path: 'documents', component: () => import('@/views/Documents.vue') },
      { path: 'transport', component: () => import('@/views/Transport.vue') },
      { path: 'mcp', component: () => import('@/views/MCPChat.vue') },
      { path: 'knowledge', component: () => import('@/views/KnowledgeBase.vue') },
      {
        path: 'analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { roles: ['director', 'manager', 'admin'] }
      },
      {
        path: 'approvals',
        component: () => import('@/views/Approvals.vue'),
        meta: { roles: ['director', 'admin'] }
      },
      { path: 'profile', component: () => import('@/views/Profile.vue') },
    ]
  },

  // 404
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = sessionStorage.getItem('nortgru_token')
  const userRaw = sessionStorage.getItem('nortgru_user')
  const user = userRaw ? JSON.parse(userRaw) : null

  // 1. Проверка авторизации
  if (to.meta.requiresAuth && !token) return next('/login')

  // 2. Если залогинен — не пускаем на страницу логина
  if (to.meta.guest && token) return next('/dashboard')

  if (to.meta.roles && user) {
    const userRole = user.role || 'user' // У нас строка role, а не массив roles

    if (!to.meta.roles.includes(userRole)) {
      console.warn('Доступ запрещен: недостаточно прав')
      return next('/dashboard')
    }
  }

  next()
})

export default router