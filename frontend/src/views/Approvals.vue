<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">Заявки на регистрацию</div>
        <div class="ps">Модерация запросов на доступ к личному кабинету NortGru</div>
      </div>
      <div class="ph-r">
        <button class="btn btn-ghost" @click="fetchPending" :disabled="loading">
          <i :class="['fas fa-sync-alt', loading && 'fa-spin']"></i> Обновить
        </button>
      </div>
    </div>

    <!-- STATS CARD -->
    <div class="g g4 mb4">
      <div class="kpi">
        <div class="kico ico-y"><i class="fas fa-user-clock"></i></div>
        <div>
          <div class="klb">Ожидают проверки</div>
          <div class="kv">{{ pendingUsers.length }}</div>
          <div class="ks">Новых заявок</div>
        </div>
      </div>
    </div>

    <!-- PENDING USERS TABLE -->
    <div class="card">
      <div class="ch">
        <span class="ct">Список входящих заявок</span>
        <span class="fs12 tm">Пользователи, заполнившие регистрационную форму</span>
      </div>
      <div class="tw">
        <table>
          <thead>
            <tr>
              <th>Дата подачи</th>
              <th>ФИО</th>
              <th>Email</th>
              <th>Телефон</th>
              <th>Желаемая роль</th>
              <th style="text-align: right;">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in pendingUsers" :key="user.id">
              <td class="fs12 tm">{{ formatDate(user.created_at) }}</td>
              <td class="fw6">{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.phone || '—' }}</td>
              <td>
                <span class="badge b-warn">
                  {{ getRoleName(user.role) }}
                </span>
              </td>
              <td style="text-align: right;">
                <div style="display: inline-flex; gap: 8px;">
                  <button class="btn btn-success btn-sm" @click="openApproveModal(user)">
                    <i class="fas fa-check"></i> Одобрить
                  </button>
                  <button class="btn btn-danger btn-sm" @click="rejectUser(user)">
                    <i class="fas fa-times"></i> Отклонить
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!pendingUsers.length && !loading">
              <td colspan="6" style="text-align:center; padding: 30px; color: var(--muted)">
                <i class="fas fa-user-check fa-2x mb2" style="color:#cbd5e1; display:block;"></i>
                Нет ожидающих заявок. Все запросы обработаны!
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- APPROVE MODAL -->
    <div v-if="showModal" class="ov" @click.self="showModal = false">
      <div class="modal">
        <div class="mh">
          <div class="mh-ico ico-g">
            <i class="fas fa-user-check"></i>
          </div>
          <span class="mt2">Одобрение пользователя</span>
          <button class="mc" @click="showModal = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody">
          <p style="margin-bottom:16px; font-size:14px; color:#475569;">
            Вы одобряете доступ для <b>{{ selectedUser?.name }}</b> ({{ selectedUser?.email }}).
          </p>
          <div class="fgr">
            <label class="fll">Роль в системе *</label>
            <select v-model="assignRole" class="fin" @change="updateDefaultJobTitle">
              <option value="warehouse">Кладовщик</option>
              <option value="driver">Водитель</option>
              <option value="manager">Финансовый менеджер</option>
              <option value="master">Мастер-бригадир</option>
              <option value="director">Директор</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          <div class="fgr">
            <label class="fll">Должность в компании *</label>
            <input v-model="assignJobTitle" class="fin" type="text" placeholder="Например: Старший кладовщик" />
          </div>
        </div>
        <div class="mfoot">
          <button class="btn btn-ghost" @click="showModal = false">Отмена</button>
          <button class="btn btn-success" :disabled="submitting" @click="submitApprove">
            <i v-if="submitting" class="fas fa-circle-notch fa-spin"></i>
            <i v-else class="fas fa-check"></i>
            Подтвердить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const loading = ref(false)
const submitting = ref(false)
const pendingUsers = ref([])

// Модальное окно
const showModal = ref(false)
const selectedUser = ref(null)
const assignRole = ref('warehouse')
const assignJobTitle = ref('Кладовщик')

const defaultJobTitles = {
  warehouse: 'Кладовщик склада торфа',
  driver: 'Водитель грузового автомобиля',
  manager: 'Финансовый менеджер',
  master: 'Мастер-бригадир участка',
  director: 'Генеральный директор',
  admin: 'Администратор системы'
}

function updateDefaultJobTitle() {
  assignJobTitle.value = defaultJobTitles[assignRole.value] || 'Сотрудник'
}

function getRoleName(role) {
  const map = {
    admin: 'Администратор',
    director: 'Директор',
    manager: 'Фин. менеджер',
    master: 'Мастер-бригадир',
    warehouse: 'Кладовщик',
    driver: 'Водитель'
  }
  return map[role] || role
}

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function fetchPending() {
  loading.value = true
  try {
    const { data } = await api.get('/auth/pending')
    pendingUsers.value = data
  } catch (e) {
    app.toast('err', '❌ Ошибка', 'Не удалось загрузить список заявок')
  } finally {
    loading.value = false
  }
}

function openApproveModal(user) {
  selectedUser.value = user
  assignRole.value = user.role || 'warehouse'
  updateDefaultJobTitle()
  showModal.value = true
}

async function submitApprove() {
  if (!assignJobTitle.value) {
    app.toast('warn', '⚠️ Внимание', 'Укажите должность сотрудника')
    return
  }

  submitting.value = true
  try {
    await api.post(`/auth/approve/${selectedUser.value.id}`, {
      role: assignRole.value,
      job_title: assignJobTitle.value
    })
    app.toast('ok', '✅ Успешно', `Пользователь ${selectedUser.value.name} одобрен!`)
    showModal.value = false
    fetchPending()
  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Не удалось одобрить пользователя')
  } finally {
    submitting.value = false
  }
}

async function rejectUser(user) {
  if (!confirm(`Вы действительно хотите отклонить и удалить заявку от ${user.name}?`)) {
    return
  }

  try {
    await api.delete(`/auth/reject/${user.id}`)
    app.toast('ok', '✅ Отклонено', 'Заявка успешно удалена')
    fetchPending()
  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Не удалось отклонить заявку')
  }
}

onMounted(() => {
  fetchPending()
})
</script>
