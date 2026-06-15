import os
import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy import text

from database import SessionLocal, engine, Base
import models

# Установка кодировки для Windows
os.environ['PGCLIENTENCODING'] = 'utf-8'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    print("=== Start database seeding for NortGru ===")
    
    # Сброс и создание таблиц
    print("Resetting database tables (DROP ALL with CASCADE)...")
    try:
        with engine.connect() as conn:
            tables_to_drop = [
                "person_roles", "roles", "notifications", "waybill_details", 
                "waybills", "waybill_routes", "waybill_technical_data", 
                "drivers", "vehicles", "employees", "job_titles", "stock", 
                "inventory_operations", "products", "warehouses", 
                "documents", "persons", "knowledge_items"
            ]
            for table in tables_to_drop:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            conn.commit()
        print("Existing tables dropped successfully with CASCADE.")
    except Exception as e:
        print(f"Warning during drop_all: {str(e)}")
        
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    db = SessionLocal()
    try:
        # 2. Создание Ролей
        print("Creating roles...")
        roles_list = ["admin", "director", "manager", "master", "warehouse"]
        roles_map = {}
        for r_name in roles_list:
            role = models.Role(role_type=r_name)
            db.add(role)
            db.flush()
            roles_map[r_name] = role
            
        # 3. Создание Должностей
        print("Creating job titles...")
        jobs_list = [
            "Администратор", 
            "Генеральный директор", 
            "Финансовый директор", 
            "Мастер-бригадир", 
            "Старший кладовщик",
            "Водитель-экспедитор"
        ]
        jobs_map = {}
        for j_name in jobs_list:
            job = models.JobTitle(name=j_name)
            db.add(job)
            db.flush()
            jobs_map[j_name] = job
            
        # 4. Создание Пользователей
        print("Creating users...")
        hashed_pass = pwd_context.hash("123")
        hashed_pass_1234 = pwd_context.hash("1234")
        hashed_demo_pass = pwd_context.hash("demo123")
        
        users_data = [
            {
                "full_name": "Еремин Дмитрий Сергеевич",
                "email": "dmitry.erema@mail.ru",
                "phone": "+7 (999) 111-22-33",
                "role": "admin",
                "job": "Администратор",
                "pass": hashed_pass
            },
            {
                "full_name": "Тимофеев Александр Николаевич",
                "email": "timofeev.dir@mail.ru",
                "phone": "+7 (999) 222-33-44",
                "role": "director",
                "job": "Генеральный директор",
                "pass": hashed_pass
            },
            {
                "full_name": "Смирнова Елена Викторовна",
                "email": "manager@nortgru.ru",
                "phone": "+7 (999) 333-44-55",
                "role": "manager",
                "job": "Финансовый директор",
                "pass": hashed_pass_1234
            },
            {
                "full_name": "Козлов Игорь Петрович",
                "email": "master@nortgru.ru",
                "phone": "+7 (999) 444-55-66",
                "role": "master",
                "job": "Мастер-бригадир",
                "pass": hashed_demo_pass
            },
            {
                "full_name": "Павлов Сергей Александрович",
                "email": "warehouse@nortgru.ru",
                "phone": "+7 (999) 555-66-77",
                "role": "warehouse",
                "job": "Старший кладовщик",
                "pass": hashed_demo_pass
            }
        ]
        
        users_map = {}
        for idx, u in enumerate(users_data):
            person = models.Person(
                full_name=u["full_name"],
                email=u["email"],
                phone=u["phone"],
                password_hash=u["pass"],
                is_approved=True,
                created_at=datetime.datetime.now() - datetime.timedelta(days=30)
            )
            db.add(person)
            db.flush()
            users_map[u["role"]] = person
            
            # Связываем роль
            db.execute(
                models.PersonRole.__table__.insert().values(
                    person_id=person.id, 
                    role_id=roles_map[u["role"]].id
                )
            )
            
            # Создаем запись Employee
            emp = models.Employee(
                person_id=person.id,
                job_title_id=jobs_map[u["job"]].id,
                tabel_number=f"T-{idx+1:04d}"
            )
            db.add(emp)
            db.flush()
            
        # 5. Создание Водителей (из числа сотрудников, добавим пару новых лиц)
        print("Creating drivers...")
        drivers_data = [
            {"name": "Ковалев Игорь Петрович", "license": "79 12 345678", "snils": "123-456-789 01", "email": "driver@nortgru.ru", "pass": "1234"},
            {"name": "Смирнов Алексей Владимирович", "license": "27 05 987654", "snils": "987-654-321 09", "email": "driver2@nortgru.ru", "pass": "demo123"},
            {"name": "Иванов Сергей Николаевич", "license": "79 10 112233", "snils": "111-222-333 44", "email": "driver3@nortgru.ru", "pass": "demo123"}
        ]
        
        drivers_list = []
        for idx, d_info in enumerate(drivers_data):
            p = models.Person(
                full_name=d_info["name"],
                email=d_info["email"],
                phone=f"+7 (914) 000-00-0{idx+1}",
                password_hash=pwd_context.hash(d_info["pass"]),
                is_approved=True
            )
            db.add(p)
            db.flush()
            
            # Привязываем роль warehouse
            db.execute(
                models.PersonRole.__table__.insert().values(
                    person_id=p.id, 
                    role_id=roles_map["warehouse"].id
                )
            )
            
            # Создаем employee
            emp = models.Employee(
                person_id=p.id,
                job_title_id=jobs_map["Водитель-экспедитор"].id,
                tabel_number=f"DR-{idx+1:03d}"
            )
            db.add(emp)
            db.flush()
            
            # Создаем driver
            driver = models.Driver(
                employee_id=emp.id,
                license_series_number=d_info["license"],
                license_issue_date=datetime.date.today() - datetime.timedelta(days=365*2),
                snils=d_info["snils"],
                license_card_reg_num=f"LC-{idx+1000}"
            )
            db.add(driver)
            db.flush()
            drivers_list.append(driver)
            
        # 6. Создание Складов
        print("Creating warehouses...")
        warehouses_data = [
            {"name": "Центральный хаб (Биробиджан)", "location": "г. Биробиджан, ул. Шолом-Алейхема, 115"},
            {"name": "Логистический терминал (Хабаровск)", "location": "г. Хабаровск, ул. Карла Маркса, 202"},
            {"name": "Запасной склад (Амурск)", "location": "г. Амурск, ул. Машиностроителей, 8"}
        ]
        warehouses_list = []
        for w in warehouses_data:
            wh = models.Warehouse(name=w["name"], location=w["location"])
            db.add(wh)
            db.flush()
            warehouses_list.append(wh)
            
        # 7. Создание Товаров (Продуктов)
        print("Creating products...")
        products_data = [
            {"name": "Торф кусковой верховой", "price": 1200.00},
            {"name": "Торф низинный фрезерный", "price": 950.00},
            {"name": "Обогащенный грунт 'NortPeat'", "price": 1850.00},
            {"name": "Жидкое органическое удобрение (Тип Б)", "price": 450.00}
        ]
        products_list = []
        for p in products_data:
            prod = models.Product(name=p["name"], price=p["price"])
            db.add(prod)
            db.flush()
            products_list.append(prod)
            
        # 8. Создание Остатков на Складах (Stock)
        print("Filling stock...")
        stocks_data = [
            # Центральный склад (Биробиджан)
            {"warehouse_idx": 0, "product_idx": 0, "qty": 3450.5},
            {"warehouse_idx": 0, "product_idx": 1, "qty": 1200.0},
            {"warehouse_idx": 0, "product_idx": 2, "qty": 850.0},
            {"warehouse_idx": 0, "product_idx": 3, "qty": 2300.0},
            # Логистический склад (Хабаровск)
            {"warehouse_idx": 1, "product_idx": 0, "qty": 1150.0},
            {"warehouse_idx": 1, "product_idx": 1, "qty": 980.5},
            {"warehouse_idx": 1, "product_idx": 2, "qty": 1400.0},
            {"warehouse_idx": 1, "product_idx": 3, "qty": 500.0},
            # Резервный склад (Амурск)
            {"warehouse_idx": 2, "product_idx": 0, "qty": 450.0},
            {"warehouse_idx": 2, "product_idx": 1, "qty": 200.0},
            {"warehouse_idx": 2, "product_idx": 2, "qty": 100.0},
            {"warehouse_idx": 2, "product_idx": 3, "qty": 50.0}
        ]
        for s in stocks_data:
            wh = warehouses_list[s["warehouse_idx"]]
            prod = products_list[s["product_idx"]]
            stock = models.Stock(
                warehouse_id=wh.id,
                product_id=prod.id,
                quantity=s["qty"],
                last_updated=datetime.datetime.now() - datetime.timedelta(hours=2)
            )
            db.add(stock)
            
        # 9. Создание Истории Операций (InventoryOperation / PeatOperation)
        print("Creating inventory operations history...")
        ops_data = [
            {"wh": 0, "prod": 0, "type": "in", "amt": 500.0, "desc": "Поставка от добывающей бригады N3", "days_ago": 1},
            {"wh": 0, "prod": 2, "type": "out", "amt": 120.0, "desc": "Передано дилеру ООО 'АгроГроу'", "days_ago": 2},
            {"wh": 1, "prod": 0, "type": "in", "amt": 350.0, "desc": "Приход с центрального склада (рейс N12)", "days_ago": 2},
            {"wh": 1, "prod": 1, "type": "out", "amt": 80.0, "desc": "Отгрузка клиенту 'Зеленый Сад'", "days_ago": 3},
            {"wh": 0, "prod": 3, "type": "in", "amt": 1000.0, "desc": "Производство новой партии жидкого удобрения", "days_ago": 4},
            {"wh": 2, "prod": 0, "type": "in", "amt": 150.0, "desc": "Резервное пополнение запасов", "days_ago": 5}
        ]
        for op in ops_data:
            wh = warehouses_list[op["wh"]]
            prod = products_list[op["prod"]]
            inv_op = models.InventoryOperation(
                product_id=prod.id,
                warehouse_id=wh.id,
                operation_type=op["type"],
                amount=op["amt"],
                description=op["desc"],
                created_at=datetime.datetime.now() - datetime.timedelta(days=op["days_ago"]),
                author_id=users_map["warehouse"].id
            )
            db.add(inv_op)
            
        # 10. Создание Транспорта (Vehicles)
        print("Creating vehicles...")
        vehicles_data = [
            {
                "brand": "Scania G400 Тягач", 
                "gov": "Е777КХ79", 
                "fuel": "Дизель", 
                "garage": "Г-01", 
                "payload": 25.0, 
                "mileage": 184500.0
            },
            {
                "brand": "KamAZ 6520 Самосвал", 
                "gov": "М432УТ27", 
                "fuel": "Дизель", 
                "garage": "Г-02", 
                "payload": 20.0, 
                "mileage": 95400.0
            },
            {
                "brand": "MAN TGS Самосвал", 
                "gov": "Х999АМ79", 
                "fuel": "Дизель", 
                "garage": "Г-03", 
                "payload": 24.0, 
                "mileage": 120200.0
            },
            {
                "brand": "GAZelle Next Фургон", 
                "gov": "О112РТ79", 
                "fuel": "Газ", 
                "garage": "Г-04", 
                "payload": 1.5, 
                "mileage": 45300.0
            }
        ]
        
        vehicles_list = []
        for v in vehicles_data:
            veh = models.Vehicle(
                brand=v["brand"],
                gov_number=v["gov"],
                osago_expiry=datetime.date.today() + datetime.timedelta(days=120),
                kasko_expiry=datetime.date.today() + datetime.timedelta(days=240),
                fuel_type=v["fuel"],
                garage_number=v["garage"],
                max_payload=v["payload"],
                current_mileage=v["mileage"],
                description="В рабочем состоянии, плановое ТО пройдено"
            )
            db.add(veh)
            db.flush()
            vehicles_list.append(veh)
            
        # 11. Создание Путевых Листов (Waybills & WaybillDetails)
        print("Creating waybills...")
        wb1 = models.Waybill(
            series_number="ПЛ-8801",
            date=datetime.date.today(),
            vehicle_id=vehicles_list[0].id, 
            driver_id=drivers_list[0].id, 
            is_1c_integrated=False,
            color_mark="active"
        )
        db.add(wb1)
        db.flush()
        
        wbd1 = models.WaybillDetail(
            waybill_id=wb1.id,
            route_from="Центральный хаб (Биробиджан)",
            route_to="Логистический терминал (Хабаровск)",
            odometer_start=184200.0,
            fuel_at_start=380.0,
            fuel_issued=250.0,
            fuel_type="Дизель"
        )
        db.add(wbd1)
        
        wb2 = models.Waybill(
            series_number="ПЛ-8765",
            date=datetime.date.today() - datetime.timedelta(days=1),
            vehicle_id=vehicles_list[1].id, 
            driver_id=drivers_list[1].id, 
            is_1c_integrated=True,
            color_mark="completed"
        )
        db.add(wb2)
        db.flush()
        
        wbd2 = models.WaybillDetail(
            waybill_id=wb2.id,
            route_from="Запасной склад (Амурск)",
            route_to="Логистический терминал (Хабаровск)",
            odometer_start=95100.0,
            odometer_end=95400.0,
            fuel_at_start=200.0,
            fuel_issued=150.0,
            fuel_at_return=110.0,
            fuel_handed_over=0.0,
            fuel_cost=11500.0,
            fuel_type="Дизель",
            spec_equipment_hours=2.0,
            engine_hours=8.0
        )
        db.add(wbd2)
        
        # 12. Создание Документов (Documents)
        print("Creating documents...")
        docs_data = [
            {
                "number": "ДОГ-104-26", 
                "type": "Договор поставки", 
                "emp": "Тимофеев А.Н.", 
                "status": "approved", 
                "extra": "Договор на поставку питательного грунта для АО 'ДальСад'. Объем: 2000 тонн."
            },
            {
                "number": "АКТ-582", 
                "type": "Акт инвентаризации", 
                "emp": "Павлов С.А.", 
                "status": "pending", 
                "extra": "Результаты плановой инвентаризации остатков торфа кускового на Центральном складе."
            },
            {
                "number": "Накл-9912", 
                "type": "Накладная ТОРГ-12", 
                "emp": "Смирнова Е.В.", 
                "status": "draft", 
                "extra": "Отгрузочная накладная для дилера ООО 'АгроХаб'. Сумма: 450,000 руб."
            }
        ]
        
        for d in docs_data:
            doc = models.Document(
                number=d["number"],
                document_type=d["type"],
                employee_name=d["emp"],
                status=d["status"],
                extra_data=d["extra"],
                created_at=datetime.datetime.now() - datetime.timedelta(days=1),
                created_by_id=users_map["director"].id
            )
            db.add(doc)
            
        # 13. Создание Уведомлений (Notifications)
        print("Creating notifications...")
        notifs_data = [
            {
                "title": "Новый путевой лист", 
                "msg": "Создан путевой лист ПЛ-8801 для тягача Scania (водитель Ковалев И.П.).", 
                "icon": "fas fa-truck-moving", 
                "tc": "tb"
            },
            {
                "title": "Критический остаток", 
                "msg": "Остаток 'Обогащенного грунта NortPeat' на складе в Амурске опустился ниже нормы (100 тонн).", 
                "icon": "fas fa-exclamation-triangle", 
                "tc": "tr2"
            },
            {
                "title": "Интеграция 1С успешна", 
                "msg": "Данные путевого листа ПЛ-8765 успешно выгружены в 1С:Предприятие.", 
                "icon": "fas fa-check-circle", 
                "tc": "tg"
            }
        ]
        
        for n in notifs_data:
            notif = models.Notification(
                user_id=users_map["admin"].id,
                title=n["title"],
                message=n["msg"],
                is_read=False,
                icon=n["icon"],
                tc=n["tc"],
                created_at=datetime.datetime.now()
            )
            db.add(notif)
            
        # 14. Создание статей Базы Знаний (KnowledgeItems)
        print("Creating knowledge base articles...")
        kb_articles = [
            {
                "title": "Регламент работы со складами торфа",
                "category": "Склады",
                "content": (
                    "Нормативные требования по складированию и учету торфа на объектах ООО «НОРД-ИСТ ГРУПП»:\n\n"
                    "1. **Прием сырья**:\n"
                    "   - Каждая входящая партия торфа должна сопровождаться товарно-транспортной накладной.\n"
                    "   - Проводится обязательный визуальный контроль влажности.\n"
                    "   - Объем фиксируется в тоннах и заносится в систему через форму «Приход» в течение 1 часа с момента разгрузки.\n\n"
                    "2. **Отгрузка и списание**:\n"
                    "   - Любое списание товара со склада (отгрузка дилерам, передача в производство) разрешено только при наличии путевого листа или расходного ордера.\n"
                    "   - В системе NortGru операция оформляется через кнопку «Расход».\n\n"
                    "3. **Техника безопасности**:\n"
                    "   - Запрещено хранить торф вблизи открытого огня или нагревательных приборов.\n"
                    "   - Температура буртов должна измеряться еженедельно. При превышении 50°C необходимо произвести перелопачивание сырья с целью предотвращения самовозгорания."
                )
            },
            {
                "title": "Инструкция по заполнению путевых листов",
                "category": "Транспорт",
                "content": (
                    "Правила оформления путевых листов (ПЛ) для водителей NortGru:\n\n"
                    "- **Начало смены**: Водитель обязан получить ПЛ у диспетчера перед выездом на маршрут. В листе фиксируются начальные показания одометра и объем топлива в баке.\n"
                    "- **Завершение рейса**: После возвращения в гараж фиксируются конечные показания одометра и фактический остаток топлива.\n"
                    "- **Оформление расхода**: Расчет расхода топлива производится автоматически в системе NortGru. Если водитель заправлялся в пути, чеки сдаются в бухгалтерию, а сумма и объем внесенного топлива заносятся в систему при закрытии путевого листа.\n"
                    "- **Списание груза**: Если рейс был связан с доставкой торфа со склада, при закрытии путевого листа необходимо указать массу перевезенного груза, чтобы система автоматически списала соответствующий объем со склада отправителя."
                )
            },
            {
                "title": "Инструкция по интеграции с 1С",
                "category": "1С Интеграция",
                "content": (
                    "Интеграция NortGru с 1С:Предприятие осуществляется через встроенный HTTP-сервис по протоколу MCP:\n\n"
                    "- **Публикация базы**: База 1С опубликована на веб-сервере по адресу `http://localhost:8081/InfoBase4/hs/edu-agent`.\n"
                    "- **Проверка связи**: Для проверки доступности 1С в интерфейсе чата MCP AI-помощника вы можете выполнить команду `ping_1c_service` (или нажать быструю кнопку «Проверить подключение»).\n"
                    "- **Выгрузка путевых листов**: Все завершенные путевые листы выгружаются в 1С в конце смены. Для этого в меню путевого листа нажмите кнопку «Интегрировать в 1С» или воспользуйтесь XML-экспортом.\n"
                    "- **Роли доступа**: Права на получение данных из 1С жестко разграничены по ролям: `admin` и `director` могут видеть финансовые показатели, `warehouse` видит остатки, `master` видит путевые листы водителей своей бригады."
                )
            },
            {
                "title": "Общая информация о компании NortGru",
                "category": "Общие правила",
                "content": (
                    "**ООО «НОРД-ИСТ ГРУПП» (NortGru)** — ведущий производитель и поставщик высококачественных торфяных грунтов и органических удобрений в Дальневосточном регионе РФ.\n\n"
                    "### Наши филиалы:\n"
                    "- **Главный офис и центральный склад**: г. Биробиджан, Еврейская автономная область.\n"
                    "- **Логистический центр и филиал сбыта**: г. Хабаровск, Хабаровский край.\n"
                    "- **Резервная база хранения**: г. Амурск.\n\n"
                    "### Основные виды продукции:\n"
                    "- Верховой кусковой торф (для улучшения структуры почв).\n"
                    "- Низинный фрезерный торф (высококонцентрированный органический субстрат).\n"
                    "- Питательные грунты серии «NortPeat».\n"
                    "- Гуминовые удобрения и жидкие экстракты.\n\n"
                    "### Контакты:\n"
                    "- **Общий email**: info@nortgru.ru\n"
                    "- **Горячая линия поддержки**: 8-800-555-35-35"
                )
            }
        ]
        
        for art in kb_articles:
            ki = models.KnowledgeItem(
                title=art["title"],
                category=art["category"],
                content=art["content"],
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            db.add(ki)
            
        db.commit()
        print("[SUCCESS] All data has been successfully imported into PostgreSQL database!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
