from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from database import get_db
import models, schemas

from auth_utils import verify_password, create_access_token, get_password_hash, require_role

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

    # 2. Проверка одобрения администратором
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваша учетная запись ожидает одобрения администратором"
        )

    # 3. Извлекаем реальные роли из базы
    user_roles = [r.role_type for r in user.roles]
    primary_role = user_roles[0] if user_roles else "user"

    # 4. Извлекаем должность/департамент (через таблицу Employee)
    job_name = "Не указана"
    try:
        employee_record = db.query(models.Employee).filter(models.Employee.person_id == user.id).first()
        if employee_record and getattr(employee_record, 'job_title_id', None):
            job_title = db.query(models.JobTitle).filter(models.JobTitle.id == employee_record.job_title_id).first()
            if job_title:
                job_name = job_title.name
    except Exception:
        db.rollback()

    # 5. Генерируем нормальный JWT с временем жизни
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "roles": user_roles}
    )
    
    # 6. Собираем ответ
    user_info = schemas.UserResponse(
        id=user.id,
        name=user.full_name,
        email=user.email,
        role=primary_role,
        phone=user.phone,
        department=job_name,
        is_active=True,
        is_approved=user.is_approved,
        created_at=user.created_at or datetime.now()
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": user_info
    }


@router.post("/register")
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    # 1. Проверка, существует ли уже пользователь с таким email
    existing = db.query(models.Person).filter(models.Person.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )
    
    # 2. Хешируем пароль
    hashed_pass = get_password_hash(data.password)
    
    # 3. Создаем неодобренного пользователя
    new_user = models.Person(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hashed_pass,
        requested_role=data.requested_role,
        is_approved=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "message": "Заявка на регистрацию успешно отправлена"}


@router.get("/pending", response_model=List[schemas.UserResponse])
def get_pending_users(
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(require_role("admin", "director"))
):
    # Получаем список неодобренных пользователей
    pending = db.query(models.Person).filter(models.Person.is_approved == False).all()
    res = []
    for u in pending:
        # В качестве роли передаем его requested_role для информирования админа
        res.append(schemas.UserResponse(
            id=u.id,
            name=u.full_name,
            email=u.email,
            role=u.requested_role or "warehouse",
            phone=u.phone,
            department="Ожидает одобрения",
            is_active=False,
            is_approved=False,
            created_at=u.created_at or datetime.now()
        ))
    return res


@router.post("/approve/{user_id}")
def approve_user(
    user_id: int,
    body: schemas.UserApproveRequest,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(require_role("admin", "director"))
):
    user = db.query(models.Person).filter(models.Person.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    if user.is_approved:
        return {"status": "success", "message": "Пользователь уже одобрен ранее"}
        
    # Находим или создаем роль в системе
    role_obj = db.query(models.Role).filter(models.Role.role_type == body.role).first()
    if not role_obj:
        role_obj = models.Role(role_type=body.role)
        db.add(role_obj)
        db.flush()
        
    # Привязываем роль
    db.execute(
        models.PersonRole.__table__.insert().values(
            person_id=user.id,
            role_id=role_obj.id
        )
    )
    
    # Находим или создаем должность
    job_title_name = body.job_title or "Сотрудник"
    job_title = db.query(models.JobTitle).filter(models.JobTitle.name == job_title_name).first()
    if not job_title:
        job_title = models.JobTitle(name=job_title_name)
        db.add(job_title)
        db.flush()
        
    # Создаем Employee запись
    employee = models.Employee(
        person_id=user.id,
        job_title_id=job_title.id,
        tabel_number=f"T-{user.id:04d}"
    )
    db.add(employee)
    
    # Одобряем и сохраняем изменения
    user.is_approved = True
    db.commit()
    
    return {"status": "success", "message": "Пользователь успешно одобрен"}


@router.delete("/reject/{user_id}")
def reject_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(require_role("admin", "director"))
):
    user = db.query(models.Person).filter(models.Person.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    if user.is_approved:
        raise HTTPException(status_code=400, detail="Нельзя отклонить уже одобренного пользователя")
        
    db.delete(user)
    db.commit()
    
    return {"status": "success", "message": "Заявка на регистрацию успешно отклонена"}