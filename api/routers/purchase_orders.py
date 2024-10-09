from fastapi import APIRouter

from api.models import purchase_orders as po_models
from api.queries import purchase_orders as po_queries

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders"])

@router.post("/create", response_model=po_models.PurchaseOrderOut)
async def create_purchase_order(po: po_models.PurchaseOrderIn):
  new_po = await po_queries.create_purchase_order(po=po)
  return new_po