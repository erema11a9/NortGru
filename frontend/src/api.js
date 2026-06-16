import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  // Добавляем таймаут 
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Добавляем токен к каждому запросу
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('nortgru_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// Обработка ответов
api.interceptors.response.use(
  (res) => res,
  (err) => {
    // 2. Улучшенная логика разлогина
    if (err.response?.status === 401) {
      // Очищаем хранилище
      sessionStorage.removeItem('nortgru_token')
      sessionStorage.removeItem('nortgru_user')

      // Чтобы не зациклить редирект, если мы и так на странице логина
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    // Вывод ошибки 403 
    if (err.response?.status === 403) {
      console.error('Доступ запрещен: недостаточно прав')
    }

    return Promise.reject(err)
  }
)

export default api