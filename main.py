from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from database.database import Base, engine, SessionLocal
from database.database import Base, engine
from database import  models
from routers import supplier, sales, product, login
import os

models.Base.metadata.create_all(bind=engine)
load_dotenv()
app = FastAPI(title="Inventory Managment System API")

#Routers
app.include_router(login.router)
app.include_router(supplier.router)
app.include_router(sales.router)
app.include_router(product.router)

app.mount("/static", StaticFiles(directory="static"), name="static") # Loding static images

# Managing cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  
)

# Config
@app.get("/api/v1/")
def index():
    return {"message":"Home page"}
