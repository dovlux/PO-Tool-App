from fastapi import HTTPException, status

from api.crud.purchase_orders import get_purchase_order
from api.services.po_utils.create_skus_and_po_validation import validate_worksheet_for_po
from api.crud.purchase_orders import add_log_to_purchase_order, update_purchase_order
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

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Validating Worksheet data for PO.", type="log"),
    )

    worksheet_values = await validate_worksheet_for_po(
      spreadsheet_id=spreadsheet_id, is_ats=po.is_ats
    )

    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal", message="Creating/Finding SKUs for all rows missing SKUs.", type="log"
      )
    )

  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error"),
    )
  