from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Contact as DBContact
from schemas import ContactCreate, Contact
from auth import get_current_active_user
from models import AdminUser

router = APIRouter()

@router.post("/", response_model=Contact)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact message"""
    # FIXED: Use database model (DBContact), not API schema (Contact)
    db_contact = DBContact(
        name=contact.name,
        email=contact.email,
        message=contact.message
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/", response_model=list[Contact])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all contact messages (admin only)"""
    contacts = db.query(DBContact).offset(skip).limit(limit).all()
    return contacts

@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: int,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific contact message"""
    contact = db.query(DBContact).filter(DBContact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}/read")
async def mark_contact_read(
    contact_id: int,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark contact as read"""
    contact = db.query(DBContact).filter(DBContact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_read = True
    db.commit()
    return {"message": "Contact marked as read"}

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a contact message"""
    contact = db.query(DBContact).filter(DBContact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}