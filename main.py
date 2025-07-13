from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from schemas.user_schema import Users, RegisterInput, UpdateInput, LoginInput, Roles
from schemas.product_schema import ProductInput, ProductImage, ProductOut,ProductUpdate
from database import models
from dotenv import load_dotenv
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from database.database import Base, engine, SessionLocal
from datetime import datetime, UTC
from utils.functions import generate_access_token, generate_hash, verify_password, decode_access_token
import os
import  json


# ✅ Create all tables after all models are imported

models.Base.metadata.create_all(bind=engine)
load_dotenv()
router = APIRouter()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
    return user_id

# Config
SECRETE_KEY = os.getenv("SECRETE_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRES = os.getenv("ACCESS_TOKEN_EXPIRES")

# DB Session Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def index():
    return {"message":"Viewing the home page"}

from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if user and verify_password(form_data.password, user.password):
        data: dict = {
            "user_id": user.id,
            "names": user.names,
            "email": user.email,
            "phone": user.phone
        }
        access_token = generate_access_token(data={"sub": str(user.id)})
        return {
            "message": "User logged in successfully",
            "user_data": data,
            "access_token": access_token,
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/register", dependencies=[Depends(get_current_user)])
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



@app.post("/register_product", dependencies=[Depends(get_current_user)])
def register_product(p: ProductInput, db: Session = Depends(get_db)):
    
    """
    Registering new product into database
    """
    check_sku = db.query(models.Product).filter(models.Product.sku == p.sku).first()
    if(check_sku):
        return {"status":"failed", "message":f"Product with sku {p.sku} alredy registered"}
    new_product = models.Product(
        id=uuid4(),
        created_by=p.created_by,
        product_name = p.product_name,
        selling_price = p.selling_price,
        buying_price = p.buying_price,
        quantity = int(p.quantity),
        category = str(p.category),
        brand = str(p.brand),
        front_image = str(p.image.front_image),
        back_image=json.dumps(p.image.other_images),
        description = str(p.description),
        sku = str(p.sku),
        unit = str(p.unit),
        low_stock_alert = int(p.low_stock_alert)
    )
    product_data: dict = {
        "name":p.product_name,
        "sku":p.sku

    }
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"status":"success","message":f"Product Registered well", "data":product_data}

# getting a certian product info

@app.get("/product/{product_id}", response_model=ProductOut, dependencies=[Depends(get_current_user)])
def view_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_dict = product.__dict__
    product_dict["back_image"] = json.loads(product.back_image)
    return product

#Listing All products

@app.get("/get_products", response_model=list[ProductOut], dependencies=[Depends(get_current_user)])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    for p in products:
        try:
            p.back_image = p.back_image.split(",")
        except:
            p.back_image = []
    return products        

@app.put("/edit_product/{product_id}", response_model=ProductUpdate, dependencies=[Depends(get_current_user)])
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
    if updated_data.sku and updated_data.sku == product.sku:
        raise HTTPException(status_code=400, detail="Try to use another SKU code")

    db.commit()
    db.refresh(product)
    return updated_data
@app.delete("/delete_product/{product_id}",  dependencies=[Depends(get_current_user)])
async def delete_product(product_id: UUID, db: Session = Depends(get_db),):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message":"Product deleted well"}