import os
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from auth_utils import get_current_user
import models
import schemas

# Импортируем функции из нашего 1С MCP-сервера
try:
    from mcp_server_1c import ping_1c, discover_1c_configuration, query_1c_data
except ImportError:
    # Заглушки на случай, если файл не найден в пути импорта
    async def ping_1c(): return "MCP 1С модуль не найден"
    async def discover_1c_configuration(role="admin", include_fields=True): return "MCP 1С модуль не найден"
    async def query_1c_data(*args, **kwargs): return "MCP 1С модуль не найден"

router = APIRouter(prefix="/api/mcp", tags=["MCP AI Chat"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_router")

# Конфигурация локальной Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b") # По умолчанию легкая gemma4

class ChatMessage(BaseModel):
    role: str # "user", "assistant", "system", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# --- Определение локальных инструментов для базы данных ---

async def get_local_warehouse_summary(db: Session) -> str:
    """Получает актуальную сводку по складам и остаткам товаров из локальной БД NortGru."""
    try:
        warehouses = db.query(models.Warehouse).all()
        products = db.query(models.Product).all()
        stocks = db.query(models.Stock).all()
        
        if not warehouses:
            return "В базе данных нет зарегистрированных складов."
        
        result = "=== Склады NortGru ===\n"
        for wh in warehouses:
            result += f"📍 **Склад: {wh.name}** (Локация: {wh.location or 'Не указана'})\n"
            wh_stocks = [s for s in stocks if s.warehouse_id == wh.id]
            if not wh_stocks:
                result += "  (Остатки товаров отсутствуют)\n"
            for st in wh_stocks:
                prod = next((p for p in products if p.id == st.product_id), None)
                prod_name = prod.name if prod else f"Товар ID {st.product_id}"
                result += f"  - {prod_name}: **{st.quantity}** тонн/шт.\n"
        return result
    except Exception as e:
        logger.error(f"Error in get_local_warehouse_summary: {str(e)}")
        return f"Ошибка при получении данных о складах: {str(e)}"

async def get_local_vehicles_and_drivers(db: Session) -> str:
    """Получает сводку по автотранспорту и активным путевым листам из локальной БД NortGru."""
    try:
        vehicles = db.query(models.Vehicle).all()
        drivers = db.query(models.Driver).all()
        waybills = db.query(models.Waybill).all()
        
        result = "=== Транспорт и Водители ===\n"
        result += f"Всего транспортных средств в автопарке: {len(vehicles)}\n"
        for v in vehicles[:5]: # Показываем первые 5 для компактности
            result += f"🚘 {v.brand} (Гос.номер: {v.gov_number}), Пробег: {v.current_mileage or 0} км\n"
            
        result += f"\nВсего водителей в системе: {len(drivers)}\n"
        result += f"Всего путевых листов: {len(waybills)}\n"
        
        active_waybills = [w for w in waybills if w.color_mark == "active" or not w.is_1c_integrated]
        result += f"Активных (не интегрированных в 1С) путевых листов: {len(active_waybills)}\n"
        for w in active_waybills[:5]:
            v_info = next((veh.brand + " " + veh.gov_number for veh in vehicles if veh.id == w.vehicle_id), "Неизвестное авто")
            result += f"  - Путевой лист №{w.series_number} от {w.date} на авто [{v_info}]\n"
            
        return result
    except Exception as e:
        logger.error(f"Error in get_local_vehicles_and_drivers: {str(e)}")
        return f"Ошибка при получении данных о транспорте: {str(e)}"

async def search_knowledge_base_local(query: str, db: Session) -> str:
    """Поиск по локальной корпоративной базе знаний."""
    try:
        if not query:
            return "Не передан запрос для поиска."
            
        search_filter = f"%{query}%"
        items = db.query(models.KnowledgeItem).filter(
            (models.KnowledgeItem.title.ilike(search_filter)) |
            (models.KnowledgeItem.content.ilike(search_filter))
        ).all()
        
        if not items:
            # Попробуем сделать поиск по отдельным словам
            words = [w for w in query.split() if len(w) > 4]
            if words:
                conditions = []
                for w in words:
                    conditions.append(models.KnowledgeItem.title.ilike(f"%{w}%"))
                    conditions.append(models.KnowledgeItem.content.ilike(f"%{w}%"))
                items = db.query(models.KnowledgeItem).filter(or_(*conditions)).all()
                
        if not items:
            return f"По запросу '{query}' ничего не найдено."
            
        result = ""
        for item in items:
            result += f"📖 **{item.title}** (Категория: {item.category})\n{item.content}\n\n"
            
        return result.strip()
    except Exception as e:
        logger.error(f"Error in search_knowledge_base_local: {str(e)}")
        return f"Ошибка поиска: {str(e)}"

# --- Схема описания инструментов для Ollama ---

OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
          "name": "get_local_warehouse_summary",
          "description": "Получить сводку по остаткам торфа и других товаров на складах в локальной БД NortGru"
        }
    },
    {
        "type": "function",
        "function": {
          "name": "get_local_vehicles_and_drivers",
          "description": "Получить список автотранспорта и активных путевых листов водителей в локальной БД NortGru"
        }
    },
    {
        "type": "function",
        "function": {
          "name": "search_knowledge_base",
          "description": "Поиск регламентов, инструкций, FAQ и общей информации в корпоративной базе знаний NortGru",
          "parameters": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string",
                "description": "Ключевые слова для поиска в базе знаний (например: интеграция 1С, регламент складов, заполнение путевых листов)"
              }
            },
            "required": ["query"]
          }
        }
    },
    {
        "type": "function",
        "function": {
          "name": "ping_1c_service",
          "description": "Проверить доступность публикации и HTTP-сервиса 1С"
        }
    },
    {
        "type": "function",
        "function": {
          "name": "discover_1c_metadata",
          "description": "Загрузить структуру метаданных 1С (список справочников, документов и реквизитов) для указанной роли",
          "parameters": {
            "type": "object",
            "properties": {
              "role": {
                "type": "string",
                "description": "Роль доступа (admin, director, accountant, study-office, department-head)",
                "default": "admin"
              },
              "include_fields": {
                "type": "boolean",
                "description": "Включать ли описание реквизитов (полей)",
                "default": True
              }
            }
          }
        }
    },
    {
        "type": "function",
        "function": {
          "name": "query_1c_data",
          "description": "Запросить табличные данные из конкретного объекта 1С по его datasetId (например: 1c://object/document/РекламационныеАкты)",
          "parameters": {
            "type": "object",
            "properties": {
              "dataset_id": {
                "type": "string",
                "description": "Уникальный ID объекта 1С"
              },
              "role": {
                "type": "string",
                "description": "Роль доступа для проверки прав в 1С"
              },
              "period_start": {
                "type": "string",
                "description": "Начальная дата периода в формате YYYY-MM-DD (необязательно)"
              },
              "period_end": {
                "type": "string",
                "description": "Конечная дата периода в формате YYYY-MM-DD (необязательно)"
              },
              "query_text": {
                "type": "string",
                "description": "Строка поиска или текстовый фильтр (необязательно)"
              },
              "limit": {
                "type": "integer",
                "description": "Максимальное количество возвращаемых строк",
                "default": 50
              }
            },
            "required": ["dataset_id", "role"]
          }
        }
    }
]

