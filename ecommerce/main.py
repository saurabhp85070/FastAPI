from fastapi import FastAPI, Query, HTTPException, Path, Query
from typing import List, Optional
from bson import ObjectId

from database import product_collection, order_collection
from schemas import ProductCreate, ProductResponse, ProductListResponse, ProductSummary, OrderCreate, OrderResponse, OrderListResponse
from models import serialize_doc

app = FastAPI()

# Create Product API
@app.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    product_dict = product.model_dump()
    result = await product_collection.insert_one(product_dict)
    return {"id": str(result.inserted_id)}

# List Products API
@app.get("/products", response_model=ProductListResponse)
async def list_products(
    name: Optional[str] = None,
    size: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if size:
        query["sizes.size"] = size  # search inside embedded sizes

    cursor = product_collection.find(query).sort("_id").skip(offset).limit(limit)
    products = []
    async for doc in cursor:
        products.append(ProductSummary(
            id=str(doc["_id"]),
            name=doc["name"],
            price=doc["price"]
        ))

    # Pagination logic
    page = {
        "next": offset + limit,
        "limit": len(products),
        "previous": offset - limit if offset - limit >= 0 else -10
    }

    return {"data": products, "page": page}

# Create Order API
@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate):
    product_ids = []

    for item in order.items:
        try:
            product_ids.append(ObjectId(item.productId))
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid productId: {item.productId}")

    # Fetch product documents
    products = await product_collection.find({"_id": {"$in": product_ids}}).to_list(length=len(product_ids))

    if len(products) != len(order.items):
        found_ids = {str(p["_id"]) for p in products}
        missing_ids = [item.productId for item in order.items if item.productId not in found_ids]
        raise HTTPException(status_code=404, detail=f"Products not found: {missing_ids}")

    # Check stock & prepare deduction plan
    stock_updates = []  # collect (product_id, updated_sizes) to update DB later

    for item in order.items:
        product = next((p for p in products if str(p["_id"]) == item.productId), None)
        if not product:
            continue

        sizes = product.get("sizes", [])
        total_stock = sum(size.get("quantity", 0) for size in sizes)

        if item.qty > total_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product '{product['name']}' (available: {total_stock}, requested: {item.qty})"
            )

        # Deduct qty from sizes
        # We are not specifying size during order — we’ll deduct from available sizes in any order, starting with the largest available quantity
        qty_to_deduct = item.qty
        new_sizes = []
        for size in sizes:
            available = size["quantity"]
            if qty_to_deduct == 0:
                new_sizes.append(size)
                continue

            deduct = min(qty_to_deduct, available)
            new_sizes.append({
                "size": size["size"],
                "quantity": available - deduct
            })
            qty_to_deduct -= deduct

        stock_updates.append((product["_id"], new_sizes))

    # Apply stock updates in MongoDB
    for product_id, updated_sizes in stock_updates:
        await product_collection.update_one(
            {"_id": product_id},
            {"$set": {"sizes": updated_sizes}}
        )

    # Save order in DB
    order_data = {
        "user_id": order.userId,
        "items": [
            {"product_id": item.productId, "quantity": item.qty}
            for item in order.items
        ]
    }

    result = await order_collection.insert_one(order_data)
    return {"id": str(result.inserted_id)}


# Get Orders by User ID
@app.get("/orders/{user_id}", response_model=OrderListResponse)
async def get_user_orders(
    user_id: str = Path(...),
    limit: int = Query(10),
    offset: int = Query(0)
):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"_id": 1}},
        {"$skip": offset},
        {"$limit": limit},
        {"$unwind": "$items"},
        {
            "$addFields": {
                "items.product_id_obj": {
                    "$toObjectId": "$items.product_id"
                }
            }
        },
        {
            "$lookup": {
                "from": "products",
                "localField": "items.product_id_obj",
                "foreignField": "_id",
                "as": "product_details"
            }
        },
        {"$unwind": "$product_details"},
        {
            "$group": {
                "_id": "$_id",
                "items": {
                    "$push": {
                        "productDetails": {
                            "name": "$product_details.name",
                            "id": {"$toString": "$product_details._id"}
                        },
                        "qty": "$items.quantity"
                    }
                },
                "total": {
                    "$sum": {
                        "$multiply": ["$items.quantity", "$product_details.price"]
                    }
                }
            }
        },
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "items": 1,
                "total": 1
            }
        }
    ]


    orders_cursor = order_collection.aggregate(pipeline)
    orders = [order async for order in orders_cursor]

    # Pagination meta
    page_info = {
        "next": offset + limit,
        "limit": len(orders),
        "previous": offset - limit if offset - limit >= 0 else -10
    }

    return {
        "data": orders,
        "page": page_info
    }