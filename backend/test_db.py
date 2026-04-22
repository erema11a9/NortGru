import os
from sqlalchemy import create_engine, text

# Это лечит проблемы с кодировкой на Windows
os.environ['PGCLIENTENCODING'] = 'utf-8'

# ПРОВЕРЬ: здесь должно быть postgresql (с 'ql' на конце)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12393qwe@localhost:5432/nortgru_db"

def check():
    try:
        # Используем актуальный драйвер psycopg2 (он под капотом)
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        with engine.connect() as conn:
            # Простейшая проверка связи
            res = conn.execute(text("SELECT 1;"))
            print("✅ Соединение с PostgreSQL установлено!")
            
            # Проверка конкретной базы
            res = conn.execute(text("SELECT current_database();"))
            print(f"🗄️ База данных: {res.fetchone()[0]}")

    except Exception as e:
        print("❌ Ошибка подключения!")
        print(f"Детали: {str(e)}")

if __name__ == "__main__":
    check()