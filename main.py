from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, UploadFile, File, Form,Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from schemas.user_schema import Users, RegisterInput, UpdateInput, LoginInput, Roles
from schemas.product_schema import ProductInput, ProductImage, ProductOut,ProductUpdate
from schemas.sales_schema import SaleInput, ProductSold, PaymentMethod, SaleOut,SaleUpdateStatus
from database import models
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


# ✅ Create all tables after all models are imported

models.Base.metadata.create_all(bind=engine)
load_dotenv()
sales_router = APIRouter(prefix="/sales", tags=["Sales"])
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

# Managing cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  
)

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


from fastapi.security import OAuth2PasswordRequestForm

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
    product_list = []
    for p in products:
        try:
            p.back_image = json.loads(p.back_image)  # Convert from JSON string to list
        except Exception:
            p.back_image = []
        product_list.append(p)
    return product_list    

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

@app.post("/api/v1/sell_product", dependencies=[Depends(get_current_user)])
async def sell_product(
    sale_data: SaleInput,
    db: Session = Depends(get_db),
    current_user: UUID = Depends(get_current_user)  # Return UUID only from get_current_user
):
    """
    Process a sale transaction with multiple products.
    """
    try:
        # Validate and calculate
        subtotal = 0.0
        products_to_sell = []

        for product in sale_data.products:
            db_product = db.query(models.Product).filter(models.Product.id == product.product_id).first()
            if not db_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product.product_id} not found"
                )
            if db_product.quantity < product.quantity_sold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product '{db_product.product_name}'. Available: {db_product.quantity}"
                )
            
            product_total = product.selling_price * product.quantity_sold
            subtotal += product_total - product.discount

            products_to_sell.append({
                "product_id": product.product_id,
                "product_name": db_product.product_name,
                "quantity_sold": product.quantity_sold,
                "selling_price": product.selling_price,
                "cost_price": db_product.buying_price,
                "discount": product.discount
            })

        # Final totals
        total_discount = sale_data.total_discount or 0.0
        taxes = sale_data.taxes or 0.0
        total = subtotal - total_discount + taxes

        # Create sale DB model
        db_sale = models.Sale(
            id=uuid4(),
            buyer_name=sale_data.buyer_name,
            buyer_phone=sale_data.buyer_phone,
            buyer_email=sale_data.buyer_email,
            payment_method=sale_data.payment_method.name.upper(),
            payment_reference=sale_data.payment_reference,
            subtotal=subtotal,
            total_discount=total_discount,
            taxes=taxes,
            total=total,
            currency=sale_data.currency,
            sold_by=UUID(current_user),
            notes=sale_data.notes,
            status="completed".upper(),
            sold_at=sale_data.sold_at or datetime.now(UTC)
        )

        db.add(db_sale)
        db.flush()  # To get sale ID

        # Insert sold products and update stock
        for p in products_to_sell:
            db_product_sold = models.ProductSold(
                sale_id=db_sale.id,
                product_id=p["product_id"],
                product_name=p["product_name"],
                quantity_sold=p["quantity_sold"],
                selling_price=p["selling_price"],
                cost_price=p["cost_price"],
                discount=p["discount"]
            )
            db.add(db_product_sold)

            db_product = db.query(models.Product).filter(models.Product.id == p["product_id"]).first()
            db_product.quantity -= p["quantity_sold"]
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

#Endpoint to display sale according to it ID

@app.get("/api/v1/sales/{sale_id}", response_model=SaleOut, dependencies=[Depends(get_current_user)])
def get_sale(sale_id: UUID, db: Session = Depends(get_db)):
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    products = db.query(models.ProductSold).filter(models.ProductSold.sale_id == sale_id).all()
    return SaleOut(
        **sale.__dict__,
        products=products
    )

#Endpoint to display all sales

@app.get("/api/v1/sales", response_model=List[SaleOut], dependencies=[Depends(get_current_user)])
def get_all_sales(db: Session = Depends(get_db)):
    sales = db.query(models.Sale).all()

    result = []
    for sale in sales:
        sold_products = db.query(models.ProductSold).filter(models.ProductSold.sale_id == sale.id).all()
        sale_out = SaleOut(
            **sale.__dict__,
            products=sold_products
        )
        result.append(sale_out)
    return result

#Endpoint to delete the sale by it ID

@app.delete("/api/v1/sales/{sale_id}", dependencies=[Depends(get_current_user)])
def delete_sale(sale_id: UUID, db: Session = Depends(get_db)):
    """
    Deleting the sale by its id
    """
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    db.delete(sale)
    db.commit()
    return {"message": "Sale deleted successfully"}

#Endpoint to  create sales order document, but here will return just json,forn end will deal with wich document to export
@app.get("/api/v1/sales/{sale_id}/document", dependencies=[Depends(get_current_user)])
async def generate_sales_document(sale_id: UUID, db: Session = Depends(get_db)):
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invalid sale ID")

    # Optionally include sold products
    sold_products = db.query(models.ProductSold).filter(models.ProductSold.sale_id == sale_id).all()

    response = {
        "sale": jsonable_encoder(sale),
        "products": jsonable_encoder(sold_products)
    }

    return response

