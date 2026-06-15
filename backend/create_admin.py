import models
from database import SessionLocal, engine, Base
from passlib.context import CryptContext

# Явно задаем схему 'bcrypt', чтобы избежать конфликтов версий
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    print("Connecting to database...")
    db = SessionLocal()
    try:
        # Убедимся, что роли существуют в БД
        roles_to_create = ["admin", "director", "manager", "master", "warehouse"]
        role_objects = {}
        for r_type in roles_to_create:
            role = db.query(models.Role).filter(models.Role.role_type == r_type).first()
            if not role:
                role = models.Role(role_type=r_type)
                db.add(role)
                db.flush()
            role_objects[r_type] = role

        # Данные предустановленных пользователей
        users_to_create = [
            {
                "full_name": "Еремин Дмитрий Сергеевич",
                "email": "dmitry.erema@mail.ru",
                "role": "admin",
                "password": "123"
            },
            {
                "full_name": "Тимофеев Александр Николаевич",
                "email": "timofeev.dir@mail.ru",
                "role": "director",
                "password": "123"
            }
        ]

        for u_data in users_to_create:
            email = u_data["email"]
            user = db.query(models.Person).filter(models.Person.email == email).first()
            
            if not user:
                print(f"Creating user {u_data['full_name']} ({email})...")
                hashed_pass = pwd_context.hash(u_data["password"])
                user = models.Person(
                    full_name=u_data["full_name"],
                    email=email,
                    password_hash=hashed_pass,
                    is_approved=True
                )
                db.add(user)
                db.flush()

                # Привязываем роль
                role_obj = role_objects[u_data["role"]]
                db.execute(
                    models.PersonRole.__table__.insert().values(
                        person_id=user.id, 
                        role_id=role_obj.id
                    )
                )
                
                # Создаем запись Employee (сотрудник) для должности
                job_title_name = "Администратор" if u_data["role"] == "admin" else "Генеральный директор"
                job_title = db.query(models.JobTitle).filter(models.JobTitle.name == job_title_name).first()
                if not job_title:
                    job_title = models.JobTitle(name=job_title_name)
                    db.add(job_title)
                    db.flush()
                
                employee = models.Employee(
                    person_id=user.id,
                    job_title_id=job_title.id,
                    tabel_number=f"T-{user.id:04d}"
                )
                db.add(employee)
                db.flush()
                
                print(f"User {email} created successfully!")
            else:
                print(f"User {email} already exists. Updating approval status...")
                user.is_approved = True
                
                # Проверим, привязана ли роль
                role_obj = role_objects[u_data["role"]]
                role_exists = db.query(models.PersonRole).filter(
                    models.PersonRole.person_id == user.id,
                    models.PersonRole.role_id == role_obj.id
                ).first()
                if not role_exists:
                    db.execute(
                        models.PersonRole.__table__.insert().values(
                            person_id=user.id, 
                            role_id=role_obj.id
                        )
                    )
                db.flush()

        db.commit()
        print("All preset users configured successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error during user initialization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()