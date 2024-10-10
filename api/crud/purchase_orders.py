from fastapi import HTTPException, status
from firebase_admin import firestore # type: ignore
from typing import List

from api.services.utils.get_next_db_id import get_next_id
from api.models.purchase_orders import PurchaseOrderDB, PurchaseOrderOut, UpdatePurchaseOrder
from api.models.response import ResponseMsg

# Create reference to purchase_orders collection
db = firestore.client() # type: ignore
po_collection = db.collection("purchase_orders")

def create_purchase_order(po: PurchaseOrderDB) -> PurchaseOrderOut:
  try:
    new_id = get_next_id(document="purchase_orders")
    po_data = po.model_dump()
    po_collection.document(new_id).set(po_data) # type: ignore
    return PurchaseOrderOut(**po_data, id=int(new_id))
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not create Purchase Order. {str(e)}",
    )

def get_all_purchase_orders() -> List[PurchaseOrderOut]:
  try:
    po_docs = po_collection.stream()
    purchase_orders = [PurchaseOrderOut(**doc.to_dict(), id=int(doc.id)) for doc in po_docs] # type: ignore
    return purchase_orders
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Purchase Orders. {str(e)}"
    )

def get_purchase_order(id: int) -> PurchaseOrderOut:
  try:
    po_ref = po_collection.document(str(id))
    po_doc = po_ref.get() # type: ignore

    if not po_doc.exists:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Purchase Order with id #{id} does not exist.",
      )
    
    po_data = po_doc.to_dict()
    return PurchaseOrderOut(**po_data, id=id) # type: ignore
  
  except HTTPException:
    raise

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Purchase Order. {str(e)}"
    )
  
def update_purchase_order(id: int, updates: UpdatePurchaseOrder) -> PurchaseOrderOut:
  try:
    po_ref = po_collection.document(str(id))

    if not po_ref.get().exists: # type: ignore
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Could not find Purchase Order with ID#{id}."
      )
    
    updated_data = updates.model_dump(exclude_none=True)
    po_ref.update(updated_data) # type: ignore
    updated_po = get_purchase_order(id=id)
    return updated_po
  
  except HTTPException:
    raise
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not update Purchase Order #{id}. {str(e)}",
    )
  
def delete_purchase_order(id: int) -> ResponseMsg:
  try:
    po_ref = po_collection.document(str(id))

    if not po_ref.get().exists: # type: ignore
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Purchase Order with ID#{id} does not exist.",
      )
    
    po_ref.delete()

    return ResponseMsg(message="Purchase Order deleted successfully.")
    
  except HTTPException:
    raise

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not delete Purchase Order with ID#{id}. {str(e)}",
    )