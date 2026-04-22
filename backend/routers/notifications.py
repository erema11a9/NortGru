from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas
from auth_utils import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Уведомления"])

@router.get("/", response_model=List[schemas.NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    notifs = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).limit(50).all()
    
    # Map message to msg for frontend layout
    for n in notifs:
        n.msg = n.message
        
    return notifs

@router.patch("/{notif_id}/read")
def read_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id,
        models.Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "ok"}

@router.post("/read-all")
def read_all_notifications(
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
