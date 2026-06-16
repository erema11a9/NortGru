<template>
    <div>
        <div class="ph">
            <div class="ph-l">
                <div class="pt">Транспорт и логистика</div>
                <div class="ps">Учет путевых листов, контроль пробега и расхода ГСМ</div>
            </div>
            <div class="ph-r" style="flex-wrap: wrap;">
                <button class="btn btn-ghost" @click="loadData">
                    <i class="fas fa-sync-alt"></i> Обновить
                </button>
                <button class="btn btn-ghost" @click="exportXML">
                    <i class="fas fa-file-code"></i> Выгрузить XML
                </button>
                <button class="btn btn-primary" @click="openModal">
                    <i class="fas fa-plus"></i> Новый путевой лист
                </button>
            </div>
        </div>

        <div class="g g4 mb4">
            <div class="kpi">
                <div class="kico ico-b"><i class="fas fa-truck-moving"></i></div>
                <div>
                    <div class="klb">Рейсов сегодня</div>
                    <div class="kv">{{ stats.today_trips }}</div>
                </div>
            </div>
            <div class="kpi">
                <div class="kico ico-g"><i class="fas fa-gas-pump"></i></div>
                <div>
                    <div class="klb">Расход ГСМ (л)</div>
                    <div class="kv">{{ stats.fuel_consumed }}</div>
                    <div class="ks">за тек. месяц</div>
                </div>
            </div>
            <div class="kpi">
                <div class="kico ico-y"><i class="fas fa-road"></i></div>
                <div>
                    <div class="klb">Общий пробег</div>
                    <div class="kv">{{ stats.total_distance }} км</div>
                </div>
            </div>
            <div class="kpi">
                <div class="kico ico-r"><i class="fas fa-weight-hanging"></i></div>
                <div>
                    <div class="klb">Перевезено груза</div>
                    <div class="kv">{{ stats.total_weight }} т</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="ch">
                <span class="ct">Журнал путевых листов</span>
                <div class="flex g2u">
                    <input v-model="search" type="text" class="fin fin-sm"
                        placeholder="Поиск по водителю или авто..." />
                </div>
            </div>
            <div class="tw">
                <table>
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Дата</th>
                            <th>Транспорт / Водитель</th>
                            <th>Маршрут</th>
                            <th>Груз (т)</th>
                            <th>Топливо (л)</th>
                            <th>Статус</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="item in filteredWaybills" :key="item.id">
                            <td class="fw6">{{ item.number }}</td>
                            <td class="fs12 tm">{{ formatDate(item.date) }}</td>
                            <td>
                                <div class="fw6">{{ item.vehicle }}</div>
                                <div class="fs11 tm">{{ item.driver }}</div>
                            </td>
                            <td class="fs12">{{ item.route_from }} &rarr; {{ item.route_to }}</td>
                            <td class="fw6">{{ item.cargo_weight || '—' }}</td>
                            <td>
                                <div class="fs12">Факт: <b>{{ item.fuel_actual }}</b></div>
                            </td>
                            <td>
                                <span :class="['badge', statusClass(item.status)]">
                                    {{ statusLabel(item.status) }}
                                </span>
                            </td>
                            <td>
                                <button v-if="item.status === 'active'" class="btn btn-sm btn-ghost"
                                    @click="openCompleteModal(item)">
                                    Завершить
                                </button>
                            </td>
                        </tr>
                        <tr v-if="!filteredWaybills.length">
                            <td colspan="8" style="text-align:center; padding: 20px;">Нет данных</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Модалка создания ПЛ -->
        <div v-if="mod" class="ov" @click.self="mod = false">
            <div class="modal" style="max-width: 600px;">
                <div class="mh">
                    <div class="mh-ico ico-b"><i class="fas fa-file-invoice"></i></div>
                    <span>Оформление путевого листа (Выезд)</span>
                    <button class="mc" @click="mod = false"><i class="fas fa-times"></i></button>
                </div>
                <div class="mbody">
                    <div class="g g2 g2u mb3">
                        <div class="fgr">
                            <label class="fll">Транспортное средство *</label>
                            <select v-model="form.vehicle_id" class="fin">
                                <option value="" disabled>Выберите авто</option>
                                <option v-for="v in vehicles" :key="v.id" :value="v.id">
                                    {{ v.name }} ({{ v.plate }})
                                </option>
                            </select>
                        </div>
                        <div class="fgr">
                            <label class="fll">Водитель *</label>
                            <input v-model="form.driver" type="text" class="fin" placeholder="ФИО" />
                        </div>
                    </div>

                    <div class="g g2 g2u mb3">
                        <div class="fgr">
                            <label class="fll">Пункт отправления</label>
                            <input v-model="form.route_from" type="text" class="fin" placeholder="Участок добычи" />
                        </div>
                        <div class="fgr">
                            <label class="fll">Пункт назначения</label>
                            <input v-model="form.route_to" type="text" class="fin" placeholder="Склад №1" />
                        </div>
                    </div>

                    <div class="g g2 g2u">
                        <div class="fgr">
                            <label class="fll">Одометр (при выезде) *</label>
                            <input v-model.number="form.odo_start" type="number" class="fin" />
                        </div>
                        <div class="fgr">
                            <label class="fll">Топливо в баке (л) *</label>
                            <input v-model.number="form.fuel_start" type="number" class="fin" />
                        </div>
                    </div>
                </div>
                <div class="mfoot">
                    <button class="btn btn-ghost" @click="mod = false">Отмена</button>
                    <button class="btn btn-primary" :disabled="saving" @click="save">
                        <i v-if="saving" class="fas fa-circle-notch fa-spin"></i>
                        <i v-else class="fas fa-check"></i> Создать лист
                    </button>
                </div>
            </div>
        </div>

        <!-- Модалка завершения ПЛ -->
        <div v-if="completeMod" class="ov" @click.self="completeMod = false">
            <div class="modal" style="max-width: 500px;">
                <div class="mh">
                    <div class="mh-ico ico-g"><i class="fas fa-flag-checkered"></i></div>
                    <span>Завершение рейса: {{ selectedWaybill?.number }}</span>
                    <button class="mc" @click="completeMod = false"><i class="fas fa-times"></i></button>
                </div>
                <div class="mbody">
                    <div class="g g2 g2u mb3">
                        <div class="fgr">
                            <label class="fll">Одометр (возврат) *</label>
                            <input v-model.number="completeForm.odo_end" type="number" class="fin" />
                        </div>
                        <div class="fgr">
                            <label class="fll">Остаток топлива (л) *</label>
                            <input v-model.number="completeForm.fuel_end" type="number" class="fin" />
                        </div>
                    </div>
                    <div class="g g2 g2u mb3">
                        <div class="fgr">
                            <label class="fll">Сумма на бензин (руб)</label>
                            <input v-model.number="completeForm.fuel_cost" type="number" class="fin" placeholder="0" />
                        </div>
                        <div class="fgr">
                            <label class="fll">Тип топлива</label>
                            <select v-model="completeForm.fuel_type" class="fin">
                                <option value="ДТ">ДТ</option>
                                <option value="92">АИ-92</option>
                                <option value="95">АИ-95</option>
                            </select>
                        </div>
                    </div>
                    <div class="alert al-info mb3" style="font-size: 13px;">
                        <i class="fas fa-warehouse"></i> Если был привезен или отвезен груз со склада, укажите данные ниже для авто-списания.
                    </div>
                    <div class="fgr mb3">
                        <label class="fll">Вес привезенного/перевезенного груза (т)</label>
                        <input v-model.number="completeForm.cargo_weight" type="number" class="fin" placeholder="0 = без груза" />
                    </div>
                    <!-- Блок выбора склада показываем только если вес > 0 -->
                    <div class="g g2 g2u" v-if="completeForm.cargo_weight > 0">
                        <div class="fgr">
                            <label class="fll">Склад *</label>
                            <select v-model="completeForm.warehouse_id" class="fin">
                                <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
                            </select>
                        </div>
                        <div class="fgr">
                            <label class="fll">Товар *</label>
                            <select v-model="completeForm.product_id" class="fin">
                                <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="mfoot">
                    <button class="btn btn-ghost" @click="completeMod = false">Отмена</button>
                    <button class="btn btn-success" :disabled="saving" @click="submitComplete">
                        <i v-if="saving" class="fas fa-circle-notch fa-spin"></i>
                        <i v-else class="fas fa-check"></i> Завершить
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const mod = ref(false)
const completeMod = ref(false)
const saving = ref(false)
const search = ref('')

