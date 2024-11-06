from fastapi import APIRouter, BackgroundTasks

from api.crud import purchase_orders as po_crud
from api.models.response import ResponseMsg
from api.models.purchase_orders import UpdatePurchaseOrder, Log, AdditionalFees, UpdatePurchaseOrderPoId
from api.services.po_utils.create_breakdown import create_breakdown as validate_and_create_breakdown
from api.services.po_utils.calculate_net_sales import calculate_net_sales as validate_and_calculate_net_sales
from api.services.po_utils.create_skus_and_po import create_skus_and_po as validate_and_create_skus_and_po

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders > Actions"])

@router.get("/{id}/create-breakdown", response_model=ResponseMsg)
async def create_breakdown(id: int, background_tasks: BackgroundTasks):
  po_crud.update_purchase_order(
    id=id, updates=UpdatePurchaseOrder(status="Creating Breakdown"),
  )
  po_crud.add_log_to_purchase_order(
    id=id, log=Log(user="pending", message="Submitted for breakdown.", type="user"),
  )

  background_tasks.add_task(validate_and_create_breakdown, po_id=id)

  return ResponseMsg(message="Purchase Order submitted for breakdown.")

@router.post("/{id}/calculate-net-sales", response_model=ResponseMsg)
async def calculate_net_sales(id: int, fees: AdditionalFees, background_tasks: BackgroundTasks):
  po_crud.update_purchase_order(
    id=id, updates=UpdatePurchaseOrder(status="Calculating Net Sales", additional_fees=fees),
  )
  po_crud.add_log_to_purchase_order(
    id=id, log=Log(user="pending", message="Submitted to Calculate Net Sales.", type="user"),
  )

  background_tasks.add_task(validate_and_calculate_net_sales, po_id=id)

  return ResponseMsg(message="Purchase Order submitted for Net Sales Calculation.")

@router.get("/{id}/create-skus-and-po-ats", response_model=ResponseMsg)
async def create_skus_and_po_ats(id: int, background_tasks: BackgroundTasks):
  po_crud.update_purchase_order(
    id=id, updates=UpdatePurchaseOrder(status="Creating SKUs and PO"),
  )
  po_crud.add_log_to_purchase_order(
    id=id, log=Log(user="pending", message="Submitted to create SKUs and PO.", type="user"),
  )

  background_tasks.add_task(validate_and_create_skus_and_po, po_id=id)

  return ResponseMsg(message="Purchase Order submitted for Creating SKUs and PO.")

@router.post("/{id}/create-skus-and-po-non-ats", response_model=ResponseMsg)
async def create_skus_and_po_non_ats(
  id: int, po_id: UpdatePurchaseOrderPoId, background_tasks: BackgroundTasks
):
  po_crud.update_purchase_order(
    id=id, updates=UpdatePurchaseOrder(status="Creating SKUs and PO", po_id=po_id.po_id),
  )
  po_crud.add_log_to_purchase_order(
    id=id, log=Log(user="pending", message="Submitted to create SKUs and PO.", type="user"),
  )

  background_tasks.add_task(validate_and_create_skus_and_po, po_id=id)

  return ResponseMsg(message="Purchase Order submitted for Creating SKUs and PO.")