#Endpoint to edit sale

@app.put("/api/v1/sales/{sale_id}", dependencies=[Depends(get_current_user)])
def update_sale_status(
    sale_id: UUID,
    update_data: SaleUpdateStatus,
    db: Session = Depends(get_db)
):
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    sale.status = update_data.status.value.lower()
    db.commit()
    return {"message": f"Sale status updated to {sale.status}"}


# filter sales by seller

@app.get("/api/v1/sales/by_seller/{seller_id}", dependencies=[Depends(get_current_user)])
def get_sales_by_seller(seller_id: UUID, db: Session = Depends(get_db)):
    sales = db.query(models.Sale).filter(models.Sale.sold_by == seller_id).all()
    if not sales:
        raise HTTPException(status_code=404, detail="No sales found for this seller")
    
    return sales

@app.get("/api/v1/sales/report/summary", dependencies=[Depends(get_current_user)])
def get_sales_summary(
    db: Session = Depends(get_db),
    date_from: date = Query(None, description="Filter sales from this date (YYYY-MM-DD)"),
    date_to: date = Query(None, description="Filter sales up to this date (YYYY-MM-DD)")
):
    # Build base query
    sales_query = db.query(models.Sale)
    products_query = db.query(models.ProductSold)

    if date_from:
        sales_query = sales_query.filter(cast(models.Sale.sold_at, Date) >= date_from)
        products_query = products_query.join(models.Sale).filter(cast(models.Sale.sold_at, Date) >= date_from)

    if date_to:
        sales_query = sales_query.filter(cast(models.Sale.sold_at, Date) <= date_to)
        products_query = products_query.join(models.Sale).filter(cast(models.Sale.sold_at, Date) <= date_to)

    # Metrics
    total_sales = sales_query.count()
    total_revenue = sales_query.with_entities(func.sum(models.Sale.total)).scalar() or 0.0
    total_taxes = sales_query.with_entities(func.sum(models.Sale.taxes)).scalar() or 0.0
    total_profit = products_query.with_entities(func.sum(models.ProductSold.selling_price - models.ProductSold.cost_price)).scalar() or 0.0

    pending_sales = sales_query.filter(models.Sale.status == "pending").count()
    completed_sales = sales_query.filter(models.Sale.status == "completed").count()
    refunded_sales = sales_query.filter(models.Sale.status == "refunded").count()
    partial_refunded_sales = sales_query.filter(models.Sale.status == "partially_refunded").count()

    # Most sold product
    top_product = products_query.with_entities(
        models.ProductSold.product_name,
        func.sum(models.ProductSold.quantity_sold).label("total_sold")
    ).group_by(models.ProductSold.product_name).order_by(desc("total_sold")).first()

    # Top seller
    top_seller = db.query(
        models.User.names,
        func.count(models.Sale.id).label("sales_count")
    ).join(models.Sale, models.Sale.sold_by == models.User.id)

    if date_from:
        top_seller = top_seller.filter(cast(models.Sale.sold_at, Date) >= date_from)
    if date_to:
        top_seller = top_seller.filter(cast(models.Sale.sold_at, Date) <= date_to)

    top_seller = top_seller.group_by(models.User.names).order_by(desc("sales_count")).first()

    return {
        "filters": {
            "date_from": date_from,
            "date_to": date_to
        },
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_taxes": total_taxes,
        "total_profit": total_profit,
        "pending_sales": pending_sales,
        "completed_sales": completed_sales,
        "refunded_sales": refunded_sales,
        "partial_refunded_sales": partial_refunded_sales,
        "most_sold_product": {
            "name": top_product[0] if top_product else None,
            "quantity_sold": top_product[1] if top_product else 0
        },
        "top_seller": {
            "name": top_seller[0] if top_seller else None,
            "sales_count": top_seller[1] if top_seller else 0
        }
    }
# @app.get("/sales/search", response_model=List[SaleOut])
# def search_sales(
#     start_date: Optional[datetime] = None,
#     end_date: Optional[datetime] = None,
#     sold_by: Optional[UUID] = None,
#     db: Session = Depends(get_db)
# ):
#     query = db.query(models.Sale)
#     if start_date:
#         query = query.filter(models.Sale.sold_at >= start_date)
#     if end_date:
#         query = query.filter(models.Sale.sold_at <= end_date)
#     if sold_by:
#         query = query.filter(models.Sale.sold_by == sold_by)
#     return query.order_by(models.Sale.sold_at.desc()).all()


# @app.get("/sales/summary", dependencies=[Depends(get_current_user)])
# def sales_summary(db: Session = Depends(get_db)):
#     total_sales = db.query(func.sum(models.Sale.total)).scalar() or 0
#     total_products = db.query(func.sum(models.ProductSold.quantity_sold)).scalar() or 0
#     total_tax = db.query(func.sum(models.Sale.taxes)).scalar() or 0

#     return {
#         "total_sales": total_sales,
#         "total_products_sold": total_products,
#         "total_tax_collected": total_tax
#     }

