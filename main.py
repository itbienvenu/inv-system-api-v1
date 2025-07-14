from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from schemas.user_schema import Users, RegisterInput, UpdateInput, LoginInput, Roles
from schemas.product_schema import ProductInput, ProductImage, ProductOut,ProductUpdate
from schemas.sales_schema import SaleInput, ProductSold, PaymentMethod
from database import models
from dotenv import load_dotenv
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from database.database import Base, engine, SessionLocal
from datetime import datetime, UTC
from utils.functions import generate_access_token, generate_hash, verify_password, decode_access_token
import os, shutil, json, uuid
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

@app.post("/api/v1/login")
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

@app.post("/register")
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



@app.post("/api/v1/register_product", dependencies=[Depends(get_current_user)])
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
    created_by: UUID = Form(...),
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

@app.get("/api/v1/product/{product_id}", response_model=ProductOut, dependencies=[Depends(get_current_user)])
def view_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_dict = product.__dict__
    product_dict["back_image"] = json.loads(product.back_image)
    return product

#Listing All products

@app.get("/api/v1/get_products", response_model=list[ProductOut], dependencies=[Depends(get_current_user)])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    for p in products:
        try:
            p.back_image = p.back_image.split(",")
        except:
            p.back_image = []
    return products        

@app.put("/api/v1/edit_product/{product_id}", response_model=ProductUpdate, dependencies=[Depends(get_current_user)])
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
@app.delete("/api/v1/delete_product/{product_id}",  dependencies=[Depends(get_current_user)])
async def delete_product(product_id: UUID, db: Session = Depends(get_db),):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message":"Product deleted well"}

@app.post("/sell_product", dependencies=[Depends(get_current_user)])
async def sell_product(
    sale_data: SaleInput,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    """
    Process a sale transaction with multiple products.
    """
    try:
        # Validate products and calculate totals
        subtotal = 0.0
        products_to_sell = []
        
        for product in sale_data.products:
            # Check product availability
            db_product = db.query(models.Product).filter(models.Product.id == product.product_id).first()
            if not db_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product.product_id} not found"
                )
            
            if db_product.quantity < product.quantity_sold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product {db_product.product_name}. Available: {db_product.quantity}"
                )
            
            # Calculate product total
            product_total = product.selling_price * product.quantity_sold
            subtotal += product_total
            
            # Prepare product data for sale
            products_to_sell.append({
                "product_id": product.product_id,
                "product_name": db_product.product_name,
                "quantity_sold": product.quantity_sold,
                "selling_price": product.selling_price,
                "cost_price": db_product.buying_price  # Capture cost price at time of sale
            })
        
        # Calculate final total (including discounts/taxes if applicable)
        total_discount = sale_data.total_discount or 0.0
        taxes = sale_data.taxes or 0.0
        total = subtotal - total_discount + taxes
        
        # Create the sale record
        db_sale = SaleInput(
            id=uuid4(),
            buyer_name=sale_data.buyer_name,
            buyer_phone=sale_data.buyer_phone,
            buyer_email=sale_data.buyer_email,
            payment_method=sale_data.payment_method.value,  # Using enum value
            payment_reference=sale_data.payment_reference,
            subtotal=subtotal,
            total_discount=total_discount,
            taxes=taxes,
            total=total,
            currency=sale_data.currency,
            sold_by=current_user.id,
            location_id=sale_data.location_id,
            device_id=sale_data.device_id,
            status="completed",
            notes=sale_data.notes,
            sold_at=datetime.now(UTC)
        )
        
        db.add(db_sale)
        db.flush()  # Flush to get the sale ID for product records
        
        # Create product sold records and update inventory
        for product in products_to_sell:
            # Record sold product
            db_product_sold = ProductSold(
                sale_id=db_sale.id,
                product_id=product["product_id"],
                product_name=product["product_name"],
                quantity_sold=product["quantity_sold"],
                selling_price=product["selling_price"],
                cost_price=product["cost_price"]
            )
            db.add(db_product_sold)
            
            # Update inventory
            db_product = db.query(models.Product).filter(models.Product.id == product["product_id"]).first()
            db_product.quantity -= product["quantity_sold"]
            db.add(db_product)
        
        db.commit()
        
        return {
            "message": "Sale completed successfully",
            "sale_id": str(db_sale.id),
            "total": total
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing sale: {str(e)}"
        )