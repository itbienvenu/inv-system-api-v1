# Inventory & Sales Management API (v1)

A RESTful API for managing products, sales transactions, and user authentication in an inventory system.

## 🚀 Features

## 📚 Table of Contents

- [🚀 Features](#-features)
- [📁 Project Structure](#-project-structure)
- [📌 Endpoints Documentation](#-endpoints-documentation)
  - [1. Authentication](#1-authentication)
  - [2. User Management](#2-user-management)
  - [3. Product Management](#3-product-management)
  - [4. Sales Management](#4-sales-management)
  - [5. Sales Reports](#5-sales-reports)
- [🛠️ Installation](#️-installation)
- [📝 Requirements](#-requirements)
- [📁 File Storage](#-file-storage)
- [📌 Notes](#-notes)
- [🧪 Testing](#-testing)
- [📦 Future Enhancements](#-future-enhancements)

- **Product Management**
  - Create products with multiple images (front and back)
  - View, update, and delete products
  - Low stock alerts configuration
  - SKU-based product tracking

- **Sales Processing**
  - Create sales with multiple products
  - Track buyer information (name, phone, email)
  - Support for different payment methods
  - Automatic stock updates after sales
  - Sales status management (completed, pending, refunded)

- **Reporting & Analytics**
  - Sales summary with revenue/profit calculations
  - Date range filtering for reports
  - Top products and sellers tracking
  - Sales document generation in JSON format

- **Authentication**
  - JWT-based authentication
  - Role-based access control
  - User registration and login

## 📁 Project Structure

<pre>

................
├── main.py # Main API routes and application 
├── database/ # Database models and connection
│├── models.py # SQLAlchemy models 
│└── database.py # Database configuration 
├── schemas/ # Pydantic models for data validation 
│ ├── user_schema.py # User-related schemas 
│ ├── product_schema.py # Product-related schemas 
│ └── sales_schema.py # Sales-related schemas 
├── utils/ # Utility functions 
│ └── functions.py # Token generation and password hashing 
└── static/ # File storage └── images/ # Product images storage


</pre>


## 📌 Endpoints Documentation

### 1. Authentication

**POST /login**
```
bash curl -X POST "http://localhost:8000/api/v1/login"
-H "Content-Type: application/x-www-form-urlencoded"
-d "username=user@example.com&password=yourpassword"
```

**Response:**
```
json { 
  "message": "User logged in successfully", 
  "user_data": { 
    "user_id": "123e4567-e89b-12d3-a456-426614174000", 
    "names": "John Doe", 
    "email": "user@example.com", 
    "phone": "1234567890" }, 
    "access_token": "your.jwt.token.here", 
    "token_type": "bearer" 
}
```

### 2. User Management

**POST /register**
```
bash curl -X POST "http://localhost:8000/register"
-H "Authorization: Bearer <token>"
-H "Content-Type: application/json"
-d '{ 
  "names": "Jane Smith", 
  "email": "jane@example.com", 
  "phone": 9876543210, 
  "password": "securepassword123", 
  "role": ["admin", "seller"] 
}
```

**Response:**
```
json { 
  "message": "User Registered Well", 
  "user_data": { 
    "user_id": "123e4567-e89b-12d3-a456-426614174001", 
    "names": "Jane Smith", 
    "email": "jane@example.com", 
    "phone": 9876543210, 
    "role": [
      "admin", 
      "seller"
    ] 
  } 
}
```

### 3. Product Management

**POST /register_product**

```
bash curl -X POST "http://localhost:8000/api/v1/register_product"
-H "Authorization: Bearer <token>"
-H "Content-Type: multipart/form-data"
-F "product_name=Wireless Mouse"
-F "selling_price=29.99"
-F "buying_price=15.00"
-F "quantity=100"
-F "category=Electronics"
-F "brand=TechCo"
-F "front_image=@front.jpg"
-F "back_images=@back1.jpg"
-F "back_images=@back2.jpg"
-F "description=High-quality wireless mouse"
-F "sku=MOUSE-001"
-F "unit=pcs"
-F "low_stock_alert=10"
-F "created_by=123e4567-e89b-12d3-a456-426614174000"
```

**Response:**

```
json { 
  "status": "success", 
  "message": "Product Registered well", 
  "data": { 
    "name": "Wireless Mouse", 
    "sku": "MOUSE-001" 
  }
}

```

**GET /product/{product_id}**
```
bash curl -X GET "http://localhost:8000/api/v1/product/123e4567-e89b-12d3-a456-426614174001"
-H "Authorization: Bearer <token>"
```

**Response:**

```
json { 
  "id": "123e4567-e89b-12d3-a456-426614174001", 
  "product_name": "Wireless Mouse", 
  "selling_price": 29.99, 
  "buying_price": 15.00, 
  "quantity": 100, 
  "category": "Electronics", 
  "brand": "TechCo", 
  "front_image": "front_abc123.jpg", 
  "back_image": [
    "back_def456.jpg", 
    "back_ghi789.jpg"
  ], 
    "description": "High-quality wireless mouse", 
    "sku": "MOUSE-001", 
    "unit": "pcs", 
    "low_stock_alert": 10, 
    "created_by": "123e4567-e89b-12d3-a456-426614174000", "last_modified": "2023-09-20T12:34:56Z"
}
```

### 4. Sales Management

**POST /sell_product**
```
bash curl -X POST "http://localhost:8000/api/v1/sell_product"
-H "Authorization: Bearer <token>"
-H "Content-Type: application/json"
-d '{ "products": [ { "product_id": "123e4567-e89b-12d3-a456-426614174001", "quantity_sold": 2, "selling_price": 29.99, "discount": 5.00 } ], "buyer_name": "Alice Johnson", "buyer_phone": "5556667777", "buyer_email": "alice@example.com", "payment_method": "CASH", "payment_reference": "CASH-1234", "total_discount": 10.00, "taxes": 5.00, "currency": "USD", "notes": "Walk-in customer", "sold_at": "2023-09-20T14:30:00Z" }'

```

**Response:**

```
json { 
  "message": "Sale completed successfully", 
  "sale_id": "123e4567-e89b-12d3-a456-426614174002", 
  "total": 54.98 
}
```

**GET /sales/{sale_id}**
```
bash curl -X GET "http://localhost:8000/api/v1/sales/123e4567-e89b-12d3-a456-426614174002"
-H "Authorization: Bearer <token>"
```

**Response:**

```
json { 
  "id": "123e4567-e89b-12d3-a456-426614174002", 
  "buyer_name": "Alice Johnson", 
  "buyer_phone": "5556667777", 
  "buyer_email": "alice@example.com", 
  "payment_method": "CASH", 
  "payment_reference": "CASH-1234", 
  "subtotal": 59.98, 
  "total_discount": 10.00, 
  "taxes": 5.00, 
  "total": 54.98, 
  "currency": "USD", 
  "sold_by": "123e4567-e89b-12d3-a456-426614174000", 
  "notes": "Walk-in customer", 
  "status": "completed", 
  "sold_at": "2023-09-20T14:30:00Z", 
  "products": [ 
    { 
      "product_id": "123e4567-e89b-12d3-a456-426614174001", "product_name": "Wireless Mouse", 
      "quantity_sold": 2, 
      "selling_price": 29.99, 
      "cost_price": 15.00, 
      "discount": 5.00 
    } 
  ] 
}

```

### 5. Sales Reports

**GET /sales/report/summary**

```
bash curl -X GET "http://localhost:8000/api/v1/sales/report/summary?date_from=2023-09-01&date_to=2023-09-30"
-H "Authorization: Bearer <token>"
```

**Response:**

```
json { 
  "filters": 
  { 
    "date_from": "2023-09-01", 
    "date_to": "2023-09-30" 
  }, 
  "total_sales": 150, 
  "total_revenue": 45000.00, 
  "total_taxes": 2250.00, 
  "total_profit": 12000.00, 
  "pending_sales": 5, 
  "completed_sales": 140, 
  "refunded_sales": 3, 
  "partial_refunded_sales": 2, 
  "most_sold_product": 
  { 
    "name": "Wireless Keyboard", 
    "quantity_sold": 35 
  }, 
    "top_seller": 
    { 
      "name": "John Doe", 
      "sales_count": 45 
  }
}

```

## 🛠️ Installation

1. Clone repository
2. Create `.env` file with:
   ```env
   SECRETE_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRES=30
   ```
3. Install dependencies:
   ```bash
   pip install fastapi sqlalchemy pydantic python-dotenv uvicorn
   ```
4. Initialize database:
   ```python
   from database.database import Base, engine
   Base.metadata.create_all(bind=engine)
   ```
5. Run server:
   ```bash
   uvicorn main:app --reload
   ```
## 📝 Requirements

- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn (ASGI server)
- Python-dotenv
- Jinja2 (for potential template rendering)

## 📁 File Storage

- Product images are stored in `static/images/` directory
- File naming format: UUID + original extension
- Front image stored as single file
- Back images stored as JSON array of filenames

## 📌 Notes

- All IDs use UUID format
- Status updates are case-sensitive (use "completed", "pending", etc.)
- Date filtering uses ISO format (YYYY-MM-DD)
- Product quantity validation is enforced before sales
- Role-based access control is implemented via JWT claims

## 🧪 Testing

Use the following tools:
- [Postman](https://www.postman.com/)
- [curl](https://curl.se/)
- FastAPI's built-in documentation at:
  - Swagger UI: `/docs`
  - Redoc: `/redoc`

## 📦 Future Enhancements

- Add Swagger/OpenAPI documentation
- Implement image validation
- Add pagination for large datasets
- Create CSV/Excel export for sales reports
- Add unit tests
- Implement rate limiting
