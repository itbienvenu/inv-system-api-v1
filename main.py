from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, UploadFile, File, Form,Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles



from schemas.user_schema import Users, RegisterInput, UpdateInput, LoginInput, Roles
from schemas.sales_schema import SaleInput, ProductSold, PaymentMethod, SaleOut,SaleUpdateStatus
from schemas.suppliers_schema import SupplierCreate, SupplierOut


from database.get_db import get_db


from dotenv import load_dotenv
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date
from database.database import Base, engine, SessionLocal
from datetime import datetime, UTC, date
from utils.functions import generate_access_token, generate_hash, verify_password, decode_access_token
import os, shutil, json, uuid
import  json
from database.database import Base, engine
from typing import List, Optional

from database import  models

from auth.auth import get_current_user

from routers import supplier, sales, product
# ✅ Create all tables after all models are imported

models.Base.metadata.create_all(bind=engine)
load_dotenv()
app = FastAPI()

#Routers
sales_router = APIRouter(prefix="/sales", tags=["Sales"])
app.include_router(supplier.router)
app.include_router(sales.router)
app.include_router(product.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Managing cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  
)

# Config
SECRETE_KEY = os.getenv("SECRETE_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRES = os.getenv("ACCESS_TOKEN_EXPIRES")

# DB Session Dependency


@app.get("/api/v1/")
def index():
    return {
        "message": "Welcome to the Inventory & Sales API!",
        "version": "v1",
        "status": "online",
        "endpoints": {
            "authentication": "/api/v1/login",
            "create_sale": "/sell_product",
            "list_sales": "/sales",
            "sale_summary": "/sales/report/summary",
            "update_sale": "/sales/{sale_id}",
            "get_sale": "/sales/{sale_id}",
            "sale_document": "/sales/{sale_id}/document"
        },
        "documentation": "/docs"
    }



@app.get("/api/v1/ping")
def ping(user_id: int = Depends(get_current_user)):
    return {"status": "alive"}

@app.post("/api/v1/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if user and verify_password(form_data.password, user.password):
        data: dict = {
            "user_id": user.id,
            "names": user.names,
            "email": user.email,
            "phone": user.phone,
            "role": user.role
        }
        access_token = generate_access_token(data={"sub": str(user.id)})
        return {
            "message": "User logged in successfully",
            "user_data": data,
            "access_token": access_token,
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/api/v1/register")
def register_user(u: RegisterInput, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == u.email).first()
    if existing_user and (u.phone == existing_user.phone):
        raise HTTPException(status_code=401, detail="User Already Exists. Try Another Email")
    
    new_user = models.User(
        id=uuid4(),
        names=str(u.names),
        email=str(u.email),
        phone=int(u.phone),
        password=generate_hash(str(u.password)),
        role=",".join([r.value for r in u.role])
    )
    user_data: dict = {
        "user_id": new_user.id,
        "names": u.names,
        "email": u.email,
        "phone": u.phone,
        "role": u.role
    }
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User Registered Well", "user_data": user_data}



#Endpoint to display sale according to it ID

