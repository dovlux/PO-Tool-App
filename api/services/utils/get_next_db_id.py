from fastapi import HTTPException, status
from firebase_admin import firestore # type: ignore
from typing import Literal
import threading

# Create reference to counters collection
db = firestore.client() # type: ignore
counter_collection = db.collection("counters")
counter_lock = threading.Lock()

def get_next_id(document: Literal["purchase_orders"]) -> str:
  try:
    with counter_lock:
      counter_ref = counter_collection.document(document)
      counter_doc = counter_ref.get() # type: ignore

      if not counter_doc.exists:
        counter_ref.set({ "count": 0 }) # type: ignore

      current_count = counter_doc.to_dict().get("count") # type: ignore
      new_count = current_count + 1 # type: ignore
      counter_ref.update({ "count": new_count }) # type: ignore
      return str(new_count) # type: ignore
    
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve new id for new document. {str(e)}",
    )