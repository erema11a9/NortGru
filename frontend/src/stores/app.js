import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const toasts = ref([])
  let _id = 0

  function toast(type, title, message, duration = 4000) {
    const id = ++_id
    toasts.value.push({ id, type, title, message })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  const sidebarCollapsed = ref(false)

  return { toasts, toast, sidebarCollapsed }
})