const stats = reactive({
    today_trips: 0,
    fuel_consumed: 0,
    total_distance: 0,
    total_weight: 0
})

const vehicles = ref([])
const waybills = ref([])
const warehouses = ref([])
const products = ref([])

const selectedWaybill = ref(null)

const form = reactive({
    vehicle_id: '',
    driver: '',
    route_from: '',
    route_to: '',
    odo_start: null,
    fuel_start: null
})

const completeForm = reactive({
    odo_end: null,
    fuel_end: null,
    fuel_cost: null,
    fuel_type: 'ДТ',
    cargo_weight: 0,
    warehouse_id: null,
    product_id: null
})

const filteredWaybills = computed(() => {
    if (!search.value) return waybills.value
    const s = search.value.toLowerCase()
    return waybills.value.filter(w =>
        (w.driver && w.driver.toLowerCase().includes(s)) ||
        (w.vehicle && w.vehicle.toLowerCase().includes(s)) ||
        (w.number && w.number.toLowerCase().includes(s))
    )
})

function formatDate(d) { 
    if (!d) return ''
    return new Date(d).toLocaleDateString('ru-RU') 
}

function statusLabel(s) {
    return { active: 'В рейсе', completed: 'Завершен', cancelled: 'Отменен' }[s] || s
}

function statusClass(s) {
    return { active: 'b-warn', completed: 'b-ok', cancelled: 'b-err' }[s] || ''
}

