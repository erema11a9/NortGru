<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">Мой профиль</div>
        <div class="ps">Личные данные и настройки аккаунта</div>
      </div>
    </div>

    <div class="g g21">
      <div style="display:flex;flex-direction:column;gap:14px;">
        <div class="card">
          <div class="ch"><span class="ct">Личные данные</span></div>
          <div class="cb">
            <div class="fgr">
              <label class="fll">Полное имя</label>
              <input v-model="form.full_name" class="fin" type="text" />
            </div>
            <div class="fgr">
              <label class="fll">Email</label>
              <input :value="auth.user?.email" class="fin" type="email" readonly
                style="background:#f8fafc;color:var(--muted);" />
            </div>
            <div class="fgr">
              <label class="fll">Телефон</label>
              <input v-model="form.phone" class="fin" type="tel" placeholder="+7 (000) 000-00-00" />
            </div>
            <div class="fgr">
              <label class="fll">Подразделение</label>
              <input :value="auth.user?.department" class="fin" type="text" readonly
                style="background:#f8fafc;color:var(--muted);" />
            </div>
            <button class="btn btn-primary" :disabled="saving" @click="save">
              <i v-if="saving" class="fas fa-circle-notch fa-spin"></i>
              <i v-else class="fas fa-save"></i>
              Сохранить
            </button>
          </div>
        </div>

        <div class="card">
          <div class="ch"><span class="ct">Смена пароля</span></div>
          <div class="cb">
            <div class="fgr">
              <label class="fll">Текущий пароль</label>
              <input class="fin" type="password" placeholder="••••••••" />
            </div>
            <div class="fgr">
              <label class="fll">Новый пароль</label>
              <input class="fin" type="password" placeholder="••••••••" />
            </div>
            <div class="fgr">
              <label class="fll">Подтвердите пароль</label>
              <input class="fin" type="password" placeholder="••••••••" />
            </div>
            <button class="btn btn-ghost" @click="app.toast('ok', '✅ Пароль изменён', 'Новый пароль успешно сохранён')">
              Изменить пароль
            </button>
          </div>
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:14px;">
        <div class="card">
          <div class="prof-hd">
            <div class="prof-av">{{ userInitials }}</div>
            <div style="font-size:18px;font-weight:700;">{{ auth.user?.name }}</div>
            <div style="font-size:12px;opacity:.7;margin-top:3px;">{{ roleLabel }}</div>
          </div>
          <div class="cb">
            <div class="flex itemsC g2u mb2">
              <i class="fas fa-envelope tm" style="width:15px;font-size:12px;"></i>
              <span class="fs12 tm">{{ auth.user?.email }}</span>
            </div>
            <div class="flex itemsC g2u mb2">
              <i class="fas fa-building tm" style="width:15px;font-size:12px;"></i>
              <span class="fs12 tm">{{ auth.user?.department }}</span>
            </div>
            <div class="flex itemsC g2u">
              <i class="fas fa-shield-alt tm" style="width:15px;font-size:12px;"></i>
              <span :class="['rbg', 'rbg-' + (auth.user?.role || 'user')]">{{ roleLabel }}</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="ch"><span class="ct">Права доступа</span></div>
          <div class="cb">
            <div v-for="p in permissions" :key="p.label" class="perm-item">
              <i :class="['fas', p.allowed ? 'fa-check-circle pi-yes' : 'fa-times-circle pi-no']"></i>
              <span class="fs12">{{ p.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const auth = useAuthStore()
const app = useAppStore()

const saving = ref(false)

// ИСПРАВЛЕНО: Backend отправляет полное имя в поле name
const form = reactive({
  full_name: auth.user?.name || '',
  phone: auth.user?.phone || '',
})

onMounted(() => {
  form.full_name = auth.user?.name || ''
  form.phone = auth.user?.phone || ''
})

// ИСПРАВЛЕНО: Инициалы для аватарки
const userInitials = computed(() => {
  const parts = auth.user?.name?.split(' ') || []
  if (parts.length >= 2) return parts[0][0] + parts[1][0]
  return parts[0] ? parts[0][0] : '?'
})

const roleLabelMap = {
  director: 'Директор',
  manager: 'Финансовый менеджер',
  master: 'Мастер-бригадир',
  warehouse: 'Кладовщик',
  admin: 'Администратор'
}

// ИСПРАВЛЕНО: Работаем с одной ролью из поля role
const roleLabel = computed(() => {
  const primaryRole = auth.user?.role
  return roleLabelMap[primaryRole] || 'Сотрудник'
})

// ИСПРАВЛЕНО: Проверка роли через строку role и добавлены допуски для admin
const permissions = computed(() => {
  const role = auth.user?.role || 'user'

  return [
    { label: 'Просмотр склада и остатков торфа', allowed: true },
    { label: 'Добавление складских операций', allowed: ['director', 'master', 'warehouse', 'admin'].includes(role) },
    { label: 'Создание документов', allowed: true },
    { label: 'Одобрение / отклонение документов', allowed: ['director', 'manager', 'admin'].includes(role) },
    { label: 'Доступ к аналитике и отчётам', allowed: ['director', 'manager', 'admin'].includes(role) },
    { label: 'Экспорт отчётов (PDF, Excel)', allowed: ['director', 'manager', 'admin'].includes(role) },
    { label: 'Управление пользователями', allowed: ['admin', 'director'].includes(role) },
  ]
})

async function save() {
  if (!form.full_name.trim()) {
    app.toast('warn', '⚠️ Ошибка', 'Имя не может быть пустым')
    return
  }

  saving.value = true
  try {
    // Отправляем full_name вместо name
    await auth.updateProfile({ full_name: form.full_name, phone: form.phone })
    app.toast('ok', '✅ Сохранено', 'Профиль успешно обновлён')
  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Ошибка сервера')
  } finally {
    saving.value = false
  }
}
</script>