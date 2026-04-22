from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel

from database import get_db
import models, schemas
from auth_utils import get_current_user

router = APIRouter(prefix="/api/warehouse", tags=["Склад"])

# Вспомогательные схемы для ответов списков
class WarehouseListItem(BaseModel):
    id: int
    name: str

class ProductListItem(BaseModel):
    id: int
    name: str

# Хелпер для получения остатка конкретного товара на складе
def _get_or_create_stock(db: Session, warehouse_id: int, product_id: int) -> models.Stock:
    stock = db.query(models.Stock).filter(
        models.Stock.warehouse_id == warehouse_id,
        models.Stock.product_id == product_id
    ).first()
    
    if not stock:
        # Проверяем вообще существует ли склад и товар
        wh = db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()
        pr = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not wh or not pr:
            raise HTTPException(status_code=404, detail="Склад или товар не найден")
            
        stock = models.Stock(warehouse_id=warehouse_id, product_id=product_id, quantity=0.0)
        db.add(stock)
        db.flush()
    return stock

@router.get("/list", response_model=List[WarehouseListItem])
def get_warehouses(db: Session = Depends(get_db)):
    return db.query(models.Warehouse).all()

@router.get("/products", response_model=List[ProductListItem])
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@router.get("/status", response_model=schemas.WarehouseStatus)
def get_status(
    warehouse_id: int,
    product_id: int,
    db: Session = Depends(get_db),
    _: models.Person = Depends(get_current_user)
):
    stock = db.query(models.Stock).filter(
        models.Stock.warehouse_id == warehouse_id,
        models.Stock.product_id == product_id
    ).first()
    
    current_qty = float(stock.quantity) if stock else 0.0
    
    # Заглушки для уровней (в будущем их можно вынести в таблицу Warehouse)
    capacity = 5000.0
    crit = 500.0
    warn = 1000.0
    
    pct = round((current_qty / capacity) * 100) if capacity else 0
    if current_qty <= crit:
        st = "crit"
    elif current_qty <= warn:
        st = "warn"
    else:
        st = "ok"
        
    return schemas.WarehouseStatus(
        current_stock=current_qty,
        capacity=capacity,
        percent=pct,
        status=st
    )

@router.get("/operations")
def get_operations(
    warehouse_id: int,
    product_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: models.Person = Depends(get_current_user)
):
    ops = (
        db.query(models.InventoryOperation)
        .filter(
            models.InventoryOperation.warehouse_id == warehouse_id,
            models.InventoryOperation.product_id == product_id
        )
        .order_by(models.InventoryOperation.created_at.desc())
        .limit(limit)
        .all()
    )
    
    result = []
    for op in ops:
        r = schemas.PeatOperationResponse.model_validate(op).model_dump()
        r["employee_name"] = op.author.full_name if op.author else "—"
        r["source"] = op.description or ("Поставка" if op.operation_type == "in" else "Отгрузка")
        # В данной реализации мы не храним balance_after, поэтому отправляем просто кол-во:
        r["balance_after"] = op.amount # TODO: Можно добавить расчет
        result.append(r)
    return result

@router.post("/operations")
def add_operation(
    body: schemas.PeatOperationCreate,
    warehouse_id: int,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    stock = _get_or_create_stock(db, warehouse_id, product_id)

    if body.type == "in":
        stock.quantity = float(stock.quantity) + body.amount
    elif body.type == "out":
        if float(stock.quantity) < body.amount:
             raise HTTPException(status_code=400, detail="Недостаточно товара на складе")
        stock.quantity = float(stock.quantity) - body.amount
    else:
        raise HTTPException(status_code=400, detail="Тип операции: 'in' или 'out'")

    op = models.InventoryOperation(
        product_id=product_id,
        warehouse_id=warehouse_id,
        author_id=current_user.id,
        operation_type=body.type,
        amount=body.amount,
        description=body.description
    )
    
    db.add(op)
    db.commit()
    db.refresh(op)

    r = schemas.PeatOperationResponse.model_validate(op).model_dump()
    r["employee_name"] = current_user.full_name
    r["source"] = op.description or ("Поставка" if op.operation_type == "in" else "Отгрузка")
    r["balance_after"] = stock.quantity
    return r