async function loadDictionaries() {
    try {
        const [vRes, wRes, pRes] = await Promise.all([
            api.get('/transport/vehicles'),
            api.get('/warehouse/list'),
            api.get('/warehouse/products')
        ])
        vehicles.value = vRes.data
        warehouses.value = wRes.data
        products.value = pRes.data
        
        if (warehouses.value.length) completeForm.warehouse_id = warehouses.value[0].id
        if (products.value.length) completeForm.product_id = products.value[0].id
    } catch (e) {
        console.error("Ошибка словарей", e)
    }
}

async function loadData() {
    try {
        const { data } = await api.get('/transport/waybills')
        waybills.value = data
        stats.today_trips = data.filter(w => w.status === 'active').length
    } catch (e) {
        app.toast('err', 'Ошибка', 'Не удалось загрузить путевые листы')
    }
}

async function exportXML() {
    try {
        app.toast('info', 'XML', 'Формирование XML-файла...')
        const response = await api.get('/transport/waybills/export_xml', { responseType: 'blob' })
        const downloadConfirm = confirm("Данные отправлены. Скачать XML-файл на локальное устройство?")
        if (downloadConfirm) {
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', 'waybills.xml')
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            app.toast('ok', 'Успех', 'Файл сохранен локально')
        } else {
            app.toast('ok', 'Успех', 'Данные отправлены')
        }
    } catch (e) {
        app.toast('err', 'Ошибка', 'Не удалось выгрузить XML')
    }
}

function openModal() {
    form.vehicle_id = vehicles.value[0]?.id || ''
    form.driver = ''
    form.route_from = ''
    form.route_to = ''
    form.odo_start = 0
    form.fuel_start = 0
    mod.value = true
}

async function save() {
    if (!form.vehicle_id || !form.driver || form.odo_start == null || form.fuel_start == null) {
        app.toast('warn', '⚠️ Ошибка', 'Заполните обязательные поля')
        return
    }
    saving.value = true
    try {
        const { data } = await api.post('/transport/waybills', form)
        waybills.value.unshift(data)
        stats.today_trips++
        app.toast('ok', '✅ Создано', `Путевой лист оформлен`)
        mod.value = false
    } catch (e) {
        app.toast('err', '❌ Ошибка', 'Не удалось создать путевой лист')
    } finally {
        saving.value = false
    }
}

function openCompleteModal(item) {
    selectedWaybill.value = item
    completeForm.odo_end = null
    completeForm.fuel_end = null
    completeForm.fuel_cost = null
    completeForm.fuel_type = 'ДТ'
    completeForm.cargo_weight = 0
    completeMod.value = true
}

async function submitComplete() {
    if (completeForm.odo_end == null || completeForm.fuel_end == null) {
        app.toast('warn', 'Внимание', 'Укажите одометр и остаток топлива')
        return
    }
    
    saving.value = true
    try {
        await api.post(`/transport/waybills/${selectedWaybill.value.id}/complete`, {
            odo_end: completeForm.odo_end,
            fuel_end: completeForm.fuel_end,
            fuel_cost: completeForm.fuel_cost || 0,
            fuel_type: completeForm.fuel_type,
            cargo_weight: completeForm.cargo_weight || 0,
            warehouse_id: completeForm.warehouse_id,
            product_id: completeForm.product_id
        })
        
        // Обновляем локально или перезагружаем список
        selectedWaybill.value.status = 'completed'
        if (completeForm.cargo_weight > 0) {
            selectedWaybill.value.cargo_weight = completeForm.cargo_weight
            stats.total_weight += completeForm.cargo_weight
        }
        stats.today_trips = Math.max(0, stats.today_trips - 1)
        
        app.toast('ok', '✅ Завершено', 'Рейс закрыт, данные склада и ГСМ обновлены')
        completeMod.value = false
    } catch (e) {
        app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Не удалось закрыть лист')
    } finally {
        saving.value = false
    }
}

onMounted(async () => {
    await loadDictionaries()
    await loadData()
})
</script>