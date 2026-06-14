FROM python:3.11-slim

WORKDIR /code

# Копируем требования и устанавливаем зависимости
COPY backend/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Копируем весь бэкенд в рабочую директорию
COPY backend/ /code/

# Запускаем uvicorn на порту 7860 (это стандартный порт для Hugging Face Spaces)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
