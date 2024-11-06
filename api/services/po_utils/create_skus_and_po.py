from fastapi import HTTPException, status
from typing import Set, List

from api.services.google_api.sheets_utils import post_row_dicts_to_spreadsheet
from api.crud.purchase_orders import get_purchase_order
from api.services.po_utils import create_skus_and_po_validation as worksheet_validation
from api.crud.purchase_orders import add_log_to_purchase_order, update_purchase_order
from api.services.po_utils.create_skus import create_or_find_skus
from api.crud.settings import get_sellercloud_settings
from api.services.sellercloud.base import get_token
from api.services.sellercloud.skus import check_if_skus_exist
from api.services.sellercloud.purchase_orders import add_items_to_purchase_order
from api.services.utils.purchase_orders import create_and_receive_purchase_order
from api.models.purchase_orders import UpdatePurchaseOrder, Log
from api.models.sellercloud import PoAddProduct
from api.models.sheets import WorksheetPropertiesAts, WorksheetPropertiesNonAts

async def create_skus_and_po(po_id: int) -> None:
  try:
    # Retrieve PO data from database
    po = get_purchase_order(id=po_id)

    # Retrieve spreadsheet_id from PO data
    spreadsheet_id = po.spreadsheet_id
    if spreadsheet_id is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Could not find spreadsheet ID for Purchase Order.",
      )

    # Validate data in worksheet for errors
    if po.is_ats:
      worksheet_values = await worksheet_validation.validate_worksheet_for_po_ats(
        spreadsheet_id=spreadsheet_id, po_id=po_id,
      )
    else:
      worksheet_values = await worksheet_validation.validate_worksheet_for_po_non_ats(
        spreadsheet_id=spreadsheet_id, po_id=po_id,
      )

    # If there are any errors in worksheet, log and end function
    if worksheet_values is None:
      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Create SKUs and PO)"),
      )
      return

    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal",
        message=f"Creating{'/Finding SKUs' if not po.is_ats else ''} for all rows{' missing SKUs' if not po.is_ats else ''}.",
        type="log",
      )
    )

    # Get SellerCloud settings and token
    sc_settings = get_sellercloud_settings()
    sc_token = await get_token(sc_settings=sc_settings)
    company_id = sc_settings.ats_company_id if po.is_ats else sc_settings.default_company_id

    # Create (and/or find for non-ats worksheets) SKUs for all products in worksheet
    await create_or_find_skus(
      worksheet_values=worksheet_values, po_id=po_id, is_ats=po.is_ats, po_name=po.name,
      sc_token=sc_token, company_id=company_id,
    )

    # Prepare list of skus for PO creation
    all_po_skus: Set[str] = set()
    po_products: List[PoAddProduct] = []

    # Populate lists of SKUs for PO Creation
    for row in worksheet_values.row_dicts:
      sku = str(row["ProductID"])
      qty = int(row["Qty"])
      cost = float(row[f"{'Unit Cost' if po.is_ats else 'Weighted Cost'}"])

      all_po_skus.add(sku)
      po_products.append(PoAddProduct(
        ProductID=sku, QtyUnitsOrdered=qty, UnitPrice=cost,
      ))

    # Check if all skus in worksheet exist in SellerCloud
    existing_skus = await check_if_skus_exist(token=sc_token, skus=list(all_po_skus))

    # If there are skus in the worksheet that were not found in SellerCloud
    if len(existing_skus) != len(all_po_skus):
      # Create error messages for missing SKUs
      for row in worksheet_values.row_dicts:
        if row["ProductID"] not in existing_skus:
          row["Errors"] = "Could not find SKU in SellerCloud"

      ss_properties = WorksheetPropertiesAts(id=spreadsheet_id) if po.is_ats else WorksheetPropertiesNonAts(id=spreadsheet_id)
      
      # Post error messages to the worksheet
      await post_row_dicts_to_spreadsheet(
        ss_properties=ss_properties, row_dicts=worksheet_values.row_dicts,
      )

      add_log_to_purchase_order(
        id=po_id, log=Log(
          user="Internal", message="Errors found and posted to worksheet.", type="error",
        ),
      )

      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Create SKUs and PO)"),
      )

      return
    
    if po.is_ats:
      # Create and receive the Purchase Order
      sc_po_id = await create_and_receive_purchase_order(
        po_id=po_id, token=sc_token, sc_settings=sc_settings,
        po_name=po.name, products=po_products,
      )

      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Purchase Order Received.", type="log"),
      )

      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="PO Received", po_id=sc_po_id)
      )

    else:
      # Add items to pre-existing purchase order
      await add_items_to_purchase_order(
        po_id=po.po_id, products=po_products, token=sc_token,
      )

      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Items added to PO", type="log"),
      )

      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="PO Created"),
      ) 

  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error"),
    )
  