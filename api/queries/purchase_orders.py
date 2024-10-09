from firebase_admin import firestore # type: ignore

from api.services.google_api import drive
from api.models import purchase_orders as po_models

# Create refernce to purchase_orders collection
db = firestore.client() # type: ignore
po_collection = db.collection("purchase_orders")

async def create_purchase_order(po: po_models.PurchaseOrderIn) -> po_models.PurchaseOrderOut:
  """
  This function creates a new PO worksheet from the template, and adds it to the DB.
  """
  # Create a new PO worksheet as a copy of the template.
  new_worksheet_id = await drive.create_copy_of_file(
    file_data=po_models.NewPurchaseOrder(new_file_name=po.name),
  )

  await drive.create_permissions(
    resource_id=new_worksheet_id,
    emails_to_permit=["dov@luxemporiumusa.com"],
    permission_type="writer",
  )

  new_purchase_order = po_models.PurchaseOrderDb(
    id=1, name=po.name, spreadsheet_id=new_worksheet_id, status="Draft", is_ats=False,
  )

  po_collection.document("test").add(new_purchase_order.model_dump()) # type: ignore

  return po_models.PurchaseOrderOut.model_validate(new_purchase_order)