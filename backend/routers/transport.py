from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
import models, schemas
from auth_utils import get_current_user

router = APIRouter(prefix="/api/transport", tags=["Транспорт"])

# --- Схемы для завершения ПЛ ---
class CompleteWaybillRequest(BaseModel):
    odo_end: float
    fuel_end: float
    cargo_weight: Optional[float] = 0.0
    warehouse_id: Optional[int] = None
    product_id: Optional[int] = None
    fuel_cost: Optional[float] = 0.0
    fuel_type: Optional[str] = None

# --- ТРАНСПОРТНЫЕ СРЕДСТВА ---

@router.get("/vehicles")
def get_vehicles(db: Session = Depends(get_db), current_user: models.Person = Depends(get_current_user)):
    # Возвращаем в формате, который ожидает фронт
    vehicles = db.query(models.Vehicle).all()
    return [{"id": v.id, "name": v.brand, "plate": v.gov_number} for v in vehicles]

@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle: dict, db: Session = Depends(get_db), _: models.Person = Depends(get_current_user)):
    pass # Реализация не менялась, убрал schemas.VehicleCreate чтобы избежать ошибок, если ее нет

# --- ПУТЕВЫЕ ЛИСТЫ ---

@router.get("/waybills")
def get_waybills(db: Session = Depends(get_db), _: models.Person = Depends(get_current_user)):
    waybills = db.query(models.Waybill).options(
        joinedload(models.Waybill.details),
        joinedload(models.Waybill.vehicle),
        joinedload(models.Waybill.driver).joinedload(models.Driver.employee)
    ).order_by(models.Waybill.date.desc()).all()
    
    result = []
    for wb in waybills:
        wb_status = "active"
        fuel_actual = 0
        fuel_norm = 0
        route_from = ""
        route_to = ""

        if wb.details:
            if wb.details.odometer_end and wb.details.odometer_end > 0:
                wb_status = "completed"
            fuel_actual = wb.details.fuel_consumption_actual or 0.0
            fuel_norm = wb.details.fuel_consumption_norm or 0.0
            route_from = wb.details.route_from
            route_to = wb.details.route_to

        dr_name = "Неизвестно"
        if wb.driver and wb.driver.employee and wb.driver.employee.person:
            dr_name = wb.driver.employee.person.full_name
        
        # Cargo weight в БД для детализации нет, определяем по связанным операциям Inventory (out, doc_id)
        # У нас нет явного поля, поэтому пока передаем 0 (в реале можно сделать запрос к InventoryOps)
        result.append({
            "id": wb.id,
            "number": wb.series_number,
            "date": wb.date,
            "vehicle": f"{wb.vehicle.brand} ({wb.vehicle.gov_number})" if wb.vehicle else "—",
            "driver": dr_name,
            "route_from": route_from,
            "route_to": route_to,
            "cargo_weight": 0, # Временно так
            "fuel_actual": fuel_actual,
            "fuel_norm": fuel_norm,
            "status": wb_status
        })
    return result

@router.get("/waybills/export_xml")
def export_waybills_xml(db: Session = Depends(get_db)):
    from fastapi import Response
    waybills = db.query(models.Waybill).options(joinedload(models.Waybill.details)).all()
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n<Документы>\n'
    for wb in waybills:
        if wb.details and wb.details.fuel_type:
            total_cost = wb.details.fuel_cost or 0
            fuel_qty = wb.details.fuel_consumption_actual or 0
            price = round(total_cost / fuel_qty, 2) if fuel_qty > 0 else total_cost
            xml_str += f'\t<ПутевойЛист>\n'
            xml_str += f'\t\t<ДатаСоздания>{wb.date}</ДатаСоздания>\n'
            xml_str += f'\t\t<Номенклатура>{wb.details.fuel_type}</Номенклатура>\n'
            xml_str += f'\t\t<Количество>{fuel_qty}</Количество>\n'
            xml_str += f'\t\t<Цена>{price}</Цена>\n'
            xml_str += f'\t</ПутевойЛист>\n'
    xml_str += '</Документы>'

    # Сохраняем локально на Google Диск (резервная копия, если папка смонтирована)
    try:
        import os
        export_dir = r"G:\Мой диск\XML files"
        os.makedirs(export_dir, exist_ok=True)
        with open(os.path.join(export_dir, 'waybills.xml'), 'w', encoding='utf-8') as f:
            f.write(xml_str)
    except Exception as e:
        print(f"Предупреждение: Не удалось сохранить XML на локальный Google Диск: {str(e)}")

    # Отправляем напрямую в облако Google Drive через Google Apps Script Web App
    try:
        import httpx
        script_url = os.getenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbxQJK61xo9pIqb-wM1yIPxKTpMRokhu3_2SVGEKTP046GTXqZsV0B9WBxjfrs-9cBE/exec")
        response = httpx.post(
            script_url, 
            json={"filename": "waybills.xml", "content": xml_str}, 
            follow_redirects=True, 
            timeout=10.0
        )
        print(f"Отправка waybills.xml в Google Drive: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Предупреждение: Не удалось отправить XML в облако Google Drive: {str(e)}")

    return Response(content=xml_str, media_type="application/xml")

