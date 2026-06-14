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

        <!-- РЕЖИМ ВХОДА -->
        <template v-if="mode === 'login'">
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

          <p style="text-align:center; font-size:13px; margin-top: 18px; color: #475569;">
            Нет аккаунта? <a href="#" @click.prevent="switchMode('register')" style="color:var(--primary); font-weight:600; text-decoration:none;">Подать заявку</a>
          </p>
        </template>

        <!-- РЕЖИМ РЕГИСТРАЦИИ -->
        <template v-else-if="mode === 'register'">
          <div class="lh1">Регистрация</div>
          <div class="lh2">Подайте заявку на создание личного кабинета</div>

          <div v-if="error" class="lerr">
            <i class="fas fa-exclamation-circle"></i> {{ error }}
          </div>

          <div class="fg">
            <label class="flb">ФИО *</label>
            <input v-model="fullName" class="fi" type="text" placeholder="Иванов Иван Иванович" :disabled="loading" />
          </div>

          <div class="fg">
            <label class="flb">Email *</label>
            <input v-model="email" class="fi" type="email" placeholder="your@email.ru" :disabled="loading" />
          </div>

          <div class="fg">
            <label class="flb">Телефон</label>
            <input v-model="phone" class="fi" type="text" placeholder="+7 (999) 123-45-67" :disabled="loading" />
          </div>

          <div class="fg">
            <label class="flb">Желаемая должность *</label>
            <select v-model="requestedRole" class="fi" :disabled="loading" style="padding: 10px 12px; background: white; border: 1px solid #cbd5e1; border-radius: 8px;">
              <option value="warehouse">Кладовщик (Склад торфа)</option>
              <option value="driver">Водитель</option>
              <option value="manager">Финансовый менеджер</option>
              <option value="master">Мастер-бригадир</option>
            </select>
          </div>

          <div class="fg">
            <label class="flb">Пароль *</label>
            <input v-model="password" class="fi" type="password" placeholder="••••••••" :disabled="loading" />
          </div>

          <div class="fg">
            <label class="flb">Подтверждение пароля *</label>
            <input v-model="confirmPassword" class="fi" type="password" placeholder="••••••••" :disabled="loading" />
          </div>

          <button class="btn btn-primary btn-block btn-lg" :disabled="loading" @click="doRegister" style="margin-top:4px;">
            <i v-if="loading" class="fas fa-circle-notch fa-spin"></i>
            <i v-else class="fas fa-user-plus"></i>
            {{ loading ? 'Отправка...' : 'Отправить заявку' }}
          </button>

          <p style="text-align:center; font-size:13px; margin-top: 18px; color: #475569;">
            Уже есть аккаунт? <a href="#" @click.prevent="switchMode('login')" style="color:var(--primary); font-weight:600; text-decoration:none;">Войти</a>
          </p>
        </template>

        <!-- УСПЕШНАЯ ОТПРАВКА -->
        <template v-else-if="mode === 'success'">
          <div style="text-align:center; padding: 20px 0;">
            <div style="font-size: 48px; color: #22c55e; margin-bottom: 16px;">
              <i class="fas fa-check-circle"></i>
            </div>
            <div class="lh1">Заявка отправлена</div>
            <div class="lh2" style="margin-bottom:24px; line-height: 1.5;">
              Ваш запрос на регистрацию успешно отправлен и ожидает рассмотрения администратором.
            </div>
            <button class="btn btn-primary btn-block btn-lg" @click="switchMode('login')">
              Вернуться ко входу
            </button>
          </div>
        </template>

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
import api from '@/api'

const auth = useAuthStore()
const router = useRouter()

const mode = ref('login') // 'login', 'register', 'success'
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const fullName = ref('')
const phone = ref('')
const requestedRole = ref('warehouse')

const error = ref('')
const loading = ref(false)
const showPwd = ref(false)

function switchMode(newMode) {
  mode.value = newMode
  error.value = ''
  password.value = ''
  confirmPassword.value = ''
}

async function doLogin() {
  if (!email.value || !password.value) {
    error.value = 'Введите email и пароль'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    if (e.response?.status === 403) {
      error.value = e.response?.data?.detail || 'Учетная запись ожидает одобрения'
    } else if (e.response?.status === 401) {
      error.value = 'Неверный email или пароль'
    } else {
      error.value = e.response?.data?.detail || 'Сервер временно недоступен'
    }
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  if (!fullName.value || !email.value || !password.value || !confirmPassword.value) {
    error.value = 'Пожалуйста, заполните все обязательные поля'
    return
  }

  if (password.value !== confirmPassword.value) {
    error.value = 'Пароли не совпадают'
    return
  }

  if (password.value.length < 3) {
    error.value = 'Пароль должен содержать минимум 3 символа'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await api.post('/auth/register', {
      full_name: fullName.value,
      email: email.value,
      phone: phone.value,
      password: password.value,
      requested_role: requestedRole.value
    })
    mode.value = 'success'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка при отправке заявки'
  } finally {
    loading.value = false
  }
}
</script>