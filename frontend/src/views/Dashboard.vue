<template>
  <div>
    <div class="wbar mb4 flex justB itemsC" style="flex-wrap: wrap; gap: 12px;">
      <div>
        <div class="wb-t">Добро пожаловать, {{ auth.user?.full_name?.split(' ')[0] || 'Пользователь' }}! 👋</div>
        <div class="wb-s">Система управления ООО «НОРД-ИСТ ГРУПП»</div>
        <div class="wb-d">{{ today }}</div>
      </div>
      <!-- Выбор склада -->
      <div v-if="warehouses.length > 0" class="flex itemsC" style="z-index: 10; gap: 8px;">
        <span style="font-size: 13px; font-weight: 500; opacity: 0.95; display: flex; align-items: center; gap: 4px;">
          <i class="fas fa-warehouse"></i> Склад:
        </span>
        <select v-model="selectedWarehouse" @change="onWarehouseChange" class="fin fin-sm" style="width: 200px; background: rgba(255, 255, 255, 0.15); color: #fff; border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 8px; font-weight: 500; cursor: pointer;">
          <option v-for="w in warehouses" :key="w.id" :value="w.id" style="color: var(--text);">{{ w.name }}</option>
        </select>
      </div>
    </div>

    <div v-if="warehouseStatus && warehouseStatus.status !== 'ok'"
      :class="['alert', warehouseStatus.status === 'crit' ? 'al-err' : 'al-warn']" class="mb4">
      <i :class="['fas', warehouseStatus.status === 'crit' ? 'fa-exclamation-circle' : 'fa-exclamation-triangle']"></i>
      <span>
        <b>{{ warehouseStatus.status === 'crit' ? 'Критический' : 'Низкий' }} уровень торфа!</b>
        Текущий остаток: <b>{{ warehouseStatus.current_stock }} т</b> ({{ warehouseStatus.percent }}% ёмкости).
        {{ warehouseStatus.status === 'crit' ? 'Требуется немедленное пополнение!' : 'Рекомендуется пополнить запасы.'
        }}
      </span>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div> Загрузка данных...
    </div>

    <template v-else>
      <div class="g g4 mb4">
        <div class="kpi">
          <div class="kico ico-b"><i class="fas fa-cubes"></i></div>
          <div>
            <div class="klb">Остаток торфа</div>
            <div class="kv">{{ warehouseStatus?.current_stock ?? 0 }} <span
                style="font-size:14px;font-weight:400">т</span></div>
            <div :class="['ks', warehouseStatus?.status === 'ok' ? 'up' : 'dn']">
              <i :class="['fas', warehouseStatus?.status === 'ok' ? 'fa-arrow-up' : 'fa-arrow-down']"></i>
              {{ warehouseStatus?.percent ?? 0 }}% ёмкости
            </div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-g"><i class="fas fa-file-alt"></i></div>
          <div>
            <div class="klb">Документов всего</div>
            <div class="kv">{{ stats?.total_documents ?? 0 }}</div>
            <div class="ks"><i class="fas fa-clock"></i> {{ stats?.pending_documents ?? 0 }} ожидают</div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-y"><i class="fas fa-users"></i></div>
          <div>
            <div class="klb">Сотрудников</div>
            <div class="kv">{{ stats?.total_users ?? 0 }}</div>
            <div class="ks up"><i class="fas fa-check-circle"></i> В штате</div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-s"><i class="fas fa-truck"></i></div>
          <div>
            <div class="klb">Путевых сегодня</div>
            <div class="kv">{{ stats?.waybills_today ?? 0 }}</div>
            <div class="ks up"><i class="fas fa-road"></i> Активны</div>
          </div>
        </div>
      </div>

      <div class="g g2 mb4">
        <div class="card">
          <div class="ch"><span class="ct"><i class="fas fa-chart-line tb" style="margin-right:6px;"></i>Динамика
              запасов торфа (год)</span></div>
          <div class="cb">
            <div style="height:220px;"><canvas id="dash-stock"></canvas></div>
          </div>
        </div>
        <div class="card">
          <div class="ch"><span class="ct"><i class="fas fa-warehouse ty" style="margin-right:6px;"></i>Заполнение
              склада</span></div>
          <div class="cb">
            <div style="height:160px;"><canvas id="dash-donut"></canvas></div>
            <div class="flex itemsC justB mt3" style="padding:0 8px;">
              <span class="fs12 tm">Занято: <b>{{ warehouseStatus?.current_stock ?? 0 }} т</b></span>
              <span class="fs12 tm">Свободно: <b>{{ (warehouseStatus?.capacity ?? 2000) -
                (warehouseStatus?.current_stock ?? 0) }} т</b></span>
            </div>
          </div>
        </div>
      </div>

      <div class="g g2">
        <div class="card">
          <div class="ch">
            <span class="ct">Последние операции</span>
            <a href="#" class="fs12 tb" @click.prevent="$router.push('/warehouse')">Склад →</a>
          </div>
          <div class="cb" style="padding:0 16px;">
            <div v-if="!recentOps.length" class="tm tc" style="padding:20px;">Операций пока нет</div>
            <div v-for="op in recentOps.slice(0, 5)" :key="op.id" class="act-item">
              <i :class="['fas', op.operation_type === 'in' ? 'fa-arrow-down tg' : 'fa-arrow-up tr2']"
                style="margin-top:3px;font-size:12px;width:14px;"></i>
              <div>
                <div class="act-t">{{ op.operation_type === 'in' ? 'Приход' : 'Расход' }}: <b>{{ op.quantity }} т</b> —
                  {{ op.source }}</div>
                <div class="act-d">{{ formatDate(op.created_at) }} · {{ op.employee_name }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="ch">
            <span class="ct">Нужно подписать</span>
            <a href="#" class="fs12 tb" @click.prevent="$router.push('/documents')">Документы →</a>
          </div>
          <div class="cb" style="padding:0 16px;">
            <div v-if="!pendingDocs.length" class="tm tc" style="padding:20px;">Все документы обработаны</div>
            <div v-for="doc in pendingDocs.slice(0, 5)" :key="doc.id" class="act-item">
              <i class="fas fa-file-signature tb" style="margin-top:3px;font-size:12px;width:14px;"></i>
              <div>
                <div class="act-t">{{ typeLabel(doc.document_type) }} <b>№{{ doc.number }}</b></div>
                <div class="act-d">{{ doc.employee_name }} · {{ formatDate(doc.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(true)
const warehouseStatus = ref(null)
const stats = ref(null)
const recentOps = ref([])
const pendingDocs = ref([])

const warehouses = ref([])
const selectedWarehouse = ref(null)

const today = new Date().toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

const typeLabels = { vacation: 'Отпуск', travel: 'Командировка', waybill: 'Путевой лист', employment: 'Договор' }
function typeLabel(t) { return typeLabels[t] || t }

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

// Charts (Демо-данные для линии, если бэкенд пока не отдает историю за год)
const peatStock = [1450, 1380, 1310, 1240, 1180, 1120, 1080, 1040, 1090, 1140, 1200, 1247]
const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
let stockChart = null
let donutChart = null

function initCharts() {
  // Линейный график динамики
  const el1 = document.getElementById('dash-stock')
  if (el1) {
    const currentMonthIdx = new Date().getMonth()
    const dynamicStock = peatStock.map((val, idx) => {
      if (idx < currentMonthIdx) return val
      if (idx === currentMonthIdx) return warehouseStatus.value ? warehouseStatus.value.current_stock : val
      return null
    })

    if (stockChart) stockChart.destroy()
    stockChart = new Chart(el1, {
      type: 'line',
      data: {
        labels: months,
        datasets: [{
          label: 'Остаток торфа (т)',
          data: dynamicStock,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,.08)',
          fill: true,
          tension: .4,
          pointRadius: 3
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { grid: { color: '#f1f5f9' } } } }
    })
  }

  // Кольцевой график склада
  const el2 = document.getElementById('dash-donut')
  if (el2 && warehouseStatus.value) {
    const cur = warehouseStatus.value.current_stock
    const cap = warehouseStatus.value.capacity
    const clr = warehouseStatus.value.status === 'crit' ? '#ef4444' : warehouseStatus.value.status === 'warn' ? '#f59e0b' : '#22c55e'
    
    if (donutChart) donutChart.destroy()
    donutChart = new Chart(el2, {
      type: 'doughnut',
      data: {
        labels: ['Занято', 'Свободно'],
        datasets: [{
          data: [cur, Math.max(0, cap - cur)],
          backgroundColor: [clr, '#f1f5f9'],
          borderWidth: 0
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: { legend: { display: false } } }
    })
  }
}

async function loadWarehouseData() {
  if (!selectedWarehouse.value) return
  try {
    const [ws, ops] = await Promise.all([
      api.get(`/warehouse/status?warehouse_id=${selectedWarehouse.value}&product_id=1`).catch(() => null),
      api.get(`/warehouse/operations?warehouse_id=${selectedWarehouse.value}&product_id=1&limit=10`).catch(() => null)
    ])
    if (ws) warehouseStatus.value = ws.data
    if (ops) recentOps.value = ops.data
  } catch (e) {
    console.error("Ошибка загрузки данных склада на Dashboard:", e)
  }
}

async function onWarehouseChange() {
  await loadWarehouseData()
  nextTick(() => {
    initCharts()
  })
}

onMounted(async () => {
  try {
    const whRes = await api.get('/warehouse/list').catch(() => null)
    if (whRes && whRes.data.length > 0) {
      warehouses.value = whRes.data
      selectedWarehouse.value = whRes.data[0].id
    }
    await loadWarehouseData()

    const [st, docs] = await Promise.all([
      api.get('/analytics/dashboard').catch(() => null),
      api.get('/documents/').catch(() => null),
    ])
    if (st) stats.value = st.data
    if (docs) pendingDocs.value = docs.data.filter(d => d.status === 'pending')
  } catch (e) {
    console.error("Ошибка загрузки Dashboard:", e)
  } finally {
    loading.value = false
    // Небольшая задержка, чтобы DOM успел отрисоваться для Chart.js
    nextTick(() => setTimeout(initCharts, 150))
  }
})

onUnmounted(() => {
  stockChart?.destroy()
  donutChart?.destroy()
})
</script>