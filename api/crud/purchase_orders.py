from fastapi import HTTPException, status
from firebase_admin import firestore # type: ignore
from typing import List

from api.services.utils.get_next_db_id import get_next_id
from api.models import purchase_orders as po_models
from api.models.response import ResponseMsg

# Create reference to purchase_orders collection
db = firestore.client() # type: ignore
po_collection = db.collection("purchase_orders")

def create_purchase_order(po: po_models.PurchaseOrderDB) -> po_models.PurchaseOrderOut:
  try:
    new_id = get_next_id(document="purchase_orders")
    po_data = po.model_dump()
    po_collection.document(new_id).set(po_data) # type: ignore
    return po_models.PurchaseOrderOut(**po_data, id=int(new_id))
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not create Purchase Order. {str(e)}",
    )

def get_all_purchase_orders() -> List[po_models.PurchaseOrderOut]:
  try:
    po_docs = po_collection.stream()
    purchase_orders = [
      po_models.PurchaseOrderOut(**doc.to_dict(), id=int(doc.id)) # type: ignore
      for doc in po_docs # type: ignore
    ]
    return purchase_orders
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Purchase Orders. {str(e)}"
    )

def get_purchase_order(id: int) -> po_models.PurchaseOrderOut:
  try:
    po_ref = po_collection.document(str(id))
    po_doc = po_ref.get() # type: ignore

    if not po_doc.exists:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Purchase Order with id #{id} does not exist.",
      )
    
    po_data = po_doc.to_dict()
    return po_models.PurchaseOrderOut(**po_data, id=id) # type: ignore
  
  except HTTPException:
    raise

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Purchase Order. {str(e)}"
    )
  
def update_purchase_order(
  id: int, updates: po_models.UpdatePurchaseOrder
) -> ResponseMsg:
  try:
    po_ref = po_collection.document(str(id))
    
    updated_data = updates.model_dump(exclude_none=True)
    po_ref.update(updated_data) # type: ignore
    
    return ResponseMsg(message="Purchase Order updated successfully.")
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not update Purchase Order #{id}. {str(e)}",
    )
  
def add_log_to_purchase_order(id: int, log: po_models.Log) -> ResponseMsg:
  try:
    po_ref = po_collection.document(str(id))
    
    po_ref.update({"logs": firestore.ArrayUnion([log.model_dump()])}) # type: ignore
    
    return ResponseMsg(message="Log added to Purchase Order.")
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not add log to Purchase Order #{id}. {str(e)}",
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