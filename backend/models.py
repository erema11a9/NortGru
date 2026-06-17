from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Text, Float, DateTime, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# 1. ПЕРСОНАЛ И ДОСТУП
class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    password_hash = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    requested_role = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    
    # Связи
    roles = relationship("Role", secondary="person_roles", back_populates="people")
    operations = relationship("InventoryOperation", back_populates="author")
    documents = relationship("Document", back_populates="created_by_user")

class JobTitle(Base):
    __tablename__ = "job_titles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"))
    job_title_id = Column(Integer, ForeignKey("job_titles.id"))
    tabel_number = Column(String(50), unique=True)
    
    person = relationship("Person")
    job_title = relationship("JobTitle")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_type = Column(String(50), nullable=False) # 'director', 'manager', 'master'
    people = relationship("Person", secondary="person_roles", back_populates="roles")

class PersonRole(Base):
    __tablename__ = "person_roles"
    person_id = Column(Integer, ForeignKey("persons.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

# 2. ТРАНСПОРТ
class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(100))
    gov_number = Column(String(20), unique=True)
    osago_expiry = Column(Date)
    kasko_expiry = Column(Date)
    fuel_type = Column(String(20))
    garage_number = Column(String(50))
    max_payload = Column(Float)
    current_mileage = Column(Float)
    description = Column(Text)
    
    waybills = relationship("Waybill", back_populates="vehicle")

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    license_series_number = Column(String(50))
    license_issue_date = Column(Date)
    snils = Column(String(20))
    license_card_reg_num = Column(String(50))
    
    employee = relationship("Employee")
    waybills = relationship("Waybill", back_populates="driver")

# 3. ПУТЕВЫЕ ЛИСТЫ И ДОКУМЕНТЫ
class Waybill(Base):
    __tablename__ = "waybills"
    id = Column(Integer, primary_key=True, index=True)
    series_number = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    is_1c_integrated = Column(Boolean, default=False)
    color_mark = Column(String(30))
    
    details = relationship("WaybillDetail", back_populates="waybill", uselist=False)
    vehicle = relationship("Vehicle", back_populates="waybills")
    driver = relationship("Driver", back_populates="waybills")

class WaybillDetail(Base):
    __tablename__ = "waybill_details"
    waybill_id = Column(Integer, ForeignKey("waybills.id", ondelete="CASCADE"), primary_key=True)
    route_from = Column(Text)
    route_to = Column(Text)
    odometer_start = Column(Float, default=0.0)
    odometer_end = Column(Float, default=0.0)
    fuel_at_start = Column(Float, default=0.0)
    fuel_issued = Column(Float, default=0.0)
    fuel_at_return = Column(Float, default=0.0)
    fuel_handed_over = Column(Float, default=0.0)
    fuel_cost = Column(Float, default=0.0)
    fuel_type = Column(String(50))
    spec_equipment_hours = Column(Float, default=0.0)
    engine_hours = Column(Float, default=0.0)
    
    waybill = relationship("Waybill", back_populates="details")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50))
    document_type = Column(String(50))
    employee_name = Column(String(255))
    status = Column(String(50), default="draft")
    extra_data = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    created_by_id = Column(Integer, ForeignKey("persons.id"))
    
    created_by_user = relationship("Person", back_populates="documents")

# 4. СКЛАД
class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    location = Column(Text)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # "Торф", "Удобрение тип А"
    price = Column(Numeric(10, 2))

class Stock(Base):
    __tablename__ = "stock"
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity = Column(Float, nullable=False, default=0.0)
    last_updated = Column(DateTime, default=datetime.now)

class InventoryOperation(Base):
    """ Модель операций (PeatOperation) """
    __tablename__ = "inventory_operations"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    operation_type = Column(String(10)) # 'in', 'out'
    amount = Column(Float, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    author_id = Column(Integer, ForeignKey("persons.id"))
    
    author = relationship("Person", back_populates="operations")
    __table_args__ = (CheckConstraint("operation_type IN ('in', 'out')"),)

# 5. УВЕДОМЛЕНИЯ
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("persons.id"))
    title = Column(String(255))
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    icon = Column(String(50), default="fas fa-bell")
    tc = Column(String(10), default="tb") # класс цвета иконки (tb, tg, tr, ty)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("Person")


# 6. БАЗА ЗНАНИЙ
class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

#--- Псевдонимы для удобства импорта ---
User = Person
PeatOperation = InventoryOperation