<template>
  <div class="login-bg">
    <div class="blob blob1"></div>
    <div class="blob blob2"></div>

    <div class="login-wrap">
      <div class="login-card">
        <div class="llogo">
          <div class="llogo-ico">N</div>
          <div>
            <div class="llogo-name">NortGru</div>
            <div class="llogo-sub">НОРД-ИСТ ГРУПП</div>
          </div>
        </div>

        <div class="lh1">Добро пожаловать</div>
        <div class="lh2">Введите данные для входа в личный кабинет</div>

        <div v-if="error" class="lerr">
          <i class="fas fa-exclamation-circle"></i> {{ error }}
        </div>

        <div class="fg">
          <label class="flb">Email</label>
          <input v-model="email" class="fi" type="email" placeholder="your@email.ru" @keyup.enter="doLogin"
            :disabled="loading" />
        </div>
        <div class="fg">
          <label class="flb">Пароль</label>
          <div style="position:relative;">
            <input v-model="password" class="fi" :type="showPwd ? 'text' : 'password'" placeholder="••••••••" @keyup.enter="doLogin"
              :disabled="loading" style="padding-right: 36px;" />
            <i :class="['fas', showPwd ? 'fa-eye-slash' : 'fa-eye']" 
               style="position:absolute; right:12px; top:13px; color:#64748b; cursor:pointer;" 
               @click="showPwd = !showPwd"></i>
          </div>
        </div>

        <button class="btn btn-primary btn-block btn-lg" :disabled="loading" @click="doLogin" style="margin-top:4px;">
          <i v-if="loading" class="fas fa-circle-notch fa-spin"></i>
          <i v-else class="fas fa-sign-in-alt"></i>
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>

        <p style="text-align:center;font-size:11px;color:#475569;margin-top:18px;">
          ООО «НОРД-ИСТ ГРУПП» · Биробиджан / Хабаровск
        </p>
      </div>


    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPwd = ref(false)



async function doLogin() {
  if (!email.value || !password.value) {
    error.value = 'Введите email и пароль'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Вызываем метод login из Pinia
    // Он внутри себя сделает API запрос и сохранит данные в localStorage
    await auth.login(email.value, password.value)

    // Если запрос прошел успешно (не выкинул ошибку), редиректим
    router.push('/dashboard')
  } catch (e) {
    // Красиво обрабатываем ошибки от FastAPI
    if (e.response?.status === 401) {
      error.value = 'Неверный email или пароль'
    } else {
      error.value = e.response?.data?.detail || 'Сервер временно недоступен'
    }
  } finally {
    loading.value = false
  }
}
</script>