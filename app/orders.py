from pydantic import BaseModel, Field
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

class OrderItem(BaseModel):
    book_id: int
    qty: int = Field(ge=1)

class OrderCreate(BaseModel):
    items: list[OrderItem]

async def place_order(payload: OrderCreate, client: AsyncIOMotorClient, catalog_base: str):
    async with httpx.AsyncClient(timeout=5.0) as http:
        total_price = 0
        # Validate each item & reserve
        for it in payload.items:
            r = await http.get(f"{catalog_base}/books/{it.book_id}")
            if r.status_code == 404:
                raise HTTPException(400, f"Book {it.book_id} not found")
            book = r.json()
            price = book["price"]
            # reserve
            r2 = await http.post(f"{catalog_base}/books/{it.book_id}/reserve", json={"qty": it.qty})
            if r2.status_code != 200:
                raise HTTPException(409, f"Insufficient stock for book {it.book_id}")
            total_price += price * it.qty

    order_doc = {
        "items": [i.dict() for i in payload.items],
        "status": "PLACED",
        "total_price": total_price
    }
    res = await client[ "ordersdb" ]["orders"].insert_one(order_doc)
    order_doc["_id"] = str(res.inserted_id)
    return order_doc
