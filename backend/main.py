from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Импортируем роутеры (убедись, что в них внутри тоже обновлен импорт моделей)
from routers import auth, warehouse, documents, analytics, transport, notifications, mcp, knowledge
from database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаст таблицы в PostgreSQL, если их еще нет.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="NortGru API",
    description="Корпоративный личный кабинет",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── Logging Middlewares/Handlers for Debugging ────────────────────────────────
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    try:
        with open("backend_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- EXCEPTION on {request.url.path}: {exc} ---\n")
            f.write(traceback.format_exc())
    except Exception as e:
        print(f"Logging failed: {e}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def debug_validation_handler(request, exc):
    try:
        with open("backend_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- VALIDATION ERROR on {request.url.path}: {exc} ---\n")
            f.write(str(exc.errors()))
    except Exception as e:
        print(f"Logging failed: {e}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# ── CORS (Настройки для Vite и Render) ───────────────────────────────────────
import os

allowed_origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:3000"
]
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins.extend([origin.strip() for origin in env_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",  # Автоматически разрешаем фронтенд на Render
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
app.include_router(mcp.router, tags=["MCP"])
app.include_router(knowledge.router, tags=["Knowledge Base"])

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "working", 
        "project": "NortGru",
        "version": "1.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)