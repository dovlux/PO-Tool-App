from fastapi import HTTPException, status

from api.crud.purchase_orders import get_purchase_order
from api.services.po_utils.create_skus_and_po_validation import validate_worksheet_for_po
from api.crud.purchase_orders import add_log_to_purchase_order, update_purchase_order
from api.services.po_utils.create_skus import create_or_find_skus
from api.models.purchase_orders import UpdatePurchaseOrder, Log

async def create_skus_and_po(po_id: int) -> None:
  try:
    po = get_purchase_order(id=po_id)
    spreadsheet_id = po.spreadsheet_id
    if spreadsheet_id is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Could not find spreadsheet ID for Purchase Order.",
      )

    worksheet_values = await validate_worksheet_for_po(
      spreadsheet_id=spreadsheet_id, is_ats=po.is_ats, po_id=po_id,
    )

    if worksheet_values is None:
      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Create SKUs and PO)"),
      )

      return

    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal",
        message=f"Creating{'/Finding SKUs' if not po.is_ats else ''} for all rows{' missing SKUs.' if not po.is_ats else ''}",
        type="log",
      )
    )

    await create_or_find_skus(worksheet_values=worksheet_values, po_id=po_id, is_ats=po.is_ats)

  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error"),
    )
  