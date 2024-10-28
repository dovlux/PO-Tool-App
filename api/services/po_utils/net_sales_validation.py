from typing import List, Dict

from api.crud.settings import get_breakdown_net_sales_settings
from api.crud.purchase_orders import add_log_to_purchase_order, update_purchase_order, get_purchase_order
from api.services.google_api.sheets_utils import get_row_dicts_from_spreadsheet, post_row_dicts_to_spreadsheet 
from api.models.sheets import BreakdownProperties, WorksheetProperties
from api.models.purchase_orders import Log, UpdatePurchaseOrder

async def validate_for_net_sales(po_id: int):
  """
  This function validates the data in the worksheet and breakdown sheets of the Purchase Order
  spreadsheet to prepare for calculating the net sales.    
  """
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Validating data for Net Sales.", type="log"),
  )
  
  try:
    # Get spreadsheet_id for po using po_id
    po = get_purchase_order(id=po_id)
    spreadsheet_id = po.spreadsheet_id
    if spreadsheet_id is None:
      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Could not find spreadsheet for PO.", type="error")
      )
      update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))
      return
    
    # Get current setting for calculating net sales
    current_settings = get_breakdown_net_sales_settings()

    # Get total costs and msrps for all groups from worksheet sheet
    try:
      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Retrieving totals from worksheet sheet.", type="log"),
      )
      group_totals = await get_total_costs_and_msrps(spreadsheet_id=spreadsheet_id)

    except Exception as e:
      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message=f"Failed to retrieve totals. Error: {str(e)}", type="error")
      )
      update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))
      return

    # Get values and rows from Breakdown sheet
    breakdown_values = await get_row_dicts_from_spreadsheet(
      ss_properties=BreakdownProperties(id=spreadsheet_id)
    )
    breakdown_rows = breakdown_values.row_dicts

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Validating all breakdown rows.", type="log")
    )

    has_errors: bool = False

    # Validate and post any errors in breakdown rows
    for row in breakdown_rows:
      group: str = row["Product Group"]
      error_msgs: List[str] = []

      # Validate Total Cost
      try:
        cost = float(row["Total Cost"])
        if cost != group_totals[group]["total_cost"]:
          error_msgs.append("Total Cost does not match values in Worksheet")
      except ValueError:
        error_msgs.append("Total Cost must be a number")

      # Validate Total MSRP
      try:
        msrp = float(row["Total MSRP"])
        if msrp != group_totals[group]["total_msrp"]:
          error_msgs.append("Total MSRP does not match values in Worksheet")
      except ValueError:
        error_msgs.append("Total MSRP must be a number")

      # Validate Discount and sales share columns
      total_share = 0.0
      for marketplace in current_settings.marketplace_groups:
        discount_col = f"{marketplace} Start Discount"
        sales_col = f"{marketplace} Sales %"

        # Validate Discount column
        try:
          discount = float(row[discount_col])
          if discount > 1:
            error_msgs.append(f"Invalid {discount_col}")
        except ValueError:
          error_msgs.append(f"{discount_col} must be a number")

        # Validate Sales % column
        try:
          sales_share = float(row[sales_col])
          if sales_share < 0 or sales_share > 1:
            error_msgs.append(f"Invalid {sales_col}")
        except ValueError:
          error_msgs.append(f"{sales_col} must be a number")

      if total_share != 1:
        error_msgs.append("'Sales %' does not add up to 100%")

      if row["Confidende"] not in current_settings.confidence_discounts:
        error_msgs.append("Invalid Confidence value")

      if row["Sell-through"] not in current_settings.sell_through_options:
        error_msgs.append("Invalid Sell-through value")

      row["Errors"] = ". ".join(error_msgs)
      if error_msgs:
        has_errors = True

    if has_errors:
      await post_row_dicts_to_spreadsheet(
        ss_properties=BreakdownProperties(id=spreadsheet_id), row_dicts=breakdown_rows,
      )

      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Net Sales)")
      )

      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Errors found and posted to worksheet.", type="error")
      )

    else:
      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Breakdown content validated", type="log")
      )

      return breakdown_values
    
  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error")
    )

async def get_total_costs_and_msrps(spreadsheet_id: str) -> Dict[str, Dict[str, float]]:
  worksheet_values = await get_row_dicts_from_spreadsheet(
    ss_properties=WorksheetProperties(id=spreadsheet_id),
  )

  worksheet_rows = worksheet_values.row_dicts

  group_totals: Dict[str, Dict[str, float]] = {}

  for row in worksheet_rows:
    group: str = row["Group"]
    qty = int(row["Qty"])
    if group not in group_totals:
      group_totals[group] = {"total_cost": 0.0, "total_msrp": 0.0}
    group_totals[group]["total_cost"] = float(row["Unit Cost"]) * qty
    group_totals[group]["total_msrp"] = float(row["Retail"]) * qty

  return group_totals
