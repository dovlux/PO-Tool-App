from fastapi import APIRouter, BackgroundTasks

from api.crud import purchase_orders as po_crud
from api.models.response import ResponseMsg
from api.models.purchase_orders import UpdatePurchaseOrder
from api.services.po_utils.create_breakdown import create_breakdown as validate_and_create_breakdown

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders > Actions"])

@router.get("/{id}/create-breakdown", response_model=ResponseMsg)
async def create_breakdown(id: int, background_tasks: BackgroundTasks):
  po_crud.update_purchase_order(id=id, updates=UpdatePurchaseOrder(status="Creating Breakdown"))

  background_tasks.add_task(validate_and_create_breakdown, po_id=id)

  return ResponseMsg(message="Purchase Order submitted for breakdown.")