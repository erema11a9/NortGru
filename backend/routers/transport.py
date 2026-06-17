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
    vehicles = db.query(models.Vehicle).all()
    # Возвращаем полные объекты с сохранением совместимости с именами полей
    return [
        {
            "id": v.id,
            "brand": v.brand,
            "gov_number": v.gov_number,
            "name": v.brand,
            "plate": v.gov_number,
            "fuel_type": v.fuel_type,
            "garage_number": v.garage_number,
            "max_payload": v.max_payload,
            "current_mileage": v.current_mileage,
            "description": v.description
        }
        for v in vehicles
    ]

@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle_data: dict, db: Session = Depends(get_db), _: models.Person = Depends(get_current_user)):
    try:
        new_v = models.Vehicle(
            brand=vehicle_data.get("brand"),
            gov_number=vehicle_data.get("gov_number"),
            fuel_type=vehicle_data.get("fuel_type", "ДТ"),
            garage_number=vehicle_data.get("garage_number"),
            max_payload=float(vehicle_data.get("max_payload", 0.0) or 0.0),
            current_mileage=float(vehicle_data.get("current_mileage", 0.0) or 0.0),
            description=vehicle_data.get("description", "")
        )
        db.add(new_v)
        db.commit()
        db.refresh(new_v)
        return {
            "id": new_v.id,
            "brand": new_v.brand,
            "gov_number": new_v.gov_number,
            "name": new_v.brand,
            "plate": new_v.gov_number,
            "fuel_type": new_v.fuel_type,
            "garage_number": new_v.garage_number,
            "max_payload": new_v.max_payload,
            "current_mileage": new_v.current_mileage,
            "description": new_v.description
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании транспортного средства: {str(e)}"
        )

# --- ПУТЕВЫЕ ЛИСТЫ ---

