import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('nortgru_token') || null)
  const user  = ref(JSON.parse(localStorage.getItem('nortgru_user') || 'null'))

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
    localStorage.setItem('nortgru_token', data.access_token)
    localStorage.setItem('nortgru_user',  JSON.stringify(data.user))
    router.push('/dashboard')
  }

  function logout() {
    token.value = null
    user.value  = null
    localStorage.removeItem('nortgru_token')
    localStorage.removeItem('nortgru_user')
    router.push('/login')
  }

  async function updateProfile(data) {
    const res = await api.put('/auth/me', data)
    user.value = res.data
    localStorage.setItem('nortgru_user', JSON.stringify(res.data))
  }

  return { token, user, isAuthenticated, canAnalytics, canApprove, initials, login, logout, updateProfile }
})
