<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">Склад товаров</div>
        <div class="ps">Мониторинг запасов и складские операции</div>
      </div>
      <div class="ph-r" style="align-items: center; flex-wrap: wrap;">
        <div v-if="loading || loadingAllProducts" style="color: var(--primary); font-size: 13px; display: flex; align-items: center; gap: 6px; margin-right: 8px;">
          <i class="fas fa-circle-notch fa-spin"></i>
          <span>Обновление...</span>
        </div>
        <div style="display:flex; flex-direction:column; gap:4px; margin-right: 10px;">
          <select v-model="selectedWarehouse" class="fin fin-sm" @change="loadData(false)" :disabled="loading && !warehouses.length">
             <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
          <select v-model="selectedProduct" class="fin fin-sm" @change="loadData(false)" :disabled="loading && !products.length">
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

    <!-- Сводная таблица по всей номенклатуре -->
      <div class="card mb4">
        <div class="ch" style="display: flex; justify-content: space-between; align-items: center;">
          <span class="ct">
            <i class="fas fa-list-alt tb" style="margin-right: 6px;"></i>
            Текущие остатки по всей номенклатуре на складе
          </span>
          <span class="fs12 tm">Нажмите на строку товара для переключения графиков и журнала операций ниже</span>
        </div>
        <div class="tw">
          <table>
            <thead>
              <tr>
                <th>Наименование товара / сырья</th>
                <th>Текущий остаток</th>
                <th>Ёмкость склада</th>
                <th>Заполненность</th>
                <th>Состояние</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="item in allProductsStatus" 
                :key="item.id"
                :class="['clickable-row', { 'active-row': selectedProduct === item.id }]"
                @click="selectProductFromTable(item.id)"
              >
                <td class="fw6">
                  <i :class="getProductIcon(item.name)" style="margin-right: 8px;"></i>
                  {{ item.name }}
                </td>
                <td class="fw6">{{ item.current_stock }} т / шт</td>
                <td class="tm">{{ item.capacity }} т / шт</td>
                <td>
                  <div class="flex itemsC" style="gap: 8px;">
                    <span class="fs12 fw6" style="min-width: 35px;">{{ item.percent }}%</span>
                    <div class="prw" style="flex: 1; max-width: 150px;">
                      <div class="prf" :style="{ width: item.percent + '%', background: getStatusColorVal(item.status) }"></div>
                    </div>
                  </div>
                </td>
                <td>
                  <span :class="['badge', getStatusBadgeClass(item.status)]">
                    {{ getStatusTextVal(item.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

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

const allProductsStatus = ref([])
const loadingAllProducts = ref(false)

function getProductIcon(name) {
  if (!name) return 'fas fa-box tm'
  const nameL = name.toLowerCase()
  if (nameL.includes('кусковой')) return 'fas fa-mountain ty'
  if (nameL.includes('низинный')) return 'fas fa-water tb'
  if (nameL.includes('nortpeat')) return 'fas fa-leaf tg'
  if (nameL.includes('удобрение')) return 'fas fa-flask tp'
  return 'fas fa-box tm'
}

function getStatusColorVal(st) {
  if (st === 'crit') return '#ef4444'
  if (st === 'warn') return '#f59e0b'
  return '#22c55e'
}

function getStatusBadgeClass(st) {
  if (st === 'crit') return 'b-err'
  if (st === 'warn') return 'b-warn'
  return 'b-ok'
}

function getStatusTextVal(st) {
  const map = { ok: 'Норма', warn: 'Низкий', crit: 'Критичен' }
  return map[st] || '—'
}

function selectProductFromTable(id) {
  selectedProduct.value = id
  loadData()
}

async function loadAllProductsStatus() {
  if (!selectedWarehouse.value || !products.value.length) return
  loadingAllProducts.value = true
  try {
    const results = await Promise.all(
      products.value.map(async (p) => {
        try {
          const res = await api.get(`/warehouse/status?warehouse_id=${selectedWarehouse.value}&product_id=${p.id}`)
          return {
            id: p.id,
            name: p.name,
            current_stock: res.data.current_stock,
            capacity: res.data.capacity,
            percent: res.data.percent,
            status: res.data.status
          }
        } catch (err) {
          console.error(`Failed to load status for product ${p.id}`, err)
          return {
            id: p.id,
            name: p.name,
            current_stock: 0,
            capacity: 5000,
            percent: 0,
            status: 'ok'
          }
        }
      })
    )
    allProductsStatus.value = results
  } catch (err) {
    console.error(err)
  } finally {
    loadingAllProducts.value = false
  }
}

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
    const currentMonthIdx = new Date().getMonth()
    const dynamicStock = mockStock.map((val, idx) => {
      if (idx < currentMonthIdx) return val
      if (idx === currentMonthIdx) return status.value ? status.value.current_stock : val
      return null
    })
    const dynamicCons = mockCons.map((val, idx) => {
      if (idx <= currentMonthIdx) return val
      return null
    })

    if (lineChart) lineChart.destroy()
    lineChart = new Chart(el1, {
      type: 'line',
      data: {
        labels: months,
        datasets: [
          { label: 'Остаток', data: dynamicStock, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,.07)', fill: true, tension: .4, pointRadius: 3 },
          { label: 'Потребление (расход)', data: dynamicCons, borderColor: '#f59e0b', fill: false, tension: .4, borderDash: [5, 4], pointRadius: 3 },
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

async function loadData(isInitial = false) {
  if (!isSelectionValid.value) {
    if (isInitial === true) loading.value = false
    return
  }
  if (isInitial === true) {
    loading.value = true
  }
  try {
    const qs = `?warehouse_id=${selectedWarehouse.value}&product_id=${selectedProduct.value}`
    const [stRes, opRes] = await Promise.all([
      api.get(`/warehouse/status${qs}`),
      api.get(`/warehouse/operations${qs}`)
    ])
    status.value = stRes.data
    ops.value = opRes.data

    // Загружаем всю сводку по товарам в фоновом режиме
    loadAllProductsStatus()

    nextTick(() => {
      setTimeout(initCharts, 100)
    })
  } catch (e) {
    console.error("loadData error:", e)
    app.toast('err', '❌ Ошибка', 'Не удалось загрузить данные склада')
  } finally {
    if (isInitial === true) {
      loading.value = false
    }
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
    
    // Перезагрузка статуса и всей сводки
    const [newStatusRes] = await Promise.all([
      api.get(`/warehouse/status${qs}`),
      loadAllProductsStatus()
    ])
    status.value = newStatusRes.data

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
  try {
    await loadDictionaries()
    await loadData(true)
  } catch (err) {
    console.error("Initialization failed", err)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  lineChart?.destroy()
  donutChart?.destroy()
})
</script>

<style scoped>
.clickable-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.clickable-row:hover {
  background-color: #f1f5f9 !important;
}
.active-row {
  background-color: #eff6ff !important;
}
.active-row td:first-child {
  border-left: 4px solid #2563eb;
  padding-left: 9px;
}
</style>