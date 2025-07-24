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

from routers import supplier, sales, product, login
# ✅ Create all tables after all models are imported

models.Base.metadata.create_all(bind=engine)
load_dotenv()
app = FastAPI()

#Routers
sales_router = APIRouter(prefix="/sales", tags=["Sales"])
app.include_router(login.router)
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

