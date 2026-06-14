from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# ─── СХЕМЫ АВТОРИЗАЦИИ ──────────────────────────────────────────────────

class UserBase(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    department: Optional[str] = None
    is_active: Optional[bool] = True
    is_approved: bool = False
    created_at: Optional[datetime] = None

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    requested_role: Optional[str] = "warehouse"

class UserApproveRequest(BaseModel):
    role: str
    job_title: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ─── СХЕМЫ СКЛАДА ──────────────────────────────────────────────────────

class WarehouseStatus(BaseModel):
    current_stock: float
    capacity: float
    percent: float
    status: str

    class Config:
        from_attributes = True

class PeatOperationCreate(BaseModel):
    type: str  # 'in' или 'out'
    amount: float
    description: Optional[str] = None

class PeatOperationResponse(PeatOperationCreate):
    id: int
    created_at: datetime
    author_id: int

    class Config:
        from_attributes = True

# ─── СХЕМЫ ТРАНСПОРТА ────────────────────────────────────────────────────

class WaybillDetailSchema(BaseModel):
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    odometer_start: float = 0.0
    odometer_end: float = 0.0
    fuel_at_start: float = 0.0
    fuel_issued: float = 0.0
    fuel_at_return: float = 0.0
    fuel_handed_over: float = 0.0
    fuel_cost: Optional[float] = 0.0
    fuel_type: Optional[str] = None
    spec_equipment_hours: Optional[float] = 0.0
    engine_hours: Optional[float] = 0.0
    fuel_consumption_actual: Optional[float] = 0.0
    fuel_consumption_norm: Optional[float] = 0.0
    work_hours: Optional[float] = 0.0
    break_hours: Optional[float] = 0.0
    distance: Optional[float] = 0.0

    class Config:
        from_attributes = True

class WaybillCreate(BaseModel):
    series_number: str
    date: date
    vehicle_id: int
    driver_id: int
    details: Optional[WaybillDetailSchema] = None

class WaybillResponse(BaseModel):
    id: int
    series_number: str
    date: date
    vehicle_id: int
    driver_id: int
    details: Optional[WaybillDetailSchema] = None

    class Config:
        from_attributes = True

# ─── СХЕМЫ ДОКУМЕНТОВ (ИСПРАВЛЕНО) ──────────────────────────────────────

class DocumentCreate(BaseModel):
    document_type: str
    employee_name: str
    extra_data: Optional[str] = None

class DocumentStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    title: str
    msg: str = None  # map 'message' to 'msg' for frontend compatibility if needed, but doing directly
    message: str
    is_read: bool
    icon: str
    tc: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    number: Optional[str] = None
    document_type: str
    employee_name: str
    status: str
    extra_data: Optional[str] = None
    created_at: datetime
    created_by_id: int 
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True

# ─── АНАЛИТИКА ─────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_documents: int
    pending_documents: int
    total_users: int
    current_stock: float
    waybills_today: int

    class Config:
        from_attributes = True

class AnalyticsData(BaseModel):
    monthly_labels: List[str]
    production: List[float]
    shipping: List[float]
    peat_consumption: List[float]
    peat_stock: List[float]
    total_production: float
    total_shipping: float
    total_peat: float
    efficiency: float

# ─── СХЕМЫ БАЗЫ ЗНАНИЙ ──────────────────────────────────────────────────

class KnowledgeItemBase(BaseModel):
    title: str
    content: str
    category: str

class KnowledgeItemCreate(KnowledgeItemBase):
    pass

class KnowledgeItemResponse(KnowledgeItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True