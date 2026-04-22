from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Импортируем роутеры (убедись, что в них внутри тоже обновлен импорт моделей)
from routers import auth, warehouse, documents, analytics, transport, notifications
from database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаст таблицы в PostgreSQL, если их еще нет.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="NortGru API",
    description="Корпоративный личный кабинет (PostgreSQL Version)",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS (Настройки для Vite) ───────────────────────────────────────────────
# Добавил 127.0.0.1, так как браузеры иногда капризничают с localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация БД теперь происходит через lifespan

# ── Роутеры ──────────────────────────────────────────────────────────────────
# Добавил новый роутер 'transport', так как мы создали таблицы для машин
app.include_router(auth.router, tags=["Auth"])
app.include_router(warehouse.router, tags=["Warehouse"])
app.include_router(transport.router, tags=["Transport"])
app.include_router(documents.router, tags=["Documents"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(notifications.router, tags=["Notifications"])

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "working", 
        "database": "PostgreSQL", 
        "project": "NortGru",
        "version": "1.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)