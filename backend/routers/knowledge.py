from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models, schemas
from auth_utils import get_current_user

router = APIRouter(prefix="/api/knowledge", tags=["База знаний"])

def check_write_permission(user: models.Person):
    user_roles = [r.role_type for r in user.roles]
    if not any(role in ["admin", "director", "manager"] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования базы знаний. Требуется роль Администратора, Директора или Менеджера."
        )

@router.get("/list", response_model=List[schemas.KnowledgeItemResponse])
def list_knowledge_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    query = db.query(models.KnowledgeItem)
    
    if category:
        query = query.filter(models.KnowledgeItem.category == category)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.KnowledgeItem.title.ilike(search_filter)) | 
            (models.KnowledgeItem.content.ilike(search_filter))
        )
        
    return query.order_by(models.KnowledgeItem.category, models.KnowledgeItem.title).all()

@router.get("/categories", response_model=List[str])
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    categories = db.query(models.KnowledgeItem.category).distinct().all()
    return [c[0] for c in categories if c[0]]

@router.get("/{item_id}", response_model=schemas.KnowledgeItemResponse)
def get_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    item = db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return item

@router.post("", response_model=schemas.KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_item(
    item_data: schemas.KnowledgeItemCreate,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    check_write_permission(current_user)
    
    item = models.KnowledgeItem(
        title=item_data.title,
        content=item_data.content,
        category=item_data.category
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/{item_id}", response_model=schemas.KnowledgeItemResponse)
def update_knowledge_item(
    item_id: int,
    item_data: schemas.KnowledgeItemCreate,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    check_write_permission(current_user)
    
    item = db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Статья не найдена")
        
    item.title = item_data.title
    item.content = item_data.content
    item.category = item_data.category
    
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    check_write_permission(current_user)
    
    item = db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Статья не найдена")
        
    db.delete(item)
    db.commit()
    return {"message": "Статья успешно удалена"}
