<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">Документооборот</div>
        <div class="ps">Создание, просмотр и согласование документов</div>
      </div>
      <div class="ph-r" style="flex-wrap: wrap;">
        <button class="btn btn-ghost" @click="exportXML">
          <i class="fas fa-file-code"></i> XML путевых листов
        </button>
        <button class="btn btn-ghost" @click="exportEmploymentXML" style="color:#6366f1;border-color:#6366f1;">
          <i class="fas fa-file-export"></i> XML договоров
        </button>
        <button class="btn btn-primary" @click="dMod = true">
          <i class="fas fa-plus"></i> Создать документ
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tnav mb4">
      <div :class="['tab', filter === 'all' && 'act']" @click="filter = 'all'">Все</div>
      <div :class="['tab', filter === 'vacation' && 'act']" @click="filter = 'vacation'">Отпуска</div>
      <div :class="['tab', filter === 'travel' && 'act']" @click="filter = 'travel'">Командировки</div>
      <div :class="['tab', filter === 'waybill' && 'act']" @click="filter = 'waybill'">Путевые листы</div>
      <div :class="['tab', filter === 'employment' && 'act']" @click="filter = 'employment'">Договоры</div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading"><div class="spinner"></div> Загрузка...</div>

    <template v-else>
      <!-- Stats row -->
      <div class="g g4 mb4">
        <div class="kpi" v-for="s in docStats" :key="s.lbl">
          <div class="kico" :style="{ background: s.clr + '20', color: s.clr }"><i :class="s.icon"></i></div>
          <div>
            <div class="klb">{{ s.lbl }}</div>
            <div class="kv">{{ s.cnt }}</div>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="card">
        <div class="ch">
          <span class="ct">{{ filterLabel }}</span>
          <span class="fs12 tm">{{ filteredDocs.length }} записей</span>
        </div>
        <div class="tw responsive-table">
          <table>
            <thead>
              <tr>
                <th>Номер</th>
                <th>Тип</th>
                <th>Сотрудник</th>
                <th>Дата</th>
                <th>Составил</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredDocs.length === 0">
                <td colspan="7" class="tc tm" style="padding:24px;">Документов не найдено</td>
              </tr>
              <tr v-for="doc in filteredDocs" :key="doc.id">
                <td data-label="Номер" class="fw6 fs12">{{ doc.number }}</td>
                <td data-label="Тип">{{ typeLabel(doc.document_type) }}</td>
                <td data-label="Сотрудник">{{ doc.employee_name }}</td>
                <td data-label="Дата" class="tm fs12">{{ formatDate(doc.created_at) }}</td>
                <td data-label="Составил" class="tm">{{ doc.created_by_name }}</td>
                <td data-label="Статус"><span :class="['badge', statusClass(doc.status)]">{{ statusLabel(doc.status) }}</span></td>
                <td data-label="Действия">
                  <div class="flex g2u" style="width:100%;">
                    <button class="btn btn-ghost btn-sm" @click="viewDoc = doc">
                      <i class="fas fa-eye"></i>
                    </button>
                    <template v-if="auth.canApprove && doc.status === 'pending'">
                      <button class="btn btn-success btn-sm" @click="confirmApprove(doc)" :disabled="processing === doc.id">
                        <i class="fas fa-check"></i>
                      </button>
                      <button class="btn btn-danger btn-sm" @click="confirmReject(doc)" :disabled="processing === doc.id">
                        <i class="fas fa-times"></i>
                      </button>
                    </template>
                    <template v-if="doc.status === 'draft'">
                      <button class="btn btn-primary btn-sm" @click="updateStatus(doc, 'pending')" :disabled="processing === doc.id" title="Отправить на рассмотрение">
                        <i class="fas fa-paper-plane"></i>
                      </button>
                    </template>
                    <button v-if="auth.canApprove || doc.status === 'draft'" class="btn btn-ghost btn-sm text-danger" @click="confirmDelete(doc)" :disabled="processing === doc.id" title="Удалить">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ══ VIEW MODAL ══ -->
    <div v-if="viewDoc" class="ov" @click.self="viewDoc = null">
      <div class="modal">
        <div class="mh">
          <div class="mh-ico ico-b"><i class="fas fa-file-alt"></i></div>
          <span class="mt2">{{ typeLabel(viewDoc.document_type) }} · {{ viewDoc.number }}</span>
          <button class="mc" @click="viewDoc = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody">
          <div style="background:#f8fafc;border:1px solid var(--border);border-radius:10px;padding:18px;">
            <h3 style="margin-bottom:12px;">{{ typeLabel(viewDoc.document_type) }}</h3>
            <p class="mb2"><b>Номер документа:</b> {{ viewDoc.number }}</p>
            <p class="mb2"><b>Дата составления:</b> {{ formatDate(viewDoc.created_at) }}</p>
            <p class="mb2"><b>Сотрудник:</b> {{ viewDoc.employee_name }}</p>
            <p class="mb2"><b>Составил:</b> {{ viewDoc.created_by_name }}</p>
            <p class="mb2"><b>Статус:</b>
              <span :class="['badge', statusClass(viewDoc.status)]" style="margin-left:4px;">{{ statusLabel(viewDoc.status) }}</span>
            </p>
            <p class="mb2" v-if="viewDoc.status === 'rejected' && parseExtra(viewDoc.extra_data)?.rejection_reason" style="color:var(--err);">
              <b>Причина отказа:</b> {{ parseExtra(viewDoc.extra_data).rejection_reason }}
            </p>
            <hr style="margin:12px 0;border:none;border-top:1px solid var(--border);" />
            <p class="fs12 tm">Документ сформирован автоматически системой NortGru. Для получения версии .docx используйте кнопку «Печать».</p>
            <p class="mt2 fs12"><i class="fas fa-building tm"></i> <b>ООО «НОРД-ИСТ ГРУПП»</b>, г. Биробиджан / г. Хабаровск</p>
          </div>
        </div>
        <div class="mfoot">
          <button class="btn btn-ghost" @click="viewDoc = null">Закрыть</button>
          <button class="btn btn-primary" @click="printDoc(viewDoc)"><i class="fas fa-print"></i> Печать</button>
          <button class="btn btn-success" @click="downloadDoc(viewDoc)"><i class="fas fa-download"></i> Скачать .doc</button>
        </div>
      </div>
    </div>

    <!-- CONFIRM APPROVE MODAL -->
    <div v-if="cApproveDoc" class="ov" @click.self="cApproveDoc = null">
      <div class="modal">
        <div class="mh">
          <div class="mh-ico ico-b" style="background:#dcfce7;color:#22c55e;"><i class="fas fa-check"></i></div>
          <span class="mt2">Одобрение документа</span>
          <button class="mc" @click="cApproveDoc = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody tc">
          <p>Вы уверены, что хотите одобрить документ <b>{{ cApproveDoc.number }}</b>?</p>
        </div>
        <div class="mfoot" style="justify-content:flex-end;">
          <button class="btn btn-ghost" @click="cApproveDoc = null">Отмена</button>
          <button class="btn btn-success" @click="doApprove">Да, одобрить</button>
        </div>
      </div>
    </div>

    <!-- CONFIRM REJECT MODAL -->
    <div v-if="cRejectDoc" class="ov" @click.self="cRejectDoc = null">
      <div class="modal">
        <div class="mh">
          <div class="mh-ico" style="background:#fee2e2;color:#ef4444;"><i class="fas fa-times"></i></div>
          <span class="mt2">Отклонение документа</span>
          <button class="mc" @click="cRejectDoc = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody">
          <p class="mb2">Вы собираетесь отклонить документ <b>{{ cRejectDoc.number }}</b>.</p>
          <div class="fgr">
            <label class="fll">Причина отказа (обязательно)</label>
            <textarea v-model="rejectReason" class="fin" placeholder="Укажите, что нужно исправить..."></textarea>
          </div>
        </div>
        <div class="mfoot" style="justify-content:flex-end;">
          <button class="btn btn-ghost" @click="cRejectDoc = null">Отмена</button>
          <button class="btn btn-danger" @click="doReject" :disabled="!rejectReason.trim()">Отклонить</button>
        </div>
      </div>
    </div>

    <!-- CONFIRM DELETE MODAL -->
    <div v-if="cDeleteDoc" class="ov" @click.self="cDeleteDoc = null">
      <div class="modal">
        <div class="mh">
          <div class="mh-ico" style="background:#fee2e2;color:#ef4444;"><i class="fas fa-trash"></i></div>
          <span class="mt2">Удаление документа</span>
          <button class="mc" @click="cDeleteDoc = null"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody tc">
          <p>Вы уверены, что хотите удалить документ <b>{{ cDeleteDoc.number }}</b>?</p>
          <p class="tm fs12 mt2">Это действие нельзя будет отменить.</p>
        </div>
        <div class="mfoot" style="justify-content:flex-end;">
          <button class="btn btn-ghost" @click="cDeleteDoc = null">Отмена</button>
          <button class="btn btn-danger" @click="doDelete">Удалить навсегда</button>
        </div>
      </div>
    </div>
    <div v-if="dMod" class="ov" @click.self="dMod = false">
      <div class="modal">
        <div class="mh">
          <div class="mh-ico ico-b"><i class="fas fa-plus"></i></div>
          <span class="mt2">Создать документ</span>
          <button class="mc" @click="dMod = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody">
          <div class="fgr">
            <label class="fll">Тип документа</label>
            <select v-model="newType" class="fin">
              <option value="vacation">✈️ Заявка на отпуск</option>
              <option value="travel">🚁 Приказ на командировку</option>
              <option value="waybill">🚛 Путевой лист</option>
              <option value="employment">📄 Трудовой договор</option>
            </select>
          </div>
          <div class="fgr">
            <label class="fll">ФИО сотрудника *</label>
            <input v-model="newEmp" class="fin" type="text" placeholder="Иванов Иван Иванович" />
          </div>

          <!-- Vacation fields -->
          <template v-if="newType === 'vacation'">
            <div class="frow2">
              <div class="fgr"><label class="fll">Дата начала</label><input v-model="nd.s" class="fin" type="date" /></div>
              <div class="fgr"><label class="fll">Дата окончания</label><input v-model="nd.e" class="fin" type="date" /></div>
            </div>
            <div class="fgr"><label class="fll">Основание</label><textarea v-model="nd.reason" class="fin" placeholder="Ежегодный оплачиваемый отпуск..."></textarea></div>
          </template>

          <!-- Travel fields -->
          <template v-if="newType === 'travel'">
            <div class="fgr"><label class="fll">Место командировки</label><input v-model="nd.dest" class="fin" placeholder="г. Хабаровск" /></div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Дата начала</label><input v-model="nd.s" class="fin" type="date" /></div>
              <div class="fgr"><label class="fll">Дата окончания</label><input v-model="nd.e" class="fin" type="date" /></div>
            </div>
          </template>

          <!-- Waybill fields -->
          <template v-if="newType === 'waybill'">
            <div class="frow2">
              <div class="fgr"><label class="fll">Серия/Номер</label><input v-model="nd.series_number" class="fin" placeholder="АА12345" /></div>
              <div class="fgr"><label class="fll">Транспорт (Гос.номер)</label><input v-model="nd.vehicle" class="fin" placeholder="КАМАЗ-5320 А123ВС27" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Водитель</label><input v-model="nd.driver" class="fin" placeholder="Иванов И.И." /></div>
              <div class="fgr"><label class="fll">Период действия</label><input v-model="nd.period_info" class="fin" placeholder="с .. по .." /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Маршрут (откуда)</label><input v-model="nd.route_from" class="fin" placeholder="База 1" /></div>
              <div class="fgr"><label class="fll">Маршрут (куда)</label><input v-model="nd.route_to" class="fin" placeholder="Склад 2" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Время выезда</label><input v-model="nd.departure_time" class="fin" type="datetime-local" /></div>
              <div class="fgr"><label class="fll">Время возврата</label><input v-model="nd.arrival_time" class="fin" type="datetime-local" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Дистанция (км)</label><input v-model.number="nd.distance_km" class="fin" type="number" @input="calcFuelCost" /></div>
              <div class="fgr">
                <label class="fll">Марка топлива</label>
                <select v-model="nd.fuel_mark" class="fin">
                  <option value="ДТ">ДТ</option>
                  <option value="92">АИ-92</option>
                  <option value="95">АИ-95</option>
                </select>
              </div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Цена за литр (руб)</label><input v-model.number="nd.fuel_price" class="fin" type="number" @input="calcFuelCost" /></div>
              <div class="fgr"><label class="fll">Расход (л/км)</label><input v-model.number="nd.fuel_rate" class="fin" type="number" step="0.01" placeholder="напр., 0.15" @input="calcFuelCost" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Потрачено топлива (л)</label><input v-model.number="nd.fuel_issued" class="fin" type="number" @input="calcFuelCost" /></div>
              <div class="fgr"><label class="fll">Остаток/Сдано</label><input v-model.number="nd.fuel_handed_over" class="fin" type="number" /></div>
            </div>
            <div class="frow2">
              <div class="fgr" style="width:100%"><label class="fll">Сумма затрат (авторасчет)</label><input v-model="nd.fuel_cost" class="fin" type="number" readonly style="background:#e2e8f0;font-weight:bold;color:#333;" /></div>
            </div>
          </template>

          <!-- Employment fields -->
          <template v-if="newType === 'employment'">
            <!-- ─── ГЛАВНОЕ ─── -->
            <div class="form-section-title"><i class="fas fa-star"></i> Основные реквизиты</div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Организация</label><input v-model="nd.organization" class="fin" placeholder="ООО «НОРД-ИСТ ГРУПП»" /></div>
              <div class="fgr"><label class="fll">Номер договора</label><input v-model="nd.contract_number" class="fin" placeholder="ТД-001" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Вид договора</label>
                <select v-model="nd.contract_type" class="fin">
                  <option value="">— Выберите —</option>
                  <option value="1">1 — Бессрочный</option>
                  <option value="2">2 — Срочный</option>
                  <option value="3">3 — По совместительству</option>
                </select>
              </div>
              <div class="fgr"><label class="fll">Дата приема</label><input v-model="nd.hire_date" class="fin" type="date" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Подразделение</label><input v-model="nd.department" class="fin" placeholder="Транспортный цех" /></div>
              <div class="fgr"><label class="fll">Территория</label><input v-model="nd.territory" class="fin" placeholder="г. Биробиджан" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Должность по штату</label><input v-model="nd.position_staff" class="fin" placeholder="Водитель категории B" /></div>
              <div class="fgr"><label class="fll">Должность</label><input v-model="nd.job_title" class="fin" placeholder="Водитель" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">График работы</label><input v-model="nd.work_schedule" class="fin" placeholder="5/2, 8 часов" /></div>
              <div class="fgr"><label class="fll">Вид занятости</label><input v-model="nd.employment_type" class="fin" placeholder="Основное место работы" /></div>
            </div>

            <!-- ─── ВТОРОСТЕПЕННОЕ ─── -->
            <div class="form-section-title" style="margin-top:14px;"><i class="fas fa-list"></i> Дополнительные сведения</div>
            <div class="frow2">
              <div class="fgr">
                <label class="fll">Наименование документа</label>
                <input v-model="nd.doc_name" class="fin" placeholder="Трудовой договор" />
              </div>
              <div class="fgr">
                <label class="fll">Трудовая фиксация</label>
                <input v-model="nd.work_fixation" class="fin" placeholder="Электронная ТК" />
              </div>
            </div>
            <div class="frow2">
              <div class="fgr" style="display:flex;align-items:center;gap:10px;">
                <input type="checkbox" v-model="nd.reflect_in_workbook" id="chk_reflect" style="width:18px;height:18px;accent-color:#6366f1;" />
                <label for="chk_reflect" class="fll" style="margin-bottom:0;">Отразить в трудовой книжке</label>
              </div>
              <div class="fgr" style="display:flex;align-items:center;gap:10px;">
                <input type="checkbox" v-model="nd.start_of_work" id="chk_start" style="width:18px;height:18px;accent-color:#6366f1;" />
                <label for="chk_start" class="fll" style="margin-bottom:0;">Начало трудовой деятельности</label>
              </div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Способ ведения</label><input v-model="nd.management_method" class="fin" placeholder="Электронный" /></div>
              <div class="fgr"><label class="fll">Дата заявления о выборе способа</label><input v-model="nd.method_choice_date" class="fin" type="date" /></div>
            </div>
            <div class="form-section-title" style="margin-top:8px;">Второй документ</div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Наименование втор. документа</label><input v-model="nd.second_doc_name" class="fin" placeholder="Паспорт" /></div>
              <div class="fgr"><label class="fll">Дата втор. документа</label><input v-model="nd.second_doc_date" class="fin" type="date" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">Серия втор. документа</label><input v-model="nd.second_doc_series" class="fin" placeholder="27 11" /></div>
              <div class="fgr"><label class="fll">Номер втор. документа</label><input v-model="nd.second_doc_number" class="fin" placeholder="123456" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">ПКУ</label><input v-model="nd.pku" class="fin" placeholder="Профессиональный квалиф. уровень" /></div>
              <div class="fgr"><label class="fll">Разряд</label><input v-model="nd.grade" class="fin" placeholder="4" /></div>
            </div>
            <div class="frow2">
              <div class="fgr"><label class="fll">ФОТ (руб.)</label><input v-model.number="nd.fot" class="fin" type="number" placeholder="50000" /></div>
              <div class="fgr"><label class="fll">Ответственный</label><input v-model="nd.responsible" class="fin" placeholder="Иванова А.П." /></div>
            </div>
          </template>
        </div>
        <div class="mfoot">
          <button class="btn btn-ghost" @click="dMod = false">Отмена</button>
          <button class="btn btn-primary" :disabled="saving" @click="createDoc">
            <i v-if="saving" class="fas fa-circle-notch fa-spin"></i>
            <i v-else class="fas fa-plus"></i>
            Создать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const auth = useAuthStore()
