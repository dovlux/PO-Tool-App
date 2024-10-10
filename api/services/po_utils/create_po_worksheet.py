from fastapi import HTTPException

from api.services.utils.send_emails import send_error_email
from api.crud.purchase_orders import update_purchase_order
from api.services.google_api import drive as drive_services
from api.models import purchase_orders as po_models

async def create_po_worksheet(po: po_models.PurchaseOrderOut, retries: int = 3) -> None:
  attempt: int = 0

  new_worksheet_properties = po_models.NewPurchaseOrderNonAts(new_file_name=po.name)
  if po.is_ats:
    new_worksheet_properties = po_models.NewPurchaseOrderAts(new_file_name=po.name)

  while attempt < retries:
    try:
      new_worksheet_id = await drive_services.create_copy_of_file(
        file_data=new_worksheet_properties,
      )

      await drive_services.create_permissions(
        resource_id=new_worksheet_id, emails_to_permit=["dov@luxemporiumusa.com"],
        permission_type="writer",
      )

      update_purchase_order(id=po.id, updates=po_models.UpdatePurchaseOrder(
        status="Worksheet Created", spreadsheet_id=new_worksheet_id,
      ))

      return
    
    except HTTPException as e:
      attempt += 1
      if attempt == retries:
        await send_error_email(
          subject="PO Tool Creating PO Worksheet Error", error_message=e.detail
        )

        return

    except Exception as e:
      await send_error_email(
        subject="PO Tool Creating PO Worksheet Unspecified Error", error_message=str(e)
      )
      
      return
  
  return