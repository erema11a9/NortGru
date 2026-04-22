from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


from database import get_db
import models, schemas

from auth_utils import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    # 1. Поиск пользователя
    user = db.query(models.Person).filter(models.Person.email == data.email).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )

    # 2. Извлекаем реальные роли из базы
    user_roles = [r.role_type for r in user.roles]
    primary_role = user_roles[0] if user_roles else "user"

    # 3. Извлекаем должность/департамент (через таблицу Employee)
    job_name = "Не указана"
    try:
        employee_record = db.query(models.Employee).filter(models.Employee.person_id == user.id).first()
        if employee_record and getattr(employee_record, 'job_title_id', None):
            job_title = db.query(models.JobTitle).filter(models.JobTitle.id == employee_record.job_title_id).first()
            if job_title:
                job_name = job_title.name
    except Exception:
        db.rollback()

    # 4. Генерируем нормальный JWT с временем жизни
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "roles": user_roles}
    )
    
    # 5. Собираем ответ (уже без заглушек)
    user_info = schemas.UserResponse(
        id=user.id,
        name=user.full_name,
        email=user.email,
        role=primary_role,
        department=job_name,
        is_active=True,
        created_at=datetime.now() # Тут можно добавить поле в models.Person, если нужно
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": user_info
    }