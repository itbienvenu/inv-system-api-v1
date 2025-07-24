from fastapi import HTTPException, Depends, APIRouter, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date
from database import models

from auth.auth import get_current_user
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from schemas.sales_schema import SaleInput, SaleOut, SaleUpdateStatus
from uuid import UUID, uuid4
from database.get_db import get_db

from datetime import datetime, UTC, date


router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])

@router.get("/{sale_id}", response_model=SaleOut, dependencies=[Depends(get_current_user)])
def get_sale(sale_id: UUID, db: Session = Depends(get_db)):
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    products = db.query(models.ProductSold).filter(models.ProductSold.sale_id == sale_id).all()
    return SaleOut(
        **sale.__dict__,
        products=products
    )

@router.post("/sell_product", dependencies=[Depends(get_current_user)])
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



#Endpoint to display all sales

@router.get("/", response_model=List[SaleOut], dependencies=[Depends(get_current_user)])
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

@router.delete("/{sale_id}", dependencies=[Depends(get_current_user)])
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
@router.get("/{sale_id}/document", dependencies=[Depends(get_current_user)])
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

@router.put("/sales/{sale_id}", dependencies=[Depends(get_current_user)])
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

@router.get("/by_seller/{seller_id}", dependencies=[Depends(get_current_user)])
def get_sales_by_seller(seller_id: UUID, db: Session = Depends(get_db)):
    sales = db.query(models.Sale).filter(models.Sale.sold_by == seller_id).all()
    if not sales:
        raise HTTPException(status_code=404, detail="No sales found for this seller")
    
    return sales

@router.get("/report/summary", dependencies=[Depends(get_current_user)])
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

@router.get("/search", response_model=List[SaleOut])
def search_sales(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sold_by: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Sale)
    if start_date:
        query = query.filter(models.Sale.sold_at >= start_date)
    if end_date:
        query = query.filter(models.Sale.sold_at <= end_date)
    if sold_by:
        query = query.filter(models.Sale.sold_by == sold_by)
    return query.order_by(models.Sale.sold_at.desc()).all()


@router.get("/summary", dependencies=[Depends(get_current_user)])
def sales_summary(db: Session = Depends(get_db)):
    total_sales = db.query(func.sum(models.Sale.total)).scalar() or 0
    total_products = db.query(func.sum(models.ProductSold.quantity_sold)).scalar() or 0
    total_tax = db.query(func.sum(models.Sale.taxes)).scalar() or 0

    return {
        "total_sales": total_sales,
        "total_products_sold": total_products,
        "total_tax_collected": total_tax
    }