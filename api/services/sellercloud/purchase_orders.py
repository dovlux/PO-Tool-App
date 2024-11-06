from typing import List, Dict
from fastapi import HTTPException, status

from api.services.sellercloud.base import sellercloud_api_call
from api.models.sellercloud import PoAddProduct, PoReceiveProduct

async def create_purchase_order(
  token: str, company_id: int, vendor_id: int, description: str,
  products: List[PoAddProduct], warehouse_id: int,
) -> int:
  endpoint = "PurchaseOrders"
  body: Dict[str, int | str | List[Dict[str, int | str | float]]] = {
    "CompanyID": company_id,
    "VendorID": vendor_id,
    "Description": description,
    "Products": [product.model_dump() for product in products],
    "DefaultWarehouseID": warehouse_id,
  }
   
  response = await sellercloud_api_call(
    method="post", endpoint=endpoint, token=token, body=body,
  )

  if response is None or response.get("Id", None) is None:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not retrieve Purchase Order Id.",
    )

  return int(response["Id"])

async def add_items_to_purchase_order(
  po_id: int | None, products: List[PoAddProduct], token: str,
) -> None:
  if po_id is None:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Purchase Order ID is None.",
    )
  
  endpoint = f"PurchaseOrders/{po_id}/items"
  body = [product.model_dump() for product in products]

  await sellercloud_api_call(
    method="post", endpoint=endpoint, token=token, body=body,
  )

async def receive_purchase_order(
  po_id: int, products: List[PoReceiveProduct], token: str,
) -> None:
  endpoint = f"PurchaseOrders/{po_id}/receive"
  body = { "Items": [product.model_dump() for product in products] }

  await sellercloud_api_call(
    method="post", endpoint=endpoint, token=token, body=body,
  )