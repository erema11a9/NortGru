import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(sessionStorage.getItem('nortgru_token') || null)
  const user  = ref(JSON.parse(sessionStorage.getItem('nortgru_user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const canAnalytics    = computed(() => ['director','manager','admin'].includes(user.value?.role))
  const canApprove      = computed(() => ['director','manager','admin'].includes(user.value?.role))

  const initials = computed(() => {
    if (!user.value?.name) return '?'
    return user.value.name.split(' ').slice(0,2).map(p => p[0]).join('')
  })

  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    token.value = data.access_token
    user.value  = data.user
    sessionStorage.setItem('nortgru_token', data.access_token)
    sessionStorage.setItem('nortgru_user',  JSON.stringify(data.user))
    router.push('/dashboard')
  }

  function logout() {
    token.value = null
    user.value  = null
    sessionStorage.removeItem('nortgru_token')
    sessionStorage.removeItem('nortgru_user')
    router.push('/login')
  }

  async function updateProfile(data) {
    const res = await api.put('/auth/me', data)
    user.value = res.data
    sessionStorage.setItem('nortgru_user', JSON.stringify(res.data))
  }

  return { token, user, isAuthenticated, canAnalytics, canApprove, initials, login, logout, updateProfile }
})
