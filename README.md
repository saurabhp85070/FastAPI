# *🛒 FastAPI eCommerce Backend*

*This project is a ****FastAPI-based eCommerce API**** that provides endpoints to create and manage products and orders. It uses ****MongoDB**** as the database (via **`motor`** - the async driver) and Pydantic for schema validation.*

---

## *📁 Project Structure*

```
ecommerce-api/
│
├── database.py          # MongoDB connection setup
├── models.py            # Helper function for BSON to JSON serialization
├── schemas.py           # Pydantic models for request and response validation
├── main.py              # FastAPI app and route handlers
├── .env                 # Environment variables (e.g., MongoDB URI)
└── README.md            # Documentation
```

---

## 🛆 Tech Stack

- **FastAPI** – Web framework
- **MongoDB** – NoSQL database
- **Motor** – Async MongoDB driver for Python
- **Pydantic v2** – Data validation and parsing
- **Uvicorn** – ASGI server (for running FastAPI)

---

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following:

```env
MONGO_URI=mongodb://localhost:27017
```

---

## ✅ API Features

### 1. **Create Product**

**Endpoint**: `POST /products`\
**Description**: Adds a new product with name, price, and sizes.

#### Request Body:

```json
{
  "name": "T-shirt",
  "price": 499.99,
  "sizes": [
    {"size": "S", "quantity": 10},
    {"size": "M", "quantity": 15}
  ]
}
```

#### Response:

```json
{
  "id": "product_mongo_id"
}
```

### 2. **List Products**

**Endpoint**: `GET /products`\
**Description**: Lists all products with optional filters.

#### Query Params:

- `name`: filter by name (case-insensitive, partial match)
- `size`: filter by available sizes
- `limit` (default: 10)
- `offset` (default: 0)

#### Response:

```json
{
  "data": [
    {"id": "...", "name": "T-shirt", "price": 499.99}
  ],
  "page": {
    "next": 10,
    "limit": 1,
    "previous": -10
  }
}
```

### 3. **Create Order**

**Endpoint**: `POST /orders`\
**Description**: Places an order for one or more products by quantity. Deducts available quantity automatically.

#### Request Body:

```json
{
  "userId": "user123",
  "items": [
    {"productId": "abc123", "qty": 2}
  ]
}
```

#### Response:

```json
{
  "id": "order_mongo_id"
}
```

> 🛑 Validates:

- product IDs exist
- requested quantity ≤ available stock
- auto-updates inventory

### 4. **Get Orders by User**

**Endpoint**: `GET /orders/{user_id}`\
**Description**: Retrieves paginated orders placed by a specific user.

#### Query Params:

- `limit` (default: 10)
- `offset` (default: 0)

#### Response:

```json
{
  "data": [
    {
      "id": "order_id",
      "items": [
        {
          "productDetails": {
            "name": "T-shirt",
            "id": "product_id"
          },
          "qty": 2
        }
      ],
      "total": 999.98
    }
  ],
  "page": {
    "next": 10,
    "limit": 1,
    "previous": -10
  }
}
```

> ⚙️ Uses MongoDB aggregation to:

- join product details
- calculate total
- handle pagination

---

## 🚀 Running the App

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Run the server**

```bash
uvicorn main:app --reload
```

3. **Visit Swagger UI**

```
https://ecom-api-v1.onrender.com/docs
```

---

