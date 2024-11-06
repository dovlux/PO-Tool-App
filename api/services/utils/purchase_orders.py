from typing import List

from api.crud.purchase_orders import add_log_to_purchase_order
from api.services.sellercloud import purchase_orders as sc_po_calls
from api.models.sellercloud import PoAddProduct, PoReceiveProduct
from api.models.settings import SellercloudSettings
from api.models.purchase_orders import Log

async def create_and_receive_purchase_order(
  po_id: int, token: str, sc_settings: SellercloudSettings,
  po_name: str, products: List[PoAddProduct],
) -> int:
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Creating purchase order.", type="log"),
  )

  sc_po_id = await sc_po_calls.create_purchase_order(
    token=token, company_id=sc_settings.ats_company_id,
    vendor_id=sc_settings.ats_vendor_id, description=po_name, products=products,
    warehouse_id=sc_settings.ats_warehouse_id,
  )

  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Receiving Purchase Order.", type="log"),
  )

  items_to_receive = [
    PoReceiveProduct(ID=product.ProductID, QtyToReceive=product.QtyUnitsOrdered)
    for product in products
  ]

  await sc_po_calls.receive_purchase_order(
    po_id=sc_po_id, products=items_to_receive, token=token,
  )

  return sc_po_id