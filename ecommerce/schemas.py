from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from bson import ObjectId

# Create Products ----------------------START----------------------
class SizeItem(BaseModel):
    size: str
    quantity: int
    
    @field_validator("quantity") # validating quantity for negative value
    @classmethod
    def quantity_non_negative(cls, value):
        if value < 0:
            raise ValueError("Quantity must be >= 0")
        return value

class ProductCreate(BaseModel):
    name: str
    price: float
    sizes: List[SizeItem]
    
    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v
    
    @model_validator(mode="after") # validating model for duplicate size
    def validate_unique_sizes(self):
        seen_sizes = set()
        for item in self.sizes:
            if item.size in seen_sizes:
                raise ValueError(f"Duplicate size found: {item.size}")
            seen_sizes.add(item.size)
        return self

class ProductResponse(BaseModel):
    id: str

# Create Products ----------------------END----------------------

# List Products ----------------START---------------
class ProductSummary(BaseModel):
    id: str
    name: str
    price: float


class ProductListResponse(BaseModel):
    data: List[ProductSummary]
    page: dict

# List Products ----------------END---------------

# Create Order------------------START-------------
class OrderItemInput(BaseModel):
    productId: str
    qty: int

    @field_validator("qty")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class OrderCreate(BaseModel):
    userId: str
    items: List[OrderItemInput]


class OrderResponse(BaseModel):
    id: str

# Create Order------------------END-------------


# Get List of Orders----------------START-----------
class ProductDetails(BaseModel):
    name: str
    id: str


class OrderItemOut(BaseModel):
    productDetails: ProductDetails
    qty: int


class OrderOut(BaseModel):
    id: str
    items: List[OrderItemOut]
    total: float


class PaginationInfo(BaseModel):
    next: int
    limit: int
    previous: int


class OrderListResponse(BaseModel):
    data: List[OrderOut]
    page: PaginationInfo
    
# Get List of Orders----------------END-----------