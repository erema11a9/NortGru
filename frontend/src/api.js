import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  // Добавляем таймаут 
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Добавляем токен к каждому запросу
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nortgru_token')
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
      localStorage.removeItem('nortgru_token')
      localStorage.removeItem('nortgru_user')

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