@router.get("/waybills")
def get_waybills(db: Session = Depends(get_db), _: models.Person = Depends(get_current_user)):
    # ── Background Auto-Sync: From approved waybill Documents to Waybill journal ──
    try:
        import json
        import re
        from datetime import datetime
        
        approved_docs = db.query(models.Document).filter(
            models.Document.document_type == "waybill",
            models.Document.status == "approved"
        ).all()
        
        synced_any = False
        for doc in approved_docs:
            extra = {}
            if doc.extra_data:
                try:
                    extra = json.loads(doc.extra_data)
                except Exception:
                    pass
            
            series_num = extra.get("series_number") or doc.number
            
            # Check if Waybill already exists in the database
            wb_exists = db.query(models.Waybill).filter(models.Waybill.series_number == series_num).first()
            if not wb_exists:
                # 1. Match Vehicle
                vehicle_str = extra.get("vehicle")
                vehicle = None
                if vehicle_str:
                    vehicle = db.query(models.Vehicle).filter(
                        (models.Vehicle.gov_number == vehicle_str) | 
                        (models.Vehicle.brand == vehicle_str)
                    ).first()
                    if not vehicle:
                        match = re.search(r'[A-Za-zА-Яа-я0-9-]{5,10}', vehicle_str)
                        if match:
                            clean_num = match.group(0)
                            vehicle = db.query(models.Vehicle).filter(
                                models.Vehicle.gov_number.ilike(f"%{clean_num}%")
                            ).first()
                if not vehicle:
                    vehicle = db.query(models.Vehicle).first()
                
                # 2. Match Driver
                driver_name = extra.get("driver") or doc.employee_name
                driver = None
                if driver_name:
                    surname = driver_name.split()[0] if driver_name.split() else ""
                    if surname:
                        person = db.query(models.Person).filter(models.Person.full_name.ilike(f"%{surname}%")).first()
                        if person:
                            employee = db.query(models.Employee).filter(models.Employee.person_id == person.id).first()
                            if employee:
                                driver = db.query(models.Driver).filter(models.Driver.employee_id == employee.id).first()
                if not driver:
                    driver = db.query(models.Driver).first()
                
                # 3. Create Waybill
                wb_date = doc.created_at.date() if doc.created_at else datetime.now().date()
                new_wb = models.Waybill(
                    series_number=series_num,
                    date=wb_date,
                    vehicle_id=vehicle.id if vehicle else 1,
                    driver_id=driver.id if driver else 1,
                    color_mark="active",
                    is_1c_integrated=False
                )
                db.add(new_wb)
                db.flush()
                
                # 4. Create WaybillDetail
                new_details = models.WaybillDetail(
                    waybill_id=new_wb.id,
                    route_from=extra.get("route_from") or "—",
                    route_to=extra.get("route_to") or "—",
                    odometer_start=float(extra.get("odo_start") or 0.0),
                    odometer_end=float(extra.get("odo_end") or 0.0),
                    fuel_at_start=float(extra.get("fuel_start") or 0.0),
                    fuel_issued=float(extra.get("fuel_issued") or 0.0),
                    fuel_at_return=float(extra.get("fuel_handed_over") or 0.0),
                    fuel_cost=float(extra.get("fuel_cost") or 0.0),
                    fuel_type=extra.get("fuel_mark") or "ДТ"
                )
                db.add(new_details)
                synced_any = True
        
        if synced_any:
            db.commit()
            
    except Exception as e:
        db.rollback()
        print(f"Ошибка фоновой автосинхронизации одобренных путевых листов в транспорт: {str(e)}")

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
        db.flush()

        # Получаем информацию о ТС
        vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == new_wb.vehicle_id).first()
        vehicle_str = f"{vehicle.brand} ({vehicle.gov_number})" if vehicle else "—"

        # Создаем документ путевого листа в таблице документов для синхронизации
        import json
        extra_data = {
            "series_number": new_wb.series_number,
            "vehicle": vehicle_str,
            "driver": waybill_data.get("driver", "—"),
            "route_from": new_details.route_from or "—",
            "route_to": new_details.route_to or "—",
            "odo_start": new_details.odometer_start,
            "fuel_start": new_details.fuel_at_start,
            "distance_km": 0,
            "fuel_issued": new_details.fuel_at_start,
            "fuel_handed_over": 0,
            "fuel_cost": 0,
            "fuel_mark": "ДТ",
            "departure_time": datetime.now().isoformat(),
            "arrival_time": ""
        }

        doc_count = db.query(models.Document).filter(
            models.Document.document_type == "waybill"
        ).count() + 1
        doc_number = f"ТМ-2026-{str(doc_count).zfill(3)}"

        new_doc = models.Document(
            number=doc_number,
            document_type="waybill",
            employee_name=waybill_data.get("driver", "—"),
            status="draft",  # Начальный статус путевого листа
            created_by_id=current_user.id,
            extra_data=json.dumps(extra_data, ensure_ascii=False)
        )
        db.add(new_doc)

        db.commit()
        db.refresh(new_wb)
        return {
            "id": new_wb.id,
            "number": new_wb.series_number,
            "date": new_wb.date,
            "vehicle": vehicle_str, 
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

    # Также обновим связанный документ в таблице documents, если он есть
    try:
        import json
        doc = db.query(models.Document).filter(
            models.Document.document_type == "waybill",
            models.Document.extra_data.like(f'%"{wb.series_number}"%')
        ).first()
        if doc:
            extra = json.loads(doc.extra_data) if doc.extra_data else {}
            extra["odo_end"] = data.odo_end
            extra["fuel_handed_over"] = data.fuel_end
            extra["fuel_cost"] = data.fuel_cost
            extra["fuel_type"] = data.fuel_type
            extra["distance_km"] = float(data.odo_end - (wb.details.odometer_start or 0))
            extra["fuel_issued"] = float(wb.details.fuel_at_start or 0.0)
            
            # Вычислим стоимость топлива, если введена цена за литр
            price = float(extra.get("fuel_price") or 0.0)
            issued = float(extra.get("fuel_issued") or 0.0)
            if price > 0:
                extra["fuel_cost"] = round(issued * price, 2)
                
            doc.extra_data = json.dumps(extra, ensure_ascii=False)
            doc.status = "approved"  # Раз рейс завершен, документ автоматически согласован
    except Exception as ex:
        print(f"Ошибка синхронизации путевого листа в документы: {str(ex)}")

    db.commit()
    return {"message": "Путевой лист завершен"}