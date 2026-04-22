from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date
import calendar

from database import get_db
import models, schemas
from auth_utils import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Аналитика"])

_MONTH_LABELS = ["Янв","Фев","Мар","Апр","Май","Июн",
                 "Июл","Авг","Сен","Окт","Ноя","Дек"]

@router.get("/", response_model=schemas.AnalyticsData)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    user_roles = [r.role_type for r in current_user.roles]
    if not any(role in ["admin", "director", "manager"] for role in user_roles):
        raise HTTPException(status_code=403, detail="Недостаточно прав для просмотра аналитики")

    current_year = date.today().year

    # 1. Считаем фактические поступления по месяцам (operation_type = 'in')
    in_stats = db.query(
        extract('month', models.InventoryOperation.created_at).label('month'),
        func.sum(models.InventoryOperation.amount).label('total')
    ).filter(
        extract('year', models.InventoryOperation.created_at) == current_year,
        models.InventoryOperation.operation_type == 'in'
    ).group_by('month').all()

    # 2. Считаем фактические отгрузки (operation_type = 'out')
    out_stats = db.query(
        extract('month', models.InventoryOperation.created_at).label('month'),
        func.sum(models.InventoryOperation.amount).label('total')
    ).filter(
        extract('year', models.InventoryOperation.created_at) == current_year,
        models.InventoryOperation.operation_type == 'out'
    ).group_by('month').all()

    # Подготавливаем массивы (12 месяцев) на основе текущего года
    production = [0.0] * 12
    shipping = [0.0] * 12

    for row in in_stats:
        month_idx = int(row.month) - 1
        if 0 <= month_idx < 12:
            production[month_idx] = float(row.total)

    for row in out_stats:
        month_idx = int(row.month) - 1
        if 0 <= month_idx < 12:
            shipping[month_idx] = float(row.total)

    total_production = sum(production)
    total_shipping = sum(shipping)

    # 3. Общий остаток на текущий момент (для графика или KPI)
    total_stock = float(db.query(func.sum(models.Stock.quantity)).scalar() or 0.0)

    return schemas.AnalyticsData(
        monthly_labels=_MONTH_LABELS,
        production=production,
        shipping=shipping,
        peat_consumption=shipping, # Условно
        peat_stock=[total_stock] * 12, # Заглушка, надо считать исторически
        total_production=total_production,
        total_shipping=total_shipping,
        total_peat=total_stock,
        efficiency=round((total_shipping / total_production * 100), 1) if total_production > 0 else 0.0,
    )

@router.get("/dashboard", response_model=schemas.DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    total_stock = float(db.query(func.sum(models.Stock.quantity)).scalar() or 0.0)

    today = date.today()
    today_waybills = db.query(models.Waybill).filter(models.Waybill.date == today).count()
    total_people = db.query(models.Person).count()
    pending_docs = db.query(models.Document).filter(models.Document.status == "pending").count()

    return schemas.DashboardStats(
        total_documents=db.query(models.Document).count(),
        pending_documents=pending_docs,
        total_users=total_people,
        current_stock=total_stock,
        waybills_today=today_waybills,
    )