<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">Склад товаров</div>
        <div class="ps">Мониторинг запасов и складские операции</div>
      </div>
      <div class="ph-r" style="display: flex; gap: 10px; align-items: center;">
        <div style="display:flex; flex-direction:column; gap:4px; margin-right: 10px;">
          <select v-model="selectedWarehouse" class="fin fin-sm" @change="loadData" :disabled="loading">
             <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
          <select v-model="selectedProduct" class="fin fin-sm" @change="loadData" :disabled="loading">
             <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="openModal('in')" :disabled="!isSelectionValid">
          <i class="fas fa-arrow-down"></i> Приход
        </button>
        <button class="btn btn-danger" @click="openModal('out')" :disabled="!isSelectionValid">
          <i class="fas fa-arrow-up"></i> Расход
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading" style="padding: 40px; text-align: center;">
      <i class="fas fa-circle-notch fa-spin fa-2x"></i>
      <div style="margin-top: 10px; color: #64748b;">Загрузка данных склада...</div>
    </div>

    <template v-else-if="status">
      <div class="g g4 mb4">
        <div :class="['peat-box', 'peat-' + (status?.status ?? 'ok')]">
          <div class="peat-num">{{ status?.current_stock ?? '—' }}</div>
          <div class="peat-unit">т / шт</div>
          <div class="peat-lbl">Текущий остаток</div>
        </div>
        <div class="kpi">
          <div class="kico ico-b"><i class="fas fa-database"></i></div>
          <div>
            <div class="klb">Ёмкость склада</div>
            <div class="kv">{{ status?.capacity }}</div>
            <div class="ks">Максимум</div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-g"><i class="fas fa-chart-pie"></i></div>
          <div>
            <div class="klb">Заполненность</div>
            <div class="kv">{{ status?.percent ?? 0 }}%</div>
            <div class="prw mt2">
              <div class="prf" :style="{ width: (status?.percent ?? 0) + '%', background: statusColor }"></div>
            </div>
          </div>
        </div>
        <div class="kpi">
          <div :class="['kico', status?.status === 'crit' ? 'ico-r' : status?.status === 'warn' ? 'ico-y' : 'ico-g']">
            <i
              :class="['fas', status?.status === 'crit' ? 'fa-exclamation-circle' : status?.status === 'warn' ? 'fa-exclamation-triangle' : 'fa-check-circle']"></i>
          </div>
          <div>
            <div class="klb">Статус</div>
            <div class="kv" style="font-size:18px;">{{ statusText }}</div>
            <div class="ks">Текущее состояние</div>
          </div>
        </div>
      </div>

      <div class="g g2 mb4">
        <div class="card">
          <div class="ch"><span class="ct">Динамика остатков и потребления</span></div>
          <div class="cb">
            <div style="height:220px;"><canvas id="wh-line"></canvas></div>
          </div>
        </div>
        <div class="card">
          <div class="ch"><span class="ct">Использование ёмкости склада</span></div>
          <div class="cb">
            <div style="height:220px;"><canvas id="wh-donut"></canvas></div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="ch">
          <span class="ct">Журнал операций</span>
          <span class="fs12 tm">Последние записи по выбранному товару</span>
        </div>
        <div class="tw">
          <table>
            <thead>
              <tr>
                <th>Дата</th>
                <th>Тип</th>
                <th>Количество</th>
                <th>Источник / Назначение</th>
                <th>Остаток после</th>
                <th>Сотрудник</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="op in ops" :key="op.id">
                <td class="fs12 tm">{{ formatDate(op.created_at) }}</td>
                <td>
                  <span :class="['badge', op.type === 'in' ? 'b-ok' : 'b-err']">
                    <i :class="['fas fa-xs', op.type === 'in' ? 'fa-arrow-down' : 'fa-arrow-up']"></i>
                    {{ op.type === 'in' ? 'Приход' : 'Расход' }}
                  </span>
                </td>
                <td class="fw6">{{ op.amount }}</td>
                <td>{{ op.source || '—' }}</td>
                <td class="fw6">{{ op.balance_after }}</td>
                <td class="tm">{{ op.employee_name }}</td>
              </tr>
              <tr v-if="!ops.length">
                <td colspan="6" style="text-align:center; padding: 20px; color: var(--muted)">Операций пока нет</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-if="opMod" class="ov" @click.self="opMod = false">
      <div class="modal">
        <div class="mh">
          <div :class="['mh-ico', opType === 'in' ? 'ico-g' : 'ico-r']">
            <i :class="['fas', opType === 'in' ? 'fa-arrow-down' : 'fa-arrow-up']"></i>
          </div>
          <span class="mt2">{{ opType === 'in' ? 'Оприходование товара' : 'Списание товара' }}</span>
          <button class="mc" @click="opMod = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody">
          <div class="fgr">
            <label class="fll">Количество *</label>
            <input v-model.number="opAmt" class="fin" type="number" min="0.1" step="0.1" placeholder="150" />
          </div>
          <div class="fgr">
            <label class="fll">Основание / Описание</label>
            <input v-model="opSrc" class="fin" type="text"
              :placeholder="opType === 'in' ? 'Поставка №...' : 'Выдача на производство...'" />
          </div>
        </div>
        <div class="mfoot">
          <button class="btn btn-ghost" @click="opMod = false">Отмена</button>
          <button :class="['btn', opType === 'in' ? 'btn-success' : 'btn-danger']" :disabled="saving" @click="submitOp">
            <i v-if="saving" class="fas fa-circle-notch fa-spin"></i>
            <i v-else class="fas fa-check"></i>
            Записать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const app = useAppStore()