const app  = useAppStore()

const loading    = ref(true)
const saving     = ref(false)
const processing = ref(null)
const docs       = ref([])
const filter     = ref('all')
const viewDoc    = ref(null)
const dMod       = ref(false)
const cApproveDoc = ref(null)
const cRejectDoc  = ref(null)
const cDeleteDoc  = ref(null)
const rejectReason = ref('')
const newType    = ref('vacation')
const newEmp     = ref('')
const nd         = reactive({ 
  s:'', e:'', reason:'', dest:'', dt:'',
  // Waybill fields
  series_number: '', vehicle: '', driver: '', period_info: '', route_from: '', route_to: '', departure_time: '', arrival_time: '', distance_km: '', fuel_mark: 'ДТ', fuel_price: '', fuel_cost: '', fuel_issued: '', fuel_handed_over: '', fuel_rate: '',
  // Employment — Главное
  organization: '', contract_number: '', contract_type: '', hire_date: '',
  department: '', territory: '', position_staff: '', job_title: '',
  work_schedule: '', employment_type: '',
  // Employment — Второстепенное
  reflect_in_workbook: false, work_fixation: '', doc_name: '',
  start_of_work: false, management_method: '', method_choice_date: '',
  second_doc_name: '', second_doc_date: '', second_doc_series: '', second_doc_number: '',
  pku: '', grade: '', fot: '', responsible: '',
  // legacy
  tabel_number: '', phone: '', email: ''
})

const typeLabels = { vacation:'Заявка на отпуск', travel:'Командировка', waybill:'Путевой лист', employment:'Трудовой договор' }
const filterLabelMap = { all:'Все документы', vacation:'Заявки на отпуск', travel:'Командировки', waybill:'Путевые листы', employment:'Трудовые договоры' }
function typeLabel(t) { return typeLabels[t] || t }

function calcFuelCost() {
  const liters = parseFloat(nd.fuel_issued) || 0
  const price = parseFloat(nd.fuel_price) || 0
  const distance = parseFloat(nd.distance_km) || 0
  // Если пользователь хотел расчет от расстояния:
  // Мы можем сделать (distance * price), но это странно.
  // Пока считаем классически: Выдано (Литры) * Цена
  // Но если он ввел "Выдано топлива" как норму на км, то distance * liters * price
  // Для надежности считаем Цена * Выдано литров.
  nd.fuel_cost = Number((liters * price).toFixed(2))
}

function statusLabel(s) { return { draft:'Черновик', pending:'На рассмотрении', approved:'Одобрено', rejected:'Отклонено' }[s] || s }
function statusClass(s) { return { draft:'b-sec', pending:'b-warn', approved:'b-ok', rejected:'b-err' }[s] || 'b-sec' }
function formatDate(dt) { return dt ? new Date(dt).toLocaleDateString('ru-RU') : '' }

const filterLabel   = computed(() => filterLabelMap[filter.value] || 'Документы')
const filteredDocs  = computed(() => filter.value === 'all' ? docs.value : docs.value.filter(d => d.document_type === filter.value))

const docStats = computed(() => [
  { lbl:'Одобрено',        cnt: docs.value.filter(d => d.status === 'approved').length, clr:'#22c55e', icon:'fas fa-check-circle' },
  { lbl:'На рассмотрении', cnt: docs.value.filter(d => d.status === 'pending').length,  clr:'#f59e0b', icon:'fas fa-clock' },
  { lbl:'Черновики',       cnt: docs.value.filter(d => d.status === 'draft').length,    clr:'#94a3b8', icon:'fas fa-file' },
  { lbl:'Отклонено',       cnt: docs.value.filter(d => d.status === 'rejected').length, clr:'#ef4444', icon:'fas fa-times-circle' },
])

async function loadDocs() {
  try {
    const { data } = await api.get('/documents/')
    docs.value = data
  } catch { app.toast('err', '❌ Ошибка', 'Не удалось загрузить документы') }
  finally { loading.value = false }
}

async function exportXML() {
  try {
    app.toast('info', 'XML', 'Формирование XML-файла...')
    const response = await api.get('/documents/export_xml', { responseType: 'blob' })
    const downloadConfirm = confirm("Данные путевых листов отправлены на Google Диск. Скачать XML-файл на локальное устройство?")
    if (downloadConfirm) {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'documents_waybills.xml')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      app.toast('ok', 'Успешно', 'Файл сохранен локально')
    } else {
      app.toast('ok', 'Успешно', 'Файл сохранен в облако Google Диска')
    }
  } catch (e) {
    app.toast('err', '❌ Ошибка', 'Не удалось выгрузить XML')
  }
}

async function exportEmploymentXML() {
  try {
    app.toast('info', 'XML', 'Формирование XML трудовых договоров...')
    const response = await api.get('/documents/export_xml_employment', { responseType: 'blob' })
    const downloadConfirm = confirm("Данные трудовых договоров отправлены на Google Диск. Скачать XML-файл на локальное устройство?")
    if (downloadConfirm) {
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/xml' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'trudovye_dogovory.xml')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      app.toast('ok', '✅ Готово', 'Файл сохранен локально')
    } else {
      app.toast('ok', '✅ Готово', 'Файл сохранен в облако Google Диска')
    }
  } catch (e) {
    app.toast('err', '❌ Ошибка', 'Не удалось выгрузить XML договоров')
  }
}

function parseExtra(ext) {
  try { return ext ? JSON.parse(ext) : {} } catch { return {} }
}

function confirmApprove(doc) { cApproveDoc.value = doc }
function confirmReject(doc) { cRejectDoc.value = doc; rejectReason.value = '' }
function confirmDelete(doc) { cDeleteDoc.value = doc }

async function doApprove() {
  if (!cApproveDoc.value) return
  await updateStatus(cApproveDoc.value, 'approved')
  cApproveDoc.value = null
}

async function doReject() {
  if (!cRejectDoc.value) return
  await updateStatus(cRejectDoc.value, 'rejected', rejectReason.value)
  cRejectDoc.value = null
}

async function doDelete() {
  if (!cDeleteDoc.value) return
  const doc = cDeleteDoc.value
  processing.value = doc.id
  try {
    await api.delete(`/documents/${doc.id}`)
    docs.value = docs.value.filter(d => d.id !== doc.id)
    app.toast('ok', '🗑️ Удалено', `Документ ${doc.number} успешно удален`)
  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Не удалось удалить документ')
  } finally {
    processing.value = null
    cDeleteDoc.value = null
  }
}

async function updateStatus(doc, status, reason = null) {
  processing.value = doc.id
  try {
    const payload = { status }
    if (reason) payload.reason = reason
    const { data } = await api.patch(`/documents/${doc.id}`, payload)
    const idx = docs.value.findIndex(d => d.id === doc.id)
    if (idx !== -1) docs.value[idx] = data
    app.toast('ok', status === 'approved' ? '✅ Одобрено' : (status === 'rejected' ? '❌ Отклонено' : '📋 Статус обновлён'), `Документ ${doc.number} — ${statusLabel(status)}`)
  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Ошибка сервера')
  } finally { processing.value = null }
}

async function createDoc() {
  if (!newEmp.value.trim()) { app.toast('warn', '⚠️ Ошибка', 'Введите ФИО сотрудника'); return }
  saving.value = true
  try {
    const { data } = await api.post('/documents/', {
      document_type: newType.value,
      employee_name: newEmp.value,
      extra_data: JSON.stringify(nd)
    })
    docs.value.unshift(data)
    dMod.value = false
    newEmp.value = ''
    Object.keys(nd).forEach(k => (nd[k] = ''))
    app.toast('ok', '✅ Создан', `${typeLabel(newType.value)} создана (черновик)`)
  } catch (e) {
    app.toast('err', '❌ Ошибка', e.response?.data?.detail || 'Ошибка сервера')
  } finally { saving.value = false }
}

function printDoc(doc) {
  app.toast('info', '🖨️ Печать', `Документ ${doc.number} отправлен на печать`)
  viewDoc.value = null
}

async function downloadDoc(doc) {
  try {
    app.toast('info', '⬇️ Скачивание', 'Генерация документа. Пожалуйста, подождите...')
    const response = await api.get(`/documents/${doc.id}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${doc.number}.docx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    app.toast('err', '❌ Ошибка', 'Не удалось скачать документ')
  }
}

onMounted(loadDocs)
</script>
