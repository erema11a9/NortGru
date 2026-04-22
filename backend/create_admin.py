import models
from database import SessionLocal, engine, Base
from passlib.context import CryptContext

# Явно задаем схему 'bcrypt', чтобы избежать конфликтов версий
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    print("🚀 Подключаюсь к базе...")
    db = SessionLocal()
    try:
        # Проверяем роль
        admin_role = db.query(models.Role).filter(models.Role.role_type == "admin").first()
        if not admin_role:
            admin_role = models.Role(role_type="admin")
            db.add(admin_role)
            db.flush()

        email = "popi.dir@mail.ru"
        existing_user = db.query(models.Person).filter(models.Person.email == email).first()
        
        if not existing_user:
            # Важно: Хешируем пароль "123"
            hashed_pass = pwd_context.hash("123")
            
            new_person = models.Person(
                full_name="Еремин Дмитрий Сергеевич",
                email=email,
                password_hash=hashed_pass
            )
            db.add(new_person)
            db.flush()

            # Привязываем роль
            db.execute(
                models.PersonRole.__table__.insert().values(
                    person_id=new_person.id, 
                    role_id=admin_role.id
                )
            )
            
            db.commit()
            print(f"✅ Готово! Теперь точно всё в базе.")
        else:
            print(f"⚠️ Пользователь {email} уже есть.")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании админа: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()