import os
import httpx
from mcp.server.fastmcp import FastMCP

# Инициализируем MCP Сервер под названием "1C-MCP-Server"
# FastMCP автоматически генерирует схему инструментов на основе аннотаций типов и docstring.
mcp = FastMCP("1C-MCP-Server")

# Параметры подключения к 1С (можно переопределить через переменные окружения)
ONEC_BASE_URL = os.getenv("ONEC_BASE_URL", "http://127.0.0.1:8081/InfoBase4/hs/edu-agent")
ONEC_USER = os.getenv("ONEC_USER", "admin")
ONEC_PASSWORD = os.getenv("ONEC_PASSWORD", "PASSWORD")

def get_client() -> httpx.AsyncClient:
    """Создает асинхронный HTTP-клиент с авторизацией Basic Auth для 1С."""
    return httpx.AsyncClient(
        auth=(ONEC_USER, ONEC_PASSWORD),
        headers={"Content-Type": "application/json"},
        timeout=30.0
    )

@mcp.tool()
async def ping_1c() -> str:
    """
    Проверить доступность публикации и HTTP-сервиса 1С.
    Возвращает статус подключения и базовые метаданные (имя конфигурации и время).
    """
    async with get_client() as client:
        try:
            response = await client.post(f"{ONEC_BASE_URL}/ping", json={})
            if response.status_code == 200:
                return f"Успешное подключение к 1С!\nОтвет сервера: {response.text}"
            else:
                return f"Ошибка при подключении к 1С (HTTP-код {response.status_code}): {response.text}"
        except Exception as e:
            return f"Не удалось подключиться к 1С. Ошибка подключения: {str(e)}"

@mcp.tool()
async def discover_1c_configuration(role: str = "admin", include_fields: bool = True) -> str:
    """
    Загрузить список доступных метаданных из 1С (справочники, документы, регистры) для указанной роли.
    
    Args:
        role: Роль для проверки прав (например: admin, director, accountant, study-office, department-head)
        include_fields: Флаг, нужно ли загружать структуру полей (реквизитов) для каждого объекта
    """
    async with get_client() as client:
        try:
            payload = {
                "role": role,
                "includeFields": include_fields
            }
            response = await client.post(f"{ONEC_BASE_URL}/metadata", json=payload)
            if response.status_code == 200:
                return response.text
            else:
                return f"Ошибка при запросе метаданных из 1С (HTTP-код {response.status_code}): {response.text}"
        except Exception as e:
            return f"Не удалось получить метаданные от 1С. Ошибка: {str(e)}"

@mcp.tool()
async def query_1c_data(
    dataset_id: str,
    role: str,
    period_start: str = None,
    period_end: str = None,
    query_text: str = None,
    limit: int = 50
) -> str:
    """
    Запросить табличные данные из конкретного объекта 1С по его datasetId (например, '1c://object/document/РекламационныеАкты').
    Модель использует этот инструмент для выборки строк из разрешенных источников.
    
    Args:
        dataset_id: Идентификатор источника из 1С (брать точное значение из результатов discover_1c_configuration, например: 1c://object/document/РекламационныеАкты)
        role: Роль пользователя для валидации доступа
        period_start: Начальная дата периода выборки в формате YYYY-MM-DD (необязательно)
        period_end: Конечная дата периода выборки в формате YYYY-MM-DD (необязательно)
        query_text: Строка текстового поиска или фильтрации (необязательно)
        limit: Лимит количества возвращаемых строк (по умолчанию 50)
    """
    async with get_client() as client:
        try:
            params = {}
            if period_start:
                params["periodStart"] = period_start
            if period_end:
                params["periodEnd"] = period_end
            if query_text:
                params["query"] = query_text

            payload = {
                "datasetId": dataset_id,
                "role": role,
                "params": params,
                "limit": limit
            }
            response = await client.post(f"{ONEC_BASE_URL}/universal-data", json=payload)
            if response.status_code == 200:
                return response.text
            else:
                return f"Ошибка получения данных из 1С (HTTP-код {response.status_code}): {response.text}"
        except Exception as e:
            return f"Не удалось выполнить запрос в 1С. Ошибка: {str(e)}"

if __name__ == "__main__":
    # Запускает MCP-сервер через стандартный ввод/вывод (stdio),
    # что является стандартным способом интеграции для MCP-клиентов (например, Claude Desktop).
    mcp.run()
