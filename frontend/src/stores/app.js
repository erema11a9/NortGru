import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const toasts = ref([])
  let _id = 0

  function toast(type, title, message, duration = 4000, action = null) {
    const id = ++_id
    toasts.value.push({ id, type, title, message, duration, action })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function removeToast(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const sidebarCollapsed = ref(false)

  return { toasts, toast, removeToast, sidebarCollapsed }
})
