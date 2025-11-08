from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from .settings import settings
from .orders import OrderCreate, place_order

app = FastAPI(title="orders-service")
_mongo = AsyncIOMotorClient(settings.MONGO_URI)

def get_client():
    return _mongo

@app.get("/health")
async def health():
    await _mongo.admin.command("ping")
    return {"status": "ok"}

@app.post("/orders", status_code=201)
async def create_order(payload: OrderCreate, client: AsyncIOMotorClient = Depends(get_client)):
    order = await place_order(payload, client, settings.CATALOG_BASE_URL)
    if "_id" in order and not isinstance(order["_id"], str):
        order["_id"] = str(order["_id"])
    return order

@app.get("/orders")
async def list_orders(client: AsyncIOMotorClient = Depends(get_client)):
    cursor = client["ordersdb"]["orders"].find().sort("_id", -1).limit(50)
    out = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        out.append(doc)
    return out

@app.get("/orders/{order_id}")
async def get_order(order_id: str, client: AsyncIOMotorClient = Depends(get_client)):
    try:
        oid = ObjectId(order_id.strip())        # ← convert string to ObjectId
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id format (expect 24-hex)")

    doc = await client["ordersdb"]["orders"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    doc["_id"] = str(doc["_id"])
    return doc
