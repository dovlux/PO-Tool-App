from fastapi import HTTPException, status
from firebase_admin import firestore # type: ignore

from api.models import settings as settings_models
from api.models.response import ResponseMsg

# Create reference to purchase_orders collection
db = firestore.client() # type: ignore
settings_collection = db.collection("settings")

def get_breakdown_net_sales_settings() -> settings_models.BreakdownNetSalesSettings:
  try:
    doc_ref = settings_collection.document("breakdown_net_sales")
    settings_doc = doc_ref.get() # type: ignore

    if not settings_doc.exists:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Settings document does not exist.",
      )
    
    settings_data = settings_doc.to_dict()
    return settings_models.BreakdownNetSalesSettings(**settings_data) # type: ignore
  
  except HTTPException:
    raise

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Breakdown Net Sales Settings. {str(e)}"
    )
  
def update_breakdown_net_sales_settings(
  updates: settings_models.UpdateBreakdownNetSalesSettings
) -> ResponseMsg:
  try:
    doc_ref = settings_collection.document("breakdown_net_sales")
    
    updated_data = updates.model_dump(exclude_none=True)
    doc_ref.update(updated_data) # type: ignore
    
    return ResponseMsg(message="Breakdown Net Sales Settings updated successfully.")
  
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not update Breakdown Net Sales Settings. {str(e)}",
    )
  
def get_sellercloud_settings() -> settings_models.SellercloudSettings:
  try:
    doc_ref = settings_collection.document("sellercloud")
    settings_doc = doc_ref.get() # type: ignore

    if not settings_doc.exists:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Settings document does not exist.",
      )
    
    settings_data = settings_doc.to_dict()
    return settings_models.SellercloudSettings(**settings_data) # type: ignore
  
  except HTTPException:
    raise

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Sellercloud Settings. {str(e)}"
    )
  
def get_lightspeed_settings() -> settings_models.LightspeedSettings:
  try:
    doc_ref = settings_collection.document("lightspeed")
    settings_doc = doc_ref.get() # type: ignore

    if not settings_doc.exists:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Settings document does not exist.",
      )
    
    settings_data = settings_doc.to_dict()
    return settings_models.LightspeedSettings(**settings_data) # type: ignore
  
  except HTTPException:
    raise

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve Lightspeed Settings. {str(e)}"
    )