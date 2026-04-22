<template>
  <div>
    <div class="ph">
      <div class="ph-l">
        <div class="pt">AI Помощник (MCP)</div>
        <div class="ps">Корпоративный ассистент с доступом к инструментам системы NortGru</div>
      </div>
    </div>

    <div class="g g21">
      <!-- Chat Interface -->
      <div class="card" style="display: flex; flex-direction: column;">
        <div class="ch"><span class="ct">Диалог с ассистентом</span></div>
        <div class="cb chat-scroll" ref="chatScroll">
          <div v-for="(m, idx) in messages" :key="idx" :class="['chat-row', m.role === 'user' ? 'row-u' : 'row-ai']">
            
            <div v-if="m.role === 'ai'" class="chat-av av-ai">
              <i class="fas fa-robot"></i>
            </div>

            <div :class="['chat-msg', m.role === 'user' ? 'msg-u' : 'msg-ai']">
              <div v-if="m.isLoading" class="msg-loading">
                <i class="fas fa-circle-notch fa-spin"></i> Обработка запроса...
              </div>
              <div v-else class="msg-text">{{ m.text }}</div>
              
              <div v-if="m.toolCall" class="msg-tool">
                <i class="fas fa-cog fa-spin"></i> Вызов инструмента: <code>{{ m.toolCall }}</code>
              </div>
            </div>

            <div v-if="m.role === 'user'" class="chat-av av-u">
              {{ auth.initials }}
            </div>
          </div>
        </div>
        <div class="cft chat-input-area">
          <input 
            v-model="inputText" 
            class="fin" 
            placeholder="Задайте вопрос или выберите инструмент..." 
            @keyup.enter="sendUserMessage"
            :disabled="loading"
          />
          <button class="btn btn-primary" @click="sendUserMessage" :disabled="!inputText.trim() || loading">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>

      <!-- Tools Panel -->
      <div class="card">
        <div class="ch">
          <span class="ct">Доступные инструменты (Tools)</span>
          <span class="fs12 tm">Интеграция по MCP</span>
        </div>
        <div class="cb" style="display: flex; flex-direction: column; gap: 8px;">
          
          <button class="btn btn-ghost tool-btn" :disabled="loading" @click="callTool('get_warehouse_summary', 'Сводка по складу торфа')">
            <div class="tx-l">
              <div class="tool-title"><i class="fas fa-warehouse tb" style="width: 20px;"></i> Сводка по складу торфа</div>
              <div class="tool-desc">get_warehouse_summary</div>
            </div>
            <i class="fas fa-chevron-right tm fs12"></i>
          </button>

          <button class="btn btn-ghost tool-btn" :disabled="loading" @click="callTool('analyze_waybills', 'Анализ путевых листов за сегодня')">
            <div class="tx-l">
              <div class="tool-title"><i class="fas fa-truck-moving tg" style="width: 20px;"></i> Анализ путевых листов</div>
              <div class="tool-desc">analyze_waybills</div>
            </div>
            <i class="fas fa-chevron-right tm fs12"></i>
          </button>

          <button class="btn btn-ghost tool-btn" :disabled="loading" @click="callTool('generate_report', 'Сгенерировать отчет для руководства')">
            <div class="tx-l">
              <div class="tool-title"><i class="fas fa-file-pdf tr2" style="width: 20px;"></i> Сгенерировать отчет</div>
              <div class="tool-desc">generate_report</div>
            </div>
            <i class="fas fa-chevron-right tm fs12"></i>
          </button>
          
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const chatScroll = ref(null)
const inputText = ref('')
const loading = ref(false)

const messages = ref([
  { 
    role: 'ai', 
    text: 'Здравствуйте! Я ваш корпоративный AI-ассистент NortGru. Чем могу помочь? Я могу анализировать данные складов, транспорта и генерировать отчеты.',
    isLoading: false
  }
])

function scrollToBottom() {
  nextTick(() => {
    if (chatScroll.value) {
      chatScroll.value.scrollTop = chatScroll.value.scrollHeight
    }
  })
}

function sendUserMessage() {
  const text = inputText.value.trim()
  if (!text) return

  // Добавляем сообщение пользователя
  messages.value.push({ role: 'user', text: text })
  inputText.value = ''
  scrollToBottom()

  // Имитируем ответ AI
  simulateAIResponse('Я пока не подключен к реальному бэкенду LLM, но вы можете использовать инструменты справа для тестирования интеграции с контекстом NortGru!')
}

function simulateAIResponse(text) {
  const aiMsgIdx = messages.value.push({ role: 'ai', text: '', isLoading: true }) - 1
  loading.value = true
  scrollToBottom()
  
  setTimeout(() => {
    messages.value[aiMsgIdx].isLoading = false
    messages.value[aiMsgIdx].text = text
    loading.value = false
    scrollToBottom()
  }, 1000)
}

function callTool(toolId, toolName) {
  // Сообщение от пользователя с командой
  messages.value.push({ role: 'user', text: `Вызови инструмент: ${toolName}` })
  scrollToBottom()
  
  // Создаем сообщение процесса от AI
  const aiMsgIdx = messages.value.push({
    role: 'ai',
    text: '',
    isLoading: true,
    toolCall: toolId
  }) - 1

  loading.value = true
  scrollToBottom()

  // Имитируем задержку выполнения инструмента
  setTimeout(() => {
    let resultText = ''
    if (toolId === 'get_warehouse_summary') {
      resultText = 'Выполнен вызов `get_warehouse_summary`.\n\nТекущий остаток торфа на главном складе: 1450 т. Склад заполнен на 72%. Критических отклонений не выявлено.'
    } else if (toolId === 'analyze_waybills') {
      resultText = 'Выполнен вызов `analyze_waybills`.\n\nСегодня активно 12 путевых листов. Автомобиль КамАЗ-65115 (А123РХ 27) завершил рейс с перерасходом топлива на 2 литра. Остальные транспорты работают в норме.'
    } else if (toolId === 'generate_report') {
      resultText = 'Выполнен вызов `generate_report`.\n\nОтчет по добыче и логистике за текущий месяц успешно сгенерирован и отправлен на email director@nortgru.ru.'
    }

    // Обновляем сообщение
    messages.value[aiMsgIdx].isLoading = false
    messages.value[aiMsgIdx].toolCall = null
    messages.value[aiMsgIdx].text = resultText
    loading.value = false
    scrollToBottom()

  }, 1500)
}
</script>

<style scoped>
.chat-scroll {
  height: 500px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #f8fafc;
  padding: 20px;
}

.chat-input-area {
  display: flex;
  gap: 10px;
  background: #fff;
  border-radius: 0 0 var(--r) var(--r);
}

.chat-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  width: 100%;
}

.row-u {
  justify-content: flex-end;
}

.row-ai {
  justify-content: flex-start;
}

.chat-av {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.av-u {
  background: var(--primary);
  color: #fff;
}

.av-ai {
  background: linear-gradient(135deg, #1e3a5f, #0f172a);
  color: #fff;
}

.chat-msg {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 80%;
  white-space: pre-wrap;
  position: relative;
  box-shadow: var(--sh);
}

.msg-u {
  background: var(--primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg-ai {
  background: #fff;
  color: var(--text);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.msg-tool {
  font-family: monospace;
  font-size: 11px;
  background: #f1f5f9;
  color: var(--muted);
  padding: 6px 10px;
  border-radius: 6px;
  margin-top: 8px;
}

.tool-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid var(--border);
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #fff;
  border-color: var(--primary);
  box-shadow: var(--sh);
  transform: translateY(-1px);
}

.tx-l {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text);
}

.tool-desc {
  font-size: 11px;
  color: var(--muted);
  font-family: monospace;
}
</style>