const loading = ref(true)
const saving = ref(false)
const status = ref(null)
const ops = ref([])

const warehouses = ref([])
const products = ref([])
const selectedWarehouse = ref(null)
const selectedProduct = ref(null)

const opMod = ref(false)
const opType = ref('in')
const opAmt = ref('')
const opSrc = ref('')

// Данные графиков (заглушка)
const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
const mockStock = [1450, 1380, 1310, 1240, 1180, 1120, 1080, 1040, 1090, 1140, 1200, 1247]
const mockCons = [120, 140, 130, 155, 165, 185, 172, 162, 178, 192, 205, 188]

const isSelectionValid = computed(() => selectedWarehouse.value && selectedProduct.value)

const statusColor = computed(() => {
  if (status.value?.status === 'crit') return '#ef4444'
  if (status.value?.status === 'warn') return '#f59e0b'
  return '#22c55e'
})

const statusText = computed(() => {
  const map = { ok: 'Норма', warn: 'Низкий', crit: 'Критичен' }
  return map[status.value?.status] || '—'
})

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

let lineChart = null
let donutChart = null

function initCharts() {
  const el1 = document.getElementById('wh-line')
  if (el1) {
    if (lineChart) lineChart.destroy()
    lineChart = new Chart(el1, {
      type: 'line',
      data: {
        labels: months,
        datasets: [
          { label: 'Остаток', data: mockStock, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,.07)', fill: true, tension: .4, pointRadius: 3 },
          { label: 'Потребление (расход)', data: mockCons, borderColor: '#f59e0b', fill: false, tension: .4, borderDash: [5, 4], pointRadius: 3 },
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
    })
  }
  updateDonut()
}

function updateDonut() {
  const el2 = document.getElementById('wh-donut')
  if (!el2 || !status.value) return

  const cur = status.value.current_stock
  const cap = status.value.capacity

  if (donutChart) donutChart.destroy()

  donutChart = new Chart(el2, {
    type: 'doughnut',
    data: {
      labels: ['Занято', 'Свободно'],
      datasets: [{
        data: [cur, Math.max(0, cap - cur)],
        backgroundColor: [statusColor.value, '#f1f5f9'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: { legend: { position: 'bottom' } }
    }
  })
}

async function loadDictionaries() {
  try {
    const [whRes, prRes] = await Promise.all([
      api.get('/warehouse/list'),
      api.get('/warehouse/products')
    ])
    warehouses.value = whRes.data
    products.value = prRes.data
    
    if (warehouses.value.length > 0) selectedWarehouse.value = warehouses.value[0].id
    if (products.value.length > 0) selectedProduct.value = products.value[0].id
  } catch (e) {
    console.error(e)
    app.toast('err', 'Ошибка', 'Не удалось загрузить списки складов и товаров')
  }
}

async function loadData() {
  if (!isSelectionValid.value) return
  loading.value = true
  try {
    const qs = `?warehouse_id=${selectedWarehouse.value}&product_id=${selectedProduct.value}`
    const [stRes, opRes] = await Promise.all([
      api.get(`/warehouse/status${qs}`),
      api.get(`/warehouse/operations${qs}`)
    ])
    status.value = stRes.data
    ops.value = opRes.data

    nextTick(() => {
      setTimeout(initCharts, 100)
    })
  } catch (e) {
    app.toast('err', '❌ Ошибка', 'Не удалось загрузить данные склада')
  } finally {
    loading.value = false
  }
}

function openModal(type) {
  if (!isSelectionValid.value) return
  opType.value = type
  opAmt.value = ''
  opSrc.value = ''
  opMod.value = true
}

async function submitOp() {
  const amt = parseFloat(opAmt.value)
  if (!amt || amt <= 0) {
    app.toast('warn', '⚠️ Ошибка', 'Введите корректное количество')
    return
  }
  saving.value = true
  try {
    const qs = `?warehouse_id=${selectedWarehouse.value}&product_id=${selectedProduct.value}`
    const { data: newOp } = await api.post(`/warehouse/operations${qs}`, {
      type: opType.value,
      amount: amt,
      description: opSrc.value || (opType.value === 'in' ? 'Поставка' : 'В производство')
    })

    ops.value.unshift(newOp)
    
    // Перезагрузка статуса
    const { data: newStatus } = await api.get(`/warehouse/status${qs}`)
    status.value = newStatus

    app.toast('ok', '✅ Записано', `${opType.value === 'in' ? 'Приход' : 'Расход'}: ${amt}`)
    opMod.value = false
    nextTick(updateDonut)

  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Ошибка при сохранении')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
    loading.value = true
    await loadDictionaries()
    await loadData()
})

onUnmounted(() => {
  lineChart?.destroy()
  donutChart?.destroy()
})
</script>