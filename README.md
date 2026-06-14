# NortGru — Корпоративный личный кабинет
**ООО «НОРД-ИСТ ГРУПП»** | Биробиджан / Хабаровск

## Стек технологий
- **Backend:** Python 3.10+ · FastAPI · SQLAlchemy (SQLite) · JWT Auth
- **Frontend:** Vue 3 · Vite · Pinia · Vue Router · Chart.js · Axios

## Быстрый старт

### Требования
- **Python** 3.10+ — https://python.org
- **Node.js** 18+ — https://nodejs.org

### Запуск
1. Откройте **два окна** терминала (или запустите два `.bat` файла)
2. **Окно 1** — Backend:  `start_backend.bat`
3. **Окно 2** — Frontend: `start_frontend.bat`
4. Откройте браузер: **http://localhost:5173**

### Тестовые аккаунты (пароль для всех: `demo123`)
| Email | Роль | Доступ |
|---|---|---|
| director@nortgru.ru | Директор | Полный |
| manager@nortgru.ru  | Финансовый менеджер | Аналитика, документы |
| master@nortgru.ru   | Мастер-бригадир | Склад, документы |
| warehouse@nortgru.ru | Кладовщик | Склад, документы |

## Развертывание в Docker (на VPS / Ubuntu)

Проект полностью оптимизирован для запуска на VPS-сервере через Docker.
Все подробные инструкции по настройке сервера, брандмауэра (UFW), интеграции с Ollama и запуску находятся в документе:
👉 **[Руководство по развертыванию (DEPLOYMENT.md)](file:///c:/Users/Erema/Desktop/ДимаКурорМодельКуртая/NortGru/DEPLOYMENT.md)**

### Быстрый запуск на сервере:
1. Клонируйте проект из GitHub на ваш VPS и перейдите в папку.
2. Сделайте скрипт исполняемым: `chmod +x deploy.sh`
3. Запустите скрипт авторазвертывания: `./deploy.sh`

## Структура проекта
```
NortGru/
├── backend/                    # FastAPI сервер
│   ├── main.py                 # Точка входа
│   ├── models.py               # SQLAlchemy модели
│   ├── schemas.py              # Pydantic схемы
│   ├── auth_utils.py           # JWT утилиты
│   ├── init_db.py              # Инициализация БД
│   └── routers/                # API роутеры
│       ├── auth.py             # POST /api/auth/login
│       ├── warehouse.py        # /api/warehouse/
│       ├── documents.py        # /api/documents/
│       └── analytics.py        # /api/analytics/
│
└── frontend/                   # Vue 3 приложение
    └── src/
        ├── views/              # Страницы
        │   ├── Login.vue
        │   ├── Dashboard.vue
        │   ├── Warehouse.vue
        │   ├── Documents.vue
        │   ├── Analytics.vue
        │   └── Profile.vue
        ├── stores/             # Pinia хранилища
        ├── components/         # Layout.vue
        └── api.js              # Axios клиент
```

## API Документация
После запуска backend доступна по адресу: http://localhost:8000/api/docs
