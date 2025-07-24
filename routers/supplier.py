from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.models import Supplier
from schemas.suppliers_schema import SupplierCreate, SupplierOut, SupplierUpdate
from database.get_db import get_db
from typing import List
from pydantic import EmailStr
from auth.auth import get_current_user
router = APIRouter(prefix="/api/v1/suppliers", tags=["Suppliers"])

@router.post("/", response_model=SupplierOut, dependencies=[Depends(get_current_user)])
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@router.get("/", response_model=List[SupplierOut], dependencies=[Depends(get_current_user)])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()

@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(supplier)
    db.commit()
    return {"detail": "Supplier deleted successfully"}

@router.put("/{supplier_id}", response_model=SupplierOut, dependencies=[Depends(get_current_user)])
def update_supplier(supplier_id: int, updates: SupplierUpdate, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)
    return supplier

@router.get("/by-email", response_model=SupplierOut, dependencies=[Depends(get_current_user)])
def get_supplier_by_email(email: EmailStr, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.email == email).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.get("/", response_model=List[SupplierOut], dependencies=[Depends(get_current_user)])
def get_suppliers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Supplier).offset(skip).limit(limit).all()

@router.get("/filter", response_model=List[SupplierOut], dependencies=[Depends(get_current_user)])
def filter_suppliers(status: str, db: Session = Depends(get_db)):
    results = db.query(Supplier).filter(Supplier.status == status.lower()).all()
    return results

@router.get("/search", response_model=List[SupplierOut], dependencies=[Depends(get_current_user)])
def search_suppliers(query: str, db: Session = Depends(get_db)):
    results = db.query(Supplier).filter(
        Supplier.name.ilike(f"%{query}%") |
        Supplier.contact_person.ilike(f"%{query}%")
    ).all()
    return results
