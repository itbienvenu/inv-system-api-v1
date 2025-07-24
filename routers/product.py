from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File

from sqlalchemy.orm import Session

from database.models import Supplier

from schemas.product_schema import ProductInput, ProductImage, ProductOut,ProductUpdate

from database.get_db import get_db
from database import models
from datetime import datetime, UTC
from typing import List
from uuid import *
from auth.auth import get_current_user
import os, shutil, json, uuid

router = APIRouter(prefix="/api/v1", tags=["Product"])

@router.post("/register_product", dependencies=[Depends(get_current_user)])
async def register_product(
    product_name: str = Form(...),
    selling_price: float = Form(...),
    buying_price: float = Form(...),
    quantity: int = Form(...),
    category: str = Form(...),
    brand: str = Form(...),
    front_image: UploadFile = File(...),
    back_images: list[UploadFile] = File(...),
    description: str = Form(...),
    sku: str = Form(...),
    unit: str = Form(...),
    low_stock_alert: int = Form(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    # Check if SKU already exists
    check_sku = db.query(models.Product).filter(models.Product.sku == sku).first()
    if check_sku:
        raise HTTPException(status_code=400, detail=f"Product with sku {sku} already registered")

    # Create uploads folder
    folder_path = "static/images"
    os.makedirs(folder_path, exist_ok=True)

    # Save front image
    front_ext = os.path.splitext(front_image.filename)[1]
    front_filename = f"{uuid.uuid4().hex}{front_ext}"
    front_path = os.path.join(folder_path, front_filename)
    with open(front_path, "wb") as f:
        shutil.copyfileobj(front_image.file, f)

    # Save back images
    back_filenames = []
    for image in back_images:
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(folder_path, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        back_filenames.append(filename)

    # Save product
    new_product = models.Product(
        id=uuid4(),
        created_by=UUID(current_user),
        product_name=product_name,
        selling_price=selling_price,
        buying_price=buying_price,
        quantity=quantity,
        category=category,
        brand=brand,
        front_image=front_filename,
        back_image=json.dumps(back_filenames),
        description=description,
        sku=sku,
        unit=unit,
        low_stock_alert=low_stock_alert
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "status": "success",
        "message": f"Product Registered well",
        "data": {
            "name": product_name,
            "sku": sku
        }
    }
# getting a certian product info

@router.get("/api/v1/product/{product_id}", response_model=ProductOut, dependencies=[Depends(get_current_user)])
def view_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_dict = product.__dict__
    product_dict["back_image"] = json.loads(product.back_image)
    return product

#Listing All products

@router.get("/get_products", response_model=list[ProductOut], dependencies=[Depends(get_current_user)])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    product_list = []
    for p in products:
        try:
            p.back_image = json.loads(p.back_image)  # Convert from JSON string to list
        except Exception:
            p.back_image = []
        product_list.append(p)
    return product_list    

@router.put("/edit_product/{product_id}", response_model=ProductUpdate, dependencies=[Depends(get_current_user)])
def edit_product(
    product_id: UUID,
    updated_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id: {product_id} was not found")

    # Update fields only if provided in the request
    for field, value in updated_data.model_dump(exclude_unset=True).items():
        if field == "back_image" and value is not None:
            setattr(product, field, json.dumps(value))  # convert list to JSON string
        else:
            setattr(product, field, value)

    # Update last_modified automatically
    product.last_modified = datetime.now(UTC)
    

    db.commit()
    db.refresh(product)
    return updated_data
@router.delete("/delete_product/{product_id}",  dependencies=[Depends(get_current_user)])
async def delete_product(product_id: UUID, db: Session = Depends(get_db),):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message":"Product deleted well"}

