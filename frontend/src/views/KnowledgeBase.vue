<template>
  <div>
    <!-- Page Header -->
    <div class="ph">
      <div class="ph-l">
        <div class="pt">База знаний компании</div>
        <div class="ps">Корпоративные регламенты, рабочие инструкции и справочные материалы</div>
      </div>
      <div class="ph-r" v-if="canWrite">
        <button class="btn btn-primary btn-add" @click="openCreateModal">
          <i class="fas fa-plus"></i> Добавить статью
        </button>
      </div>
    </div>

    <!-- Search and Filters Section -->
    <div class="kb-filters-card card mb4">
      <div class="cb search-filter-box">
        <div class="search-input-wrapper">
          <i class="fas fa-search search-icon"></i>
          <input 
            v-model="searchQuery" 
            class="fin search-input" 
            placeholder="Поиск по названию или тексту статьи..." 
            @input="filterArticles"
          />
          <button v-if="searchQuery" class="clear-search-btn" @click="clearSearch">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="category-tabs mt3">
          <span 
            v-for="cat in categories" 
            :key="cat" 
            :class="['category-tab', selectedCategory === cat && 'active']"
            @click="selectCategory(cat)"
          >
            {{ cat || 'Все категории' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <div>Загрузка корпоративной базы знаний...</div>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredArticles.length === 0" class="empty-state card">
      <div class="empty-icon"><i class="fas fa-book-open"></i></div>
      <h3>Ничего не найдено</h3>
      <p>По вашему запросу не найдено ни одной статьи. Попробуйте изменить фильтр или запрос.</p>
    </div>

    <!-- Articles Grid -->
    <div v-else class="articles-grid">
      <div 
        v-for="art in filteredArticles" 
        :key="art.id" 
        class="article-card"
        @click="openArticleModal(art)"
      >
        <div class="article-category-badge" :style="{ backgroundColor: getCategoryColor(art.category) }">
          {{ art.category }}
        </div>
        <h3 class="article-title">{{ art.title }}</h3>
        <p class="article-snippet">{{ getSnippet(art.content) }}</p>
        <div class="article-footer">
          <span class="article-date"><i class="far fa-calendar-alt"></i> {{ formatDate(art.updated_at) }}</span>
          <div class="article-actions" v-if="canWrite" @click.stop>
            <button class="btn-icon btn-edit" title="Редактировать" @click="openEditModal(art)">
              <i class="fas fa-pencil-alt"></i>
            </button>
            <button class="btn-icon btn-delete" title="Удалить" @click="deleteArticle(art)">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Article Detail Modal -->
    <div v-if="detailModalOpen" class="ov" @click.self="detailModalOpen = false">
      <div class="modal kb-detail-modal">
        <div class="mh">
          <div class="mh-ico ico-b" :style="{ backgroundColor: getCategoryColor(selectedArticle.category) + '1c', color: getCategoryColor(selectedArticle.category) }">
            <i class="fas fa-book-reader"></i>
          </div>
          <div class="mt2 header-text-box">
            <span class="detail-category" :style="{ color: getCategoryColor(selectedArticle.category) }">{{ selectedArticle.category }}</span>
            <h3>{{ selectedArticle.title }}</h3>
          </div>
          <button class="mc" @click="detailModalOpen = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody detail-content markdown-body" v-html="renderMarkdown(selectedArticle.content)"></div>
        <div class="mfoot">
          <button class="btn btn-ghost" @click="detailModalOpen = false">Закрыть</button>
          <button v-if="canWrite" class="btn btn-primary" @click="editFromDetail">Редактировать</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Article Modal -->
    <div v-if="formModalOpen" class="ov" @click.self="formModalOpen = false">
      <div class="modal kb-form-modal">
        <div class="mh">
          <div class="mh-ico ico-p">
            <i class="fas fa-edit"></i>
          </div>
          <span class="mt2">{{ isEditMode ? 'Редактировать статью' : 'Создать новую статью' }}</span>
          <button class="mc" @click="formModalOpen = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="mbody">
          <div class="fgr">
            <label class="fll">Заголовок статьи *</label>
            <input v-model="form.title" class="fin" placeholder="Например: Порядок заправки транспорта" required />
          </div>
          <div class="fgr">
            <label class="fll">Категория *</label>
            <select v-model="form.category" class="fin">
              <option value="Склады">Склады</option>
              <option value="Транспорт">Транспорт</option>
              <option value="1С Интеграция">1С Интеграция</option>
              <option value="Общие правила">Общие правила</option>
            </select>
          </div>
          <div class="fgr">
            <label class="fll">Содержимое статьи (поддерживается Markdown) *</label>
            <textarea v-model="form.content" class="fin form-textarea" placeholder="Используйте **жирный текст** или списки через дефис..." required></textarea>
          </div>
        </div>
        <div class="mfoot">
          <button class="btn btn-ghost" @click="formModalOpen = false" :disabled="saving">Отмена</button>
          <button class="btn btn-primary" @click="saveArticle" :disabled="saving || !form.title || !form.content">
            <i v-if="saving" class="fas fa-circle-notch fa-spin"></i>
            <i v-else class="fas fa-check"></i>
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import api from '@/api'

const auth = useAuthStore()
const app = useAppStore()

const loading = ref(true)
const saving = ref(false)
const articles = ref([])
const filteredArticles = ref([])
const categories = ref(['', 'Склады', 'Транспорт', '1С Интеграция', 'Общие правила'])

const searchQuery = ref('')
const selectedCategory = ref('')

// Modal States
const detailModalOpen = ref(false)
const selectedArticle = ref(null)

const formModalOpen = ref(false)
const isEditMode = ref(false)
const form = ref({
  id: null,
  title: '',
  category: 'Общие правила',
  content: ''
})

const canWrite = computed(() => {
  return ['admin', 'director', 'manager'].includes(auth.user?.role)
})

async function fetchArticles() {
  loading.value = true
  try {
    const response = await api.get('/knowledge/list')
    articles.value = response.data
    filterArticles()
  } catch (err) {
    app.toast('err', 'Ошибка', 'Не удалось загрузить базу знаний')
    console.error(err)
  } finally {
    loading.value = false
  }
}

function filterArticles() {
  let result = articles.value
  
  if (selectedCategory.value) {
    result = result.filter(a => a.category === selectedCategory.value)
  }
  
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(a => 
      a.title.toLowerCase().includes(q) || 
      a.content.toLowerCase().includes(q)
    )
  }
  
  filteredArticles.value = result
}

function selectCategory(cat) {
  selectedCategory.value = cat
  filterArticles()
}

function clearSearch() {
  searchQuery.value = ''
  filterArticles()
}

function getSnippet(content) {
  if (!content) return ''
  const cleanText = content.replace(/[*#`_\-]/g, '')
  return cleanText.length > 130 ? cleanText.substring(0, 130) + '...' : cleanText
}

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

function getCategoryColor(category) {
  const map = {
    'Склады': '#22c55e',       // Success green
    'Транспорт': '#3b82f6',     // Primary blue
    '1С Интеграция': '#f59e0b', // Warning yellow
    'Общие правила': '#a855f7'  // Purple
  }
  return map[category] || '#64748b'
}

// Detail View
function openArticleModal(art) {
  selectedArticle.value = art
  detailModalOpen.value = true
}

function editFromDetail() {
  const art = selectedArticle.value
  detailModalOpen.value = false
  openEditModal(art)
}

// Create / Edit Actions
function openCreateModal() {
  isEditMode.value = false
  form.value = {
    id: null,
    title: '',
    category: 'Общие правила',
    content: ''
  }
  formModalOpen.value = true
}

function openEditModal(art) {
  isEditMode.value = true
  form.value = {
    id: art.id,
    title: art.title,
    category: art.category,
    content: art.content
  }
  formModalOpen.value = true
}

async function saveArticle() {
  saving.value = true
  try {
    if (isEditMode.value) {
      const response = await api.put(`/knowledge/${form.value.id}`, {
        title: form.value.title,
        category: form.value.category,
        content: form.value.content
      })
      app.toast('ok', 'Успешно', 'Статья обновлена')
      
      const idx = articles.value.findIndex(a => a.id === form.value.id)
      if (idx !== -1) {
        articles.value[idx] = response.data
      }
    } else {
      const response = await api.post('/knowledge', {
        title: form.value.title,
        category: form.value.category,
        content: form.value.content
      })
      app.toast('ok', 'Успешно', 'Статья добавлена в базу знаний')
      articles.value.unshift(response.data)
    }
    formModalOpen.value = false
    filterArticles()
  } catch (err) {
    app.toast('err', 'Ошибка сохранения', err.response?.data?.detail || 'Не удалось сохранить статью')
    console.error(err)
  } finally {
    saving.value = false
  }
}

async function deleteArticle(art) {
  if (!confirm(`Вы действительно хотите удалить статью "${art.title}"?`)) return
  
  try {
    await api.delete(`/knowledge/${art.id}`)
    app.toast('ok', 'Удалено', 'Статья успешно удалена')
    articles.value = articles.value.filter(a => a.id !== art.id)
    filterArticles()
  } catch (err) {
    app.toast('err', 'Ошибка удаления', 'Не удалось удалить статью')
    console.error(err)
  }
}

// Lightweight Markdown Renderer
function renderMarkdown(text) {
  if (!text) return ''
  
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    
  // Headers
  html = html.replace(/^###\s+(.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^##\s+(.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^#\s+(.+)$/gm, '<h2>$1</h2>')
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Bullets
  html = html.replace(/^\s*[\*\-]\s+(.+)$/gm, '<li>$1</li>')
  
  // Lists wrapper
  let inList = false
  const lines = html.split('\n')
  const processed = []
  
  for (let line of lines) {
    const trimmed = line.trim()
    const isLi = trimmed.startsWith('<li>') && trimmed.endsWith('</li>')
    if (isLi) {
      if (!inList) {
        processed.push('<ul>')
        inList = true
      }
      processed.push(line)
    } else {
      if (inList) {
        processed.push('</ul>')
        inList = false
      }
      if (trimmed === '') {
        processed.push('<br>')
      } else if (trimmed.startsWith('<h') || trimmed.startsWith('</h')) {
        processed.push(line)
      } else {
        processed.push(`<p>${line}</p>`)
      }
    }
  }
  if (inList) {
    processed.push('</ul>')
  }
  
  return processed.join('\n')
}

onMounted(() => {
  fetchArticles()
})
</script>

<style scoped>
.search-filter-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-input-wrapper {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  font-size: 14px;
}

.search-input {
  padding-left: 38px;
  padding-right: 38px;
  height: 42px;
}

.clear-search-btn {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 4px;
  font-size: 14px;
  transition: color 0.15s;
}

.clear-search-btn:hover {
  color: var(--text);
}

.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.category-tab {
  padding: 6px 14px;
  border-radius: 20px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.category-tab:hover {
  background: #fff;
  border-color: var(--primary);
  color: var(--primary);
}

.category-tab.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);
}

.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.article-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 20px;
  box-shadow: var(--sh);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.article-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--sh-md);
  border-color: var(--primary);
}

.article-category-badge {
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  padding: 3px 8px;
  border-radius: 4px;
  width: fit-content;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.article-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.4;
}

.article-snippet {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: auto;
  min-height: 60px;
}

.article-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--bg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.article-date {
  font-size: 11px;
  color: var(--muted);
}

.article-actions {
  display: flex;
  gap: 6px;
}

.btn-icon {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: none;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.15s;
}

.btn-edit {
  color: var(--primary);
}
.btn-edit:hover {
  background: rgba(37, 99, 235, 0.1);
}

.btn-delete {
  color: var(--danger);
}
.btn-delete:hover {
  background: rgba(239, 68, 68, 0.1);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 40px;
  color: var(--muted);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
}

.empty-state p {
  font-size: 13px;
  color: var(--muted);
  max-width: 400px;
}

/* Modals Custom Styles */
.kb-detail-modal {
  max-width: 650px;
}

.kb-form-modal {
  max-width: 600px;
}

.header-text-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-category {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-content {
  max-height: 60vh;
  overflow-y: auto;
  line-height: 1.7;
}

.form-textarea {
  min-height: 240px;
}

/* Markdown styling inside detail modal */
.markdown-body :deep(h2), 
.markdown-body :deep(h3), 
.markdown-body :deep(h4) {
  margin: 18px 0 10px 0;
  font-weight: 700;
  color: var(--text);
}

.markdown-body :deep(h2) { font-size: 18px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
.markdown-body :deep(h3) { font-size: 15px; }
.markdown-body :deep(h4) { font-size: 13px; }

.markdown-body :deep(p) {
  margin-bottom: 12px;
  font-size: 13px;
}

.markdown-body :deep(ul) {
  margin-bottom: 12px;
  padding-left: 20px;
  list-style-type: disc;
}

.markdown-body :deep(li) {
  margin-bottom: 6px;
  font-size: 13px;
}

.markdown-body :deep(strong) {
  font-weight: 700;
  color: var(--text);
}

.markdown-body :deep(br) {
  content: "";
  display: block;
  margin-top: 8px;
}

@media(max-width: 600px) {
  .articles-grid {
    grid-template-columns: 1fr;
  }
}
</style>
