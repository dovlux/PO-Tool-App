from fastapi import APIRouter, BackgroundTasks
from datetime import datetime, timezone
from typing import List
import json

from api.models import purchase_orders as po_models
from api.models.response import ResponseMsg
from api.crud import purchase_orders as po_crud
from api.services.po_utils.create_po_worksheet import create_po_worksheet
from api.services.currency_api.currency_queries import get_exchange_rate

router = APIRouter(prefix="/api", tags=["Purchase Orders"])

@router.post("/purchase-orders", response_model=po_models.PurchaseOrderOut)
async def create_purchase_order(
  po: po_models.PurchaseOrderIn, background_tasks: BackgroundTasks
):
  # Create Purchase Order entry in Database
  current_time = datetime.now(tz=timezone.utc).isoformat()
  exchange_rate = 1.0 if po.currency == "USD" else get_exchange_rate(currency=po.currency)
  new_po = po_crud.create_purchase_order(
    po=po_models.PurchaseOrderDB(
      name=po.name, is_ats=po.is_ats, date_created=json.dumps(current_time),
      status="Creating Worksheet", currency=po.currency, currency_conversion=exchange_rate,
      logs=[po_models.Log(user="pending", message="Created PO.", type="user")]
    )
  )

  # Create background task to create a new worksheet for new Purchase Order
  background_tasks.add_task(create_po_worksheet, po=new_po)

  return new_po

@router.get("/purchase-orders", response_model=List[po_models.PurchaseOrderOut])
async def get_all_purchase_orders():
  purchase_orders = po_crud.get_all_purchase_orders()
  return purchase_orders

@router.get("/purchase-orders/{id}", response_model=po_models.PurchaseOrderOut)
async def get_purchase_order(id: int):
  purchase_order = po_crud.get_purchase_order(id=id)
  return purchase_order

@router.put("/purchase-orders/{id}", response_model=ResponseMsg)
async def update_purchase_order(id: int, updates: po_models.UpdatePurchaseOrder):
  message = po_crud.update_purchase_order(id=id, updates=updates)

  if updates.status is not None:
    po_crud.add_log_to_purchase_order(
      id=id, log=po_models.Log(
        user="pending", message=f"Status changed to {updates.status}.", type="user"
      )
    )

  return message

@router.delete("/purchase-orders/{id}", response_model=ResponseMsg)
async def delete_purchase_order(id: int):
  message = po_crud.delete_purchase_order(id=id)
  return message