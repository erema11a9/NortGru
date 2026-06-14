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
      <div class="card premium-chat-card" style="display: flex; flex-direction: column;">
        <div class="ch chat-header-gradient">
          <span class="ct text-white"><i class="fas fa-comments"></i> Диалог с ассистентом</span>
        </div>
        
        <div class="cb chat-scroll" ref="chatScroll">
          <div v-for="(m, idx) in messages" :key="idx" :class="['chat-row', m.role === 'user' ? 'row-u' : 'row-ai']">
            
            <div v-if="m.role === 'ai'" class="chat-av av-ai">
              <i class="fas fa-robot"></i>
            </div>

            <div :class="['chat-msg-wrapper', m.role === 'user' ? 'wrapper-u' : 'wrapper-ai']">
              <div :class="['chat-msg', m.role === 'user' ? 'msg-u' : 'msg-ai']">
                <!-- Message Loading State -->
                <div v-if="m.isLoading" class="msg-loading">
                  <span class="spinner-inline"><i class="fas fa-circle-notch fa-spin"></i></span> 
                  Обработка запроса...
                </div>
                
                <!-- Message Content -->
                <div v-else class="msg-text markdown-body" v-html="renderMarkdown(m.text)"></div>
              </div>
              
              <!-- Tool Executed Log -->
              <div v-if="m.toolCall" class="msg-tool-log">
                <i class="fas fa-cog fa-spin"></i> Использован инструмент: <code>{{ m.toolCall }}</code>
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
            class="fin chat-text-input" 
            placeholder="Спросите про склады, транспорт или интеграцию с 1С..." 
            @keyup.enter="sendUserMessage"
            :disabled="loading"
          />
          <button class="btn btn-primary btn-chat-send" @click="sendUserMessage" :disabled="!inputText.trim() || loading">
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>

      <!-- Tools Panel -->
      <div class="card right-tools-card">
        <div class="ch">
          <span class="ct">Быстрые действия (MCP)</span>
        </div>
        <div class="cb" style="display: flex; flex-direction: column; gap: 12px;">
          
          <button class="btn btn-ghost tool-widget-btn" :disabled="loading" @click="callTool('get_warehouse_summary', 'Сводка по складу торфа')">
            <div class="tool-widget-icon icon-green">
              <i class="fas fa-warehouse"></i>
            </div>
            <div class="tool-widget-content">
              <div class="tool-widget-title">Сводка по складам</div>
              <div class="tool-widget-desc">Остатки торфа в Биробиджанском и Хабаровском филиалах</div>
            </div>
            <i class="fas fa-chevron-right arrow-indicator"></i>
          </button>

          <button class="btn btn-ghost tool-widget-btn" :disabled="loading" @click="callTool('analyze_waybills', 'Анализ путевых листов за сегодня')">
            <div class="tool-widget-icon icon-blue">
              <i class="fas fa-truck-moving"></i>
            </div>
            <div class="tool-widget-content">
              <div class="tool-widget-title">Транспорт и ПЛ</div>
              <div class="tool-widget-desc">Активные путевые листы водителей</div>
            </div>
            <i class="fas fa-chevron-right arrow-indicator"></i>
          </button>

          <button class="btn btn-ghost tool-widget-btn" :disabled="loading" @click="callTool('generate_report', 'Проверить подключение к 1С и показать список доступных объектов')">
            <div class="tool-widget-icon icon-yellow">
              <i class="fas fa-plug"></i>
            </div>
            <div class="tool-widget-content">
              <div class="tool-widget-title">Интеграция 1С</div>
              <div class="tool-widget-desc">Проверить MCP-соединение с 1С</div>
            </div>
            <i class="fas fa-chevron-right arrow-indicator"></i>
          </button>
          
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const auth = useAuthStore()
const chatScroll = ref(null)
const inputText = ref('')
const loading = ref(false)
const offlineMode = ref(false)

const messages = ref([
  { 
    role: 'ai', 
    text: 'Здравствуйте! Я ваш корпоративный AI-ассистент NortGru. Чем могу помочь? Я имею прямой доступ к складам компании, информации о транспорте и справочным материалам.',
    isLoading: false,
    offline: false
  }
])

function scrollToBottom() {
  nextTick(() => {
    if (chatScroll.value) {
      chatScroll.value.scrollTop = chatScroll.value.scrollHeight
    }
  })
}

async function sendUserMessage() {
  const text = inputText.value.trim()
  if (!text) return

  // Добавляем сообщение пользователя
  messages.value.push({ role: 'user', text: text })
  inputText.value = ''
  scrollToBottom()

  // Включаем статус загрузки
  loading.value = true
  const aiMsgIdx = messages.value.push({ role: 'ai', text: '', isLoading: true }) - 1
  scrollToBottom()

  try {
    // Подготавливаем историю сообщений для бэкенда
    const historyForBackend = messages.value
      .filter(m => !m.isLoading && m.text)
      .map(m => ({
        role: m.role === 'ai' ? 'assistant' : 'user',
        content: m.text
      }))

    const response = await api.post('/mcp/chat', {
      messages: historyForBackend
    }, {
      timeout: 15000
    })

    // Записываем ответ от бэкенда
    messages.value[aiMsgIdx].isLoading = false
    messages.value[aiMsgIdx].text = response.data.content
    messages.value[aiMsgIdx].offline = response.data.offline || false
    
    // Обновляем режим работы ассистента
    offlineMode.value = response.data.offline || false
    
    // Отображаем вызванные инструменты
    if (response.data.tools_called && response.data.tools_called.length > 0) {
      messages.value[aiMsgIdx].toolCall = response.data.tools_called.join(', ')
    }
  } catch (err) {
    messages.value[aiMsgIdx].isLoading = false
    messages.value[aiMsgIdx].text = 'Ошибка соединения с сервером бэкенда. Убедитесь, что бэкенд запущен.'
    console.error(err)
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function callTool(toolId, toolName) {
  if (toolId === 'get_warehouse_summary') {
    inputText.value = 'Покажи сводку по остаткам на складах'
  } else if (toolId === 'analyze_waybills') {
    inputText.value = 'Покажи список активных путевых листов и машин'
  } else if (toolId === 'generate_report') {
    inputText.value = 'Проверь подключение к 1С'
  }
  sendUserMessage()
}

// Lightweight Markdown renderer
function renderMarkdown(text) {
  if (!text) return '';
  
  // Экранируем HTML для безопасности
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
    
  // Заголовки (###, ##, #)
  html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
  
  // Жирный текст (**text**)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Списки с * или -
  html = html.replace(/^\s*[\*\-]\s+(.+)$/gm, '<li>$1</li>');
  
  // Оборачиваем стоящие подряд <li> в <ul>
  let inList = false;
  const lines = html.split('\n');
  const processedLines = [];
  
  for (let line of lines) {
    const trimmed = line.trim();
    const isLi = trimmed.startsWith('<li>') && trimmed.endsWith('</li>');
    if (isLi) {
      if (!inList) {
        processedLines.push('<ul>');
        inList = true;
      }
      processedLines.push(line);
    } else {
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      if (trimmed === '') {
        processedLines.push('<br>');
      } else if (trimmed.startsWith('<h') || trimmed.startsWith('</h')) {
        processedLines.push(line);
      } else {
        processedLines.push(`<p>${line}</p>`);
      }
    }
  }
  if (inList) {
    processedLines.push('</ul>');
  }
  
  return processedLines.join('\n');
}
</script>

<style scoped>
.premium-chat-card {
  height: 600px;
}

.chat-header-gradient {
  background: linear-gradient(135deg, #1e293b, #0f172a);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-white {
  color: #fff;
}

.chat-scroll {
  flex: 1;
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
  padding: 12px 16px;
  border-radius: 0 0 var(--r) var(--r);
  border-top: 1px solid var(--border);
}

.chat-text-input {
  height: 40px;
  font-size: 13px;
}

.btn-chat-send {
  width: 40px;
  height: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.chat-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
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
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: var(--sh);
}

.av-u {
  background: var(--primary);
  color: #fff;
  margin-top: 2px;
}

.av-ai {
  background: linear-gradient(135deg, #1e3a5f, #0f172a);
  color: #fff;
  margin-top: 2px;
}

.chat-msg-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  gap: 4px;
}

.wrapper-u {
  align-items: flex-end;
}

.wrapper-ai {
  align-items: flex-start;
}

.chat-msg {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.5;
  box-shadow: var(--sh);
}

.msg-u {
  background: var(--primary);
  color: #fff;
  border-top-right-radius: 4px;
}

.msg-ai {
  background: #fff;
  color: var(--text);
  border: 1px solid var(--border);
  border-top-left-radius: 4px;
}

.spinner-inline {
  margin-right: 6px;
  color: var(--primary);
}

.msg-tool-log {
  font-family: monospace;
  font-size: 10px;
  background: rgba(37, 99, 235, 0.05);
  border: 1px solid rgba(37, 99, 235, 0.1);
  color: var(--primary);
  padding: 4px 8px;
  border-radius: 6px;
  margin-top: 2px;
}

/* Tool Widgets Styling */
.right-tools-card {
  display: flex;
  flex-direction: column;
}

.tool-widget-btn {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 10px;
  text-align: left;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.tool-widget-btn:hover {
  background: #fff;
  border-color: var(--primary);
  box-shadow: var(--sh-md);
  transform: translateY(-2px);
}

.tool-widget-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  margin-right: 12px;
  flex-shrink: 0;
}

.icon-green { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.icon-blue { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
.icon-yellow { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }

.tool-widget-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.tool-widget-title {
  font-weight: 700;
  font-size: 13px;
  color: var(--text);
}

.tool-widget-desc {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.arrow-indicator {
  font-size: 11px;
  color: var(--muted);
  transition: transform 0.2s;
}

.tool-widget-btn:hover .arrow-indicator {
  transform: translateX(3px);
  color: var(--primary);
}

/* Markdown styling inside Chat row */
.markdown-body :deep(h1), 
.markdown-body :deep(h2), 
.markdown-body :deep(h3) {
  margin: 10px 0 6px 0;
  font-weight: 700;
  line-height: 1.3;
}
.markdown-body :deep(h1) { font-size: 1.3em; }
.markdown-body :deep(h2) { font-size: 1.15em; }
.markdown-body :deep(h3) { font-size: 1.05em; }

.markdown-body :deep(p) {
  margin: 0 0 6px 0;
}
.markdown-body :deep(p):last-child {
  margin-bottom: 0;
}

.markdown-body :deep(ul) {
  margin: 4px 0;
  padding-left: 20px;
  list-style-type: disc;
}

.markdown-body :deep(li) {
  margin-bottom: 3px;
}

.markdown-body :deep(strong) {
  font-weight: 700;
}

.markdown-body :deep(br) {
  content: "";
  display: block;
  margin-top: 4px;
}

.markdown-body :deep(code) {
  font-family: monospace;
  background: #f1f5f9;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 11px;
}
</style>