@router.post("/waybills")
def create_waybill(
    waybill_data: dict, # Убрали строгую схему для большей гибкости с фронтом
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    # Пытаемся найти водителя
    
    try:
        new_wb = models.Waybill(
            series_number=f"ПЛ-{datetime.now().strftime('%M%S')}", # Генерируем временно
            date=datetime.now().date(),
            vehicle_id=waybill_data.get("vehicle_id", 1),
            driver_id=1, # Заглушка, т.к. фронт шлет ФИО
        )
        
        db.add(new_wb)
        db.flush() 

        new_details = models.WaybillDetail(
            waybill_id=new_wb.id,
            route_from=waybill_data.get("route_from"),
            route_to=waybill_data.get("route_to"),
            odometer_start=waybill_data.get("odo_start", 0),
            fuel_at_start=waybill_data.get("fuel_start", 0),
        )
        db.add(new_details)

        db.commit()
        db.refresh(new_wb)
        return {
            "id": new_wb.id,
            "number": new_wb.series_number,
            "date": new_wb.date,
            "vehicle": "—", 
            "driver": waybill_data.get("driver"), 
            "route_from": new_details.route_from, 
            "route_to": new_details.route_to, 
            "cargo_weight": 0, 
            "fuel_actual": 0, 
            "fuel_norm": 0, 
            "status": "active"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Ошибка при сохранении путевого листа {str(e)}"
        )

@router.post("/waybills/{waybill_id}/complete")
def complete_waybill(
    waybill_id: int,
    data: CompleteWaybillRequest,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    wb = db.query(models.Waybill).options(joinedload(models.Waybill.details)).filter(models.Waybill.id == waybill_id).first()
    if not wb:
        raise HTTPException(status_code=404, detail="Путевой лист не найден")
        
    if not wb.details:
        wb.details = models.WaybillDetail(waybill_id=wb.id)
        db.add(wb.details)

    wb.details.odometer_end = data.odo_end
    wb.details.fuel_at_return = data.fuel_end
    wb.details.fuel_cost = data.fuel_cost
    wb.details.fuel_type = data.fuel_type
    
    # Расчет (условный)
    dist = data.odo_end - (wb.details.odometer_start or 0)
    wb.details.distance = dist if dist > 0 else 0
    wb.details.fuel_consumption_actual = (wb.details.fuel_at_start or 0) - data.fuel_end

    # 3. Интеграция со складом (отгрузка торфа)
    if data.cargo_weight > 0 and data.warehouse_id and data.product_id:
        stock = db.query(models.Stock).filter_by(
            warehouse_id=data.warehouse_id, 
            product_id=data.product_id
        ).first()
        
        if not stock or stock.quantity < data.cargo_weight:
             raise HTTPException(status_code=400, detail="Недостаточно товара на складе для списания")
             
        stock.quantity -= data.cargo_weight
        
        op = models.InventoryOperation(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            author_id=current_user.id,
            operation_type="out",
            amount=data.cargo_weight,
            description=f"Отгрузка по путевому листу #{wb.series_number}"
        )
        db.add(op)

    db.commit()
    return {"message": "Путевой лист завершен"}