# --- Основной обработчик чата с поддержкой инструментов ---

@router.post("/chat")
async def mcp_chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    # Превращаем историю сообщений в формат Ollama
    history = []
    for msg in request.messages:
        item = {"role": msg.role, "content": msg.content}
        if msg.name:
            item["name"] = msg.name
        if msg.tool_calls:
            item["tool_calls"] = msg.tool_calls
        history.append(item)
    
    # Добавляем системную инструкцию в начало диалога
    user_roles = [r.role_type for r in current_user.roles]
    primary_role = user_roles[0] if user_roles else "user"
    
    system_instruction = (
        "Ты — корпоративный AI-ассистент компании NortGru. "
        "Твоя задача — отвечать на вопросы о работе компании NortGru, её складах торфа, транспорте, логистике, базе знаний и интеграции с 1С.\n"
        "У тебя есть доступ к инструментам для чтения локальной базы данных NortGru, корпоративной Базы Знаний и удаленной системы 1С.\n"
        f"Текущий пользователь: {current_user.full_name}, его роль в системе: {primary_role}.\n"
        "Если пользователь спрашивает про склад, транспорт или путевые листы, обязательно используй локальные инструменты. "
        "Если вопрос касается общих правил, регламентов, инструкций или FAQ, используй инструмент search_knowledge_base.\n"
        "Если вопрос касается внешних данных 1С, используй 1С инструменты.\n"
        "ПРАВИЛА ОФОРМЛЕНИЯ ОТВЕТОВ:\n"
        "- Ты можешь использовать стандартные списки (через дефис '-'). Они будут красиво отрендерены на фронтенде в виде маркированных списков и жирного текста.\n"
        "- Избегай использования сырых символов решеток (#, ##, ###) в ответах. Если нужно выделить заголовок, используй жирный шрифт или новые строки.\n"
        "Текст писать без больших промежутков между предложениями, чтобы одно сообщение было не таким громозким.\n"
        "ОГРАНИЧЕНИЕ ТЕМАТИКИ:\n"
        "- Отвечай только на вопросы, связанные с работой компании NortGru. Если задан посторонний вопрос (не о NortGru), вежливо откажись отвечать.\n"
        "Отвечай на русском языке вежливо, профессионально."
    )
    
    # Если системного промпта нет, вставляем его
    if not any(m["role"] == "system" for m in history):
        history.insert(0, {"role": "system", "content": system_instruction})
        
    tools_called = []
    max_steps = 5 # Защита от бесконечного цикла вызовов инструментов
    
    # Короткий таймаут на коннект (3 сек), длинный на генерацию текста ИИ (25 сек)
    timeout_config = httpx.Timeout(25.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        for step in range(max_steps):
            logger.info(f"Ollama Request Step {step + 1} with {len(history)} messages")
            try:
                # Отправляем запрос в локальную Ollama
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": history,
                    "tools": OLLAMA_TOOLS,
                    "stream": False
                }
                
                response = await client.post(OLLAMA_URL, json=payload)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Ошибка сервера Ollama: {response.text}"
                    )
                
                resp_json = response.json()
                message_out = resp_json.get("message", {})
                tool_calls = message_out.get("tool_calls", [])
                
                # Добавляем ответ модели в историю, чтобы сохранить последовательность
                history.append(message_out)
                
                if not tool_calls:
                    # Если инструментов больше вызывать не нужно, возвращаем ответ
                    return {
                        "role": "assistant",
                        "content": message_out.get("content", ""),
                        "tools_called": tools_called,
                        "offline": False
                    }
                
                # Если модель решила вызвать один или несколько инструментов
                for tc in tool_calls:
                    func_info = tc.get("function", {})
                    name = func_info.get("name")
                    args = func_info.get("arguments", {})
                    
                    logger.info(f"Ollama requested tool call: {name} with args: {args}")
                    tools_called.append(name)
                    
                    result = ""
                    
                    # Выполняем соответствующий инструмент
                    if name == "get_local_warehouse_summary":
                        result = await get_local_warehouse_summary(db)
                    elif name == "get_local_vehicles_and_drivers":
                        result = await get_local_vehicles_and_drivers(db)
                    elif name == "search_knowledge_base":
                        query_arg = args.get("query", "")
                        result = await search_knowledge_base_local(query_arg, db)
                    elif name == "ping_1c_service":
                        result = await ping_1c()
                    elif name == "discover_1c_metadata":
                        role_arg = args.get("role", primary_role)
                        include_fields = args.get("include_fields", True)
                        result = await discover_1c_configuration(role=role_arg, include_fields=include_fields)
                    elif name == "query_1c_data":
                        dataset_id = args.get("dataset_id")
                        role_arg = args.get("role", primary_role)
                        period_start = args.get("period_start")
                        period_end = args.get("period_end")
                        query_text = args.get("query_text")
                        limit = args.get("limit", 50)
                        
                        if not dataset_id:
                            result = "Ошибка: не указан dataset_id"
                        else:
                            result = await query_1c_data(
                                dataset_id=dataset_id,
                                role=role_arg,
                                period_start=period_start,
                                period_end=period_end,
                                query_text=query_text,
                                limit=limit
                            )
                    else:
                        result = f"Инструмент {name} не найден на бэкенде."
                    
                    # Отправляем результат выполнения инструмента обратно в Ollama
                    history.append({
                        "role": "tool",
                        "name": name,
                        "content": str(result)
                    })
                    
            except (httpx.ConnectError, httpx.HTTPError, Exception) as e:
                # Включаем умный офлайн-режим при любой ошибке ИИ
                if True:
                    logger.warning(f"Ollama connection failed, switching to offline fallback. Error: {str(e)}")
                    
                    # Извлекаем последний вопрос пользователя
                    user_msg = request.messages[-1].content
                    user_msg_lower = user_msg.lower()
                    
                    # Фильтрация по запрещенным тематикам (регламент)
                    forbidden_keywords = ["погода", "рецепт", "код", "программиров", "javascript", "python", "кулинар", "анекдот"]
                    if any(kw in user_msg_lower for kw in forbidden_keywords):
                        return {
                            "role": "assistant",
                            "content": "К сожалению, я могу отвечать только на вопросы, непосредственно связанные с работой компании NortGru, ее складами, транспортом и интеграцией 1С.",
                            "tools_called": [],
                            "offline": True
                        }
                    
                    # 1. Поиск упоминаний Складов
                    if any(kw in user_msg_lower for kw in ["склад", "остатк", "товар", "торф"]):
                        wh_summary = await get_local_warehouse_summary(db)
                        return {
                            "role": "assistant",
                            "content": wh_summary,
                            "tools_called": ["get_local_warehouse_summary"],
                            "offline": True
                        }
                        
                    # 2. Поиск упоминаний Транспорта
                    if any(kw in user_msg_lower for kw in ["транспорт", "водитель", "путев", "машин", "авто", "рейс"]):
                        veh_summary = await get_local_vehicles_and_drivers(db)
                        return {
                            "role": "assistant",
                            "content": veh_summary,
                            "tools_called": ["get_local_vehicles_and_drivers"],
                            "offline": True
                        }

                    # 2.5. Поиск упоминаний 1С
                    if any(kw in user_msg_lower for kw in ["1с", "1c", "интеграц"]):
                        if any(kw in user_msg_lower for kw in ["подключ", "пинг", "связ", "доступ", "провер"]):
                            ping_res = await ping_1c()
                            return {
                                "role": "assistant",
                                "content": ping_res,
                                "tools_called": ["ping_1c_service"],
                                "offline": True
                            }
                        elif any(kw in user_msg_lower for kw in ["рекламац", "акт", "брак"]):
                            rec_res = await query_1c_data(dataset_id="1c://object/document/РекламационныеАкты", role=primary_role)
                            try:
                                data = json.loads(rec_res)
                                content = "=== Рекламационные акты из 1С ===\n\n"
                                for item in data:
                                    content += f"- **{item['Номер']}** от {item['Дата']} (Контрагент: {item['Контрагент']}, Склад: {item['Склад']})\n"
                                    content += f"  Сумма: **{item['СуммаДокумента']} руб.** | Причина: {item['ПричинаБрака']} | Статус: *{item['Статус']}*\n"
                            except Exception:
                                content = rec_res
                            return {
                                "role": "assistant",
                                "content": content.strip(),
                                "tools_called": ["query_1c_data"],
                                "offline": True
                            }
                        elif any(kw in user_msg_lower for kw in ["поступлен", "закупк", "тн", "услуг"]):
                            post_res = await query_1c_data(dataset_id="1c://object/document/ПоступлениеТоваровУслуг", role=primary_role)
                            try:
                                data = json.loads(post_res)
                                content = "=== Поступления товаров и услуг из 1С ===\n\n"
                                for item in data:
                                    content += f"- **{item['Номер']}** от {item['Дата']} (Поставщик: {item['Контрагент']}, Склад: {item['Склад']})\n"
                                    content += f"  Сумма: **{item['СуммаДокумента']} руб.** | Комментарий: {item['Комментарий']}\n"
                            except Exception:
                                content = post_res
                            return {
                                "role": "assistant",
                                "content": content.strip(),
                                "tools_called": ["query_1c_data"],
                                "offline": True
                            }
                        elif any(kw in user_msg_lower for kw in ["контрагент", "поставщик", "партнер"]):
                            part_res = await query_1c_data(dataset_id="1c://object/catalog/Контрагенты", role=primary_role)
                            try:
                                data = json.loads(part_res)
                                content = "=== Справочник Контрагенты из 1С ===\n\n"
                                for item in data:
                                    content += f"- **{item['Наименование']}** (Код: {item['Код']}, ИНН: {item['ИНН']})\n"
                                    content += f"  Юр. адрес: {item['ЮридическийАдрес']}\n"
                            except Exception:
                                content = part_res
                            return {
                                "role": "assistant",
                                "content": content.strip(),
                                "tools_called": ["query_1c_data"],
                                "offline": True
                            }
                        else:
                            meta_res = await discover_1c_configuration(role=primary_role)
                            try:
                                data = json.loads(meta_res)
                                content = "=== Доступные объекты интеграции 1С ===\n\n"
                                for obj in data.get("objects", []):
                                    content += f"- **{obj['name']}**: {obj['description']}\n"
                                    content += f"  Поля: {', '.join(obj['fields'])}\n"
                            except Exception:
                                content = meta_res
                            return {
                                "role": "assistant",
                                "content": content.strip(),
                                "tools_called": ["discover_1c_metadata"],
                                "offline": True
                            }

                    # 3. Поиск в Базе Знаний по заголовкам статей
                    items = db.query(models.KnowledgeItem).all()
                    matched_articles = []
                    for item in items:
                        title_lower = item.title.lower()
                        if title_lower in user_msg_lower or any(word in user_msg_lower for word in title_lower.split() if len(word) > 4):
                            matched_articles.append(item)
                            
                    if matched_articles:
                        res_content = ""
                        for art in matched_articles:
                            res_content += f"**{art.title}**\n{art.content}\n\n"
                        return {
                            "role": "assistant",
                            "content": res_content.strip(),
                            "tools_called": ["search_knowledge_base"],
                            "offline": True
                        }
                        
                    # 4. Общий поиск по совпадению слов в Базе Знаний
                    search_words = [w for w in user_msg_lower.split() if len(w) > 4]
                    if search_words:
                        conditions = []
                        for w in search_words:
                            conditions.append(models.KnowledgeItem.title.ilike(f"%{w}%"))
                            conditions.append(models.KnowledgeItem.content.ilike(f"%{w}%"))
                        
                        db_items = db.query(models.KnowledgeItem).filter(or_(*conditions)).all()
                        if db_items:
                            res_content = ""
                            for art in db_items[:2]:
                                res_content += f"**{art.title}**\n{art.content}\n\n"
                            return {
                                "role": "assistant",
                                "content": res_content.strip(),
                                "tools_called": ["search_knowledge_base"],
                                "offline": True
                            }
                            
                    # 5. Приветствие
                    if any(kw in user_msg_lower for kw in ["привет", "здравствуй", "добрый день", "hello"]):
                        return {
                            "role": "assistant",
                            "content": (
                                f"Здравствуйте, {current_user.full_name}! Я ваш корпоративный ассистент и готов ответить на ваши вопросы.\n\n"
                                "Напишите, что именно вас интересует, например:\n"
                                "- *Покажи остатки на складах*\n"
                                "- *Какие машины сейчас работают?*\n"
                                "- *Инструкция по интеграции с 1С*"
                            ),
                            "tools_called": [],
                            "offline": True
                        }
                    
                    # 6. Стандартный ответ при отсутствии совпадений
                    return {
                        "role": "assistant",
                        "content": (
                            "Я не смог найти точного ответа на ваш вопрос. Пожалуйста, сформулируйте вопрос точнее, например:\n"
                            "- *показать остатки на складах*\n"
                            "- *показать путевые листы*\n"
                            "- *инструкция по заполнению путевых листов*"
                        ),
                        "tools_called": [],
                        "offline": True
                    }
                else:
                    logger.error(f"Error in chat step: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Ошибка в процессе обработки чата: {str(e)}"
                    )
                
        # Если превышено число шагов
        last_content = history[-1].get("content", "Превышено максимальное число вызовов инструментов ИИ.")
        return {
            "role": "assistant",
            "content": last_content,
            "tools_called": tools_called,
            "offline": False
        }
