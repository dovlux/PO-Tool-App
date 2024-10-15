from fastapi import HTTPException, status

from api.services.po_utils.breakdown_validation import validate_worksheet_for_breakdown
from api.services.cached_data.sales_reports import get_updated_sales_reports_rows
from api.crud.purchase_orders import update_purchase_order, add_log_to_purchase_order, get_purchase_order
from api.models.sheets import RelevantSalesProperties, WorksheetProperties
from api.services.google_api import sheets_utils
from api.models.purchase_orders import UpdatePurchaseOrder, Log

async def create_breakdown(po_id: int) -> None:
  po = get_purchase_order(id=po_id)
  if po.is_ats:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Breakdown does not apply to ATS Purchase Orders",
    )

  worksheet_values = await validate_worksheet_for_breakdown(po_id=po_id)
  if worksheet_values is None:
    return
  
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Creating breakdown.", type="log")
  )
  
  try:
    # Retrieve recents sales reports for breakdown
    sales_reports_rows = get_updated_sales_reports_rows().row_dicts
    
    groups: set[str] = set()
    brand_gender_types: set[str] = set()

    # Get brand_gender_type, group, total cost, and total msrp for each row
    for row in worksheet_values.row_dicts:
      brand_gender_type: str = f"{row['Brand'].lower()} {row['Gender']} {row['Category']}"
      brand_gender_types.add(brand_gender_type)
      row["BrandGenderType"] = brand_gender_type

      group: str = f"{row['Brand']} {row['Item Type']} {row['Grade']}"
      groups.add(group)
      row["Group"] = group

      row["Total Cost"] = float(row["Unit Cost"]) * int(row["Qty"])
      row["Total Msrp"] = float(row["Retail"]) * int(row["Qty"])

    # Get relevant sales for products in the PO
    relevant_sales_rows = [
      sales_row for sales_row in sales_reports_rows
      if sales_row["Order Date"]
      and sales_row["Brand Gender Category"] in brand_gender_types
      and sales_row['Marketplace']
    ]

    await sheets_utils.post_row_dicts_to_spreadsheet(
      ss_properties=RelevantSalesProperties(id=worksheet_values.spreadsheet_id),
      row_dicts=relevant_sales_rows,
    )

    await sheets_utils.post_row_dicts_to_spreadsheet(
      ss_properties=WorksheetProperties(id=worksheet_values.spreadsheet_id),
      row_dicts=worksheet_values.row_dicts,
    )

    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Breakdown created"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Breakdown Created.", type="log")
    )

  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))
    
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error")
    )