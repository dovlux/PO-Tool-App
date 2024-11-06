from typing import List, Dict

from api.crud.purchase_orders import add_log_to_purchase_order, update_purchase_order
from api.services.google_api.sheets_utils import get_row_dicts_from_spreadsheet, post_row_dicts_to_spreadsheet 
from api.services.utils.send_emails import send_error_email
from api.models.sheets import BreakdownProperties
from api.models.purchase_orders import Log, UpdatePurchaseOrder, PurchaseOrderOut
from api.models.sheets import SheetValues, RowDicts
from api.models.settings import BreakdownNetSalesSettings

async def validate_for_net_sales(
  po: PurchaseOrderOut, current_settings: BreakdownNetSalesSettings,
  worksheet_rows: RowDicts, spreadsheet_id: str,
) -> SheetValues | None:
  """
  This function validates the data in the worksheet and breakdown sheets of the Purchase Order
  spreadsheet to prepare for calculating the net sales.    
  """
  add_log_to_purchase_order(
    id=po.id, log=Log(user="Internal", message="Validating data for Net Sales.", type="log"),
  )
  
  try:
    # Get total costs and msrps for all groups from worksheet sheet
    try:
      add_log_to_purchase_order(
        id=po.id, log=Log(user="Internal", message="Retrieving totals from worksheet sheet.", type="log"),
      )
      group_totals = await get_total_costs_and_msrps(worksheet_rows=worksheet_rows)

    except Exception as e:
      add_log_to_purchase_order(
        id=po.id, log=Log(user="Internal", message=f"Failed to retrieve totals. Error: {str(e)}", type="error")
      )
      update_purchase_order(id=po.id, updates=UpdatePurchaseOrder(status="Internal Error"))
      await send_error_email(subject=f"PO #{po.id} Net Sales Error", error_message=str(e))
      return

    # Get values and rows from Breakdown sheet
    breakdown_values = await get_row_dicts_from_spreadsheet(
      ss_properties=BreakdownProperties(id=spreadsheet_id)
    )
    breakdown_rows = breakdown_values.row_dicts

    add_log_to_purchase_order(
      id=po.id, log=Log(user="Internal", message="Validating all breakdown rows.", type="log")
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
          else:
            total_share += sales_share
        except ValueError:
          error_msgs.append(f"{sales_col} must be a number")

      if total_share != 1:
        error_msgs.append("'Sales %' does not add up to 100%")

      if row["Confidence"] not in current_settings.confidence_discounts:
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
        id=po.id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Net Sales)")
      )

      add_log_to_purchase_order(
        id=po.id, log=Log(user="Internal", message="Errors found and posted to worksheet.", type="error")
      )

    else:
      add_log_to_purchase_order(
        id=po.id, log=Log(user="Internal", message="Breakdown content validated", type="log")
      )

      return breakdown_values
    
  except Exception as e:
    update_purchase_order(id=po.id, updates=UpdatePurchaseOrder(status="Internal Error"))

    add_log_to_purchase_order(
      id=po.id, log=Log(user="Internal", message=str(e), type="error")
    )

    await send_error_email(subject=f"PO #{po.id} Net Sales Error", error_message=str(e))

async def get_total_costs_and_msrps(worksheet_rows: RowDicts) -> Dict[str, Dict[str, float]]:
  group_totals: Dict[str, Dict[str, float]] = {}

  for row in worksheet_rows.row_dicts:
    group: str = row["Group"]
    qty = int(row["Qty"])
    if group not in group_totals:
      group_totals[group] = {"total_cost": 0.0, "total_msrp": 0.0}
    group_totals[group]["total_cost"] += float(row["Unit Cost (USD)"]) * qty
    group_totals[group]["total_msrp"] += float(row["Retail"]) * qty

  return group_totals