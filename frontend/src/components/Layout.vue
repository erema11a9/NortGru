<template>
  <div class="app-wrap">
    <!-- MOBILE OVERLAY -->
    <div :class="['mob-ov', app.sidebarCollapsed && 'show']" @click="app.sidebarCollapsed = false"></div>

    <nav :class="['sidebar', app.sidebarCollapsed && 'c']">
      <div class="sb-hd">
        <div class="sb-logo-ico">N</div>
        <div>
          <div class="sb-logo-name">NortGru</div>
          <div class="sb-logo-sub">НОРД-ИСТ ГРУПП</div>
        </div>
      </div>

      <div class="sb-nav">
        <div class="sb-sec">Навигация</div>

        <div v-for="item in navItems" :key="item.id" :class="['sb-item', route.path === '/' + item.id && 'act']"
          @click="navClick(item)">
          <i :class="['sb-item-ico', item.icon]"></i>
          <span class="sb-item-lbl">{{ item.label }}</span>
          <span v-if="item.badge" class="sb-badge">{{ item.badge }}</span>
        </div>
      </div>

      <div class="sb-ft">
        <div class="sb-user" @click="$router.push('/profile')">
          <div
            :class="['sb-av', 'av-' + (auth.user?.role === 'director' ? 'blue' : auth.user?.role === 'manager' ? 'sky' : auth.user?.role === 'master' ? 'green' : 'purple')]">
            {{ auth.initials }}
          </div>
          <div class="sb-tbox" style="flex:1;overflow:hidden;">
            <div class="sb-uname">{{ auth.user?.name }}</div>
            <div class="sb-urole">{{ roleLabel }}</div>
          </div>
          <i class="fas fa-sign-out-alt sb-logout" @click.stop="auth.logout()"
            title="Выйти"></i>
        </div>
      </div>
    </nav>

    <div :class="['main-w', app.sidebarCollapsed && 'c']">

      <header class="topbar">
        <button class="tb-tog" @click="app.sidebarCollapsed = !app.sidebarCollapsed">
          <i class="fas fa-bars"></i>
        </button>

        <div class="tb-bread">
          NortGru / <b>{{ pageTitle }}</b>
        </div>

        <div class="tb-right">
          <div class="rel">
            <button class="tb-btn" @click.stop="nOpen = !nOpen">
              <i class="fas fa-bell"></i>
              <span v-if="unread > 0" class="tb-ndot">{{ unread }}</span>
            </button>
            <div v-if="nOpen" class="npanel" v-click-outside="() => nOpen = false">
              <div class="nph">
                <span class="npht">Уведомления</span>
                <span class="fs11 tb" style="cursor:pointer" @click="readAll">Прочитать все</span>
              </div>
              <div class="nlist">
                <div v-for="n in notifs" :key="n.id" :class="['nrow', !n.is_read && 'unr']" @click="markRead(n)">
                  <i :class="['nrow-ico', n.icon, n.tc]"></i>
                  <div>
                    <div class="nrow-t">{{ n.title }}</div>
                    <div class="nrow-s">{{ n.msg }}</div>
                    <div class="nrow-d">{{ formatTime(n.created_at) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="rel">
            <div class="tb-pill" @click.stop="pOpen = !pOpen">
              <div class="tb-pav">{{ auth.initials }}</div>
              <span class="tb-pname">{{ auth.user?.name?.split(' ')[0] }}</span>
              <i class="fas fa-chevron-down" style="font-size:9px;color:var(--muted);"></i>
            </div>
            
            <div v-if="pOpen" class="npanel" v-click-outside="() => pOpen = false" style="width:180px; padding:6px; right:0; top:calc(100% + 8px);">
              <div class="nrow" style="border:none; border-radius:6px; padding:10px 12px; gap:12px;" @click="$router.push('/profile'); pOpen = false">
                <i class="fas fa-user-circle nrow-ico tm"></i>
                <div class="nrow-t">Мой профиль</div>
              </div>
              <div class="nrow" style="border:none; border-radius:6px; padding:10px 12px; gap:12px;" @click="auth.logout()">
                <i class="fas fa-sign-out-alt nrow-ico tr2"></i>
                <div class="nrow-t tr2">Выйти из аккаунта</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main class="page">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import api from '@/api'

const auth = useAuthStore()
const app = useAppStore()
const route = useRoute()
const router = useRouter()
const nOpen = ref(false)
const pOpen = ref(false)

// Маппинг ролей
const roleLabelMap = {
  director: 'Директор',
  manager: 'Финансовый менеджер',
  master: 'Мастер-бригадир',
  warehouse: 'Кладовщик'
}
const roleLabel = computed(() => roleLabelMap[auth.user?.role] || '')

// Счетчики для бейджей
const pendingCount = ref(0)
const activeTrips = ref(0)

async function loadStats() {
  try {
    const { data } = await api.get('/analytics/dashboard')
    pendingCount.value = data.pending_documents || 0
    activeTrips.value = data.active_trips || 0
  } catch (e) {
    console.warn('Stats load failed')
  }
}

async function fetchNotifs() {
  try {
    const { data } = await api.get('/notifications/')
    notifs.value = data
  } catch (e) {}
}

onMounted(() => {
  loadStats()
  fetchNotifs()
  setInterval(fetchNotifs, 15000)
})

// Навигация
const navItems = computed(() => {
  const items = [
    { id: 'dashboard', label: 'Главная', icon: 'fas fa-home' },
    { id: 'mcp', label: 'AI Помощник', icon: 'fas fa-robot', badge: 'AI' },
    { id: 'warehouse', label: 'Склад (Торф)', icon: 'fas fa-warehouse' },
    { id: 'transport', label: 'Транспорт', icon: 'fas fa-truck-moving', badge: activeTrips.value || null },
    { id: 'documents', label: 'Документы', icon: 'fas fa-file-alt', badge: pendingCount.value || null },
  ]

  if (auth.canAnalytics) {
    items.push({ id: 'analytics', label: 'Аналитика', icon: 'fas fa-chart-line' })
  }

  items.push({ id: 'profile', label: 'Мой профиль', icon: 'fas fa-user-circle' })
  return items
})

function navClick(item) {
  router.push('/' + item.id)
  if (window.innerWidth <= 900) {
    app.sidebarCollapsed = false
  }
}

// Заголовки страниц
const pageTitleMap = {
  dashboard: 'Главная',
  mcp: 'AI Помощник',
  warehouse: 'Склад торфа',
  transport: 'Транспорт и логистика',
  documents: 'Документооборот',
  analytics: 'Аналитика',
  profile: 'Мой профиль',
}
const pageTitle = computed(() => pageTitleMap[route.path.replace('/', '')] || '')

// Уведомления
const notifs = ref([])

function formatTime(d) {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })
}

const unread = computed(() => notifs.value.filter(n => !n.is_read).length)

async function readAll() { 
  try {
    await api.post('/notifications/read-all')
    notifs.value.forEach(n => (n.is_read = true))
  } catch(e) {}
}

async function markRead(n) {
  if (n.is_read) return
  n.is_read = true
  try {
    await api.patch(`/notifications/${n.id}/read`)
  } catch(e) {}
}
</script>