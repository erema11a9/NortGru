<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">Аналитика</div>
        <div class="ps">Производственные показатели и динамика потребления торфа</div>
      </div>
      <div class="ph-r">
        <button class="btn btn-ghost" @click="app.toast('info','📊 Экспорт','Выгрузка Excel формируется...')">
          <i class="fas fa-file-excel tg"></i> Excel
        </button>
        <button class="btn btn-ghost" @click="app.toast('info','📄 Экспорт','PDF отчёт формируется...')">
          <i class="fas fa-file-pdf tr2"></i> PDF
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading"><div class="spinner"></div> Загрузка аналитики...</div>

    <template v-else>
      <!-- KPI -->
      <div class="g g4 mb4">
        <div class="kpi">
          <div class="kico ico-b"><i class="fas fa-industry"></i></div>
          <div>
            <div class="klb">Произведено (год)</div>
            <div class="kv">{{ data?.total_production ?? 0 }} т</div>
            <div class="ks up"><i class="fas fa-arrow-up"></i> +8.2%</div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-g"><i class="fas fa-shipping-fast"></i></div>
          <div>
            <div class="klb">Отгружено (год)</div>
            <div class="kv">{{ data?.total_shipping ?? 0 }} т</div>
            <div class="ks up"><i class="fas fa-arrow-up"></i> +6.5%</div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-y"><i class="fas fa-leaf"></i></div>
          <div>
            <div class="klb">Потреблено торфа</div>
            <div class="kv">{{ data?.total_peat ?? 0 }} т</div>
            <div class="ks dn"><i class="fas fa-arrow-down"></i> -3.1%</div>
          </div>
        </div>
        <div class="kpi">
          <div class="kico ico-s"><i class="fas fa-percentage"></i></div>
          <div>
            <div class="klb">Эффективность</div>
            <div class="kv">{{ data?.efficiency ?? 0 }}%</div>
            <div class="ks up"><i class="fas fa-arrow-up"></i> +2.1%</div>
          </div>
        </div>
      </div>

      <!-- Charts row -->
      <div class="g g2 mb4">
        <div class="card">
          <div class="ch"><span class="ct"><i class="fas fa-chart-bar tb" style="margin-right:6px;"></i>Производство vs Отгрузка</span></div>
          <div class="cb"><div style="height:240px;"><canvas id="an-bar"></canvas></div></div>
        </div>
        <div class="card">
          <div class="ch"><span class="ct"><i class="fas fa-chart-area ty" style="margin-right:6px;"></i>Динамика потребления торфа</span></div>
          <div class="cb"><div style="height:240px;"><canvas id="an-line"></canvas></div></div>
        </div>
      </div>

      <!-- Table -->
      <div class="card">
        <div class="ch"><span class="ct">Показатели по месяцам (2025)</span></div>
        <div class="tw">
          <table>
            <thead>
              <tr>
                <th>Месяц</th>
                <th>Производство (т)</th>
                <th>Отгрузка (т)</th>
                <th>Потребление торфа (т)</th>
                <th>Остаток торфа (т)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, i) in data.monthly_labels" :key="i">
                <td class="fw6">{{ m }}</td>
                <td>{{ data.production[i] }}</td>
                <td>{{ data.shipping[i] }}</td>
                <td class="ty">{{ data.peat_consumption[i] }}</td>
                <td class="tb">{{ data.peat_stock[i] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const app     = useAppStore()
const loading = ref(true)
const data    = ref(null)

let barChart  = null
let lineChart = null

function initCharts() {
  if (!data.value) return
  const el1 = document.getElementById('an-bar')
  if (el1) {
    barChart = new Chart(el1, {
      type: 'bar',
      data: { labels: data.value.monthly_labels, datasets: [
        { label: 'Производство (т)', data: data.value.production, backgroundColor: 'rgba(37,99,235,.8)', borderRadius: 4 },
        { label: 'Отгрузка (т)',     data: data.value.shipping,   backgroundColor: 'rgba(34,197,94,.8)', borderRadius: 4 },
      ]},
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { x: { grid: { display: false } }, y: { grid: { color: '#f1f5f9' } } } }
    })
  }
  const el2 = document.getElementById('an-line')
  if (el2) {
    lineChart = new Chart(el2, {
      type: 'line',
      data: { labels: data.value.monthly_labels, datasets: [{
        label: 'Потребление торфа (т)', data: data.value.peat_consumption,
        borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,.1)', fill: true, tension: .4, pointRadius: 3,
      }]},
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { x: { grid: { display: false } }, y: { grid: { color: '#f1f5f9' } } } }
    })
  }
}

onMounted(async () => {
  try {
    const { data: d } = await api.get('/analytics/')
    data.value = d
  } catch (e) {
    app.toast('err', '❌ Ошибка', 'Не удалось загрузить аналитику')
  } finally {
    loading.value = false
    nextTick(() => setTimeout(initCharts, 100))
  }
})

onUnmounted(() => { barChart?.destroy(); lineChart?.destroy() })
</script>
