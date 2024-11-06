from typing import List, Dict, Any
from fastapi import  HTTPException, status

from api.services.po_utils.net_sales_validation import validate_for_net_sales
from api.crud.settings import get_breakdown_net_sales_settings
from api.crud.purchase_orders import update_purchase_order, add_log_to_purchase_order, get_purchase_order
from api.services.google_api.sheets_utils import post_row_dicts_to_spreadsheet, get_row_dicts_from_spreadsheet
from api.services.google_api.sheets import post_values
from api.services.utils.send_emails import send_error_email
from api.models.purchase_orders import Log, UpdatePurchaseOrder
from api.models.sheets import BreakdownProperties, WorksheetPropertiesNonAts, RowDicts, ValidationProperties
from api.models.settings import BreakdownNetSalesSettings

async def calculate_net_sales(po_id: int):
  try:
    current_settings = get_breakdown_net_sales_settings()

    po = get_purchase_order(id=po_id)

    if po.is_ats:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Calculate Net Sales does not apply to ATS Purchase Orders",
      )

    spreadsheet_id = po.spreadsheet_id
    if spreadsheet_id is None:
      add_log_to_purchase_order(
        id=po.id, log=Log(user="Internal", message="Could not find spreadsheet for PO.", type="error")
      )
      update_purchase_order(id=po.id, updates=UpdatePurchaseOrder(status="Internal Error"))
      return

    worksheet_values = await get_row_dicts_from_spreadsheet(
      ss_properties=WorksheetPropertiesNonAts(id=spreadsheet_id),
    )

    breakdown_values = await validate_for_net_sales(
      po=po, current_settings=current_settings,
      worksheet_rows=worksheet_values, spreadsheet_id=spreadsheet_id
    )
    if breakdown_values is None:
      return
    
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Adding Gross, Net, and Selling Fees.", type="log"),
    )

    add_gross_net_and_fees(
      breakdown_rows=breakdown_values.row_dicts, current_settings=current_settings,
    )

    products_cost = sum(float(row["Total Cost"]) for row in breakdown_values.row_dicts)
    fees = po.additional_fees
    total_fees = 0.0 if fees is None else fees.shipping_fees + fees.customs_fees + fees.other_fees
    total_cost = products_cost + total_fees

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Adding all projections.", type="log"),
    )

    add_all_projections(
      breakdown_rows=breakdown_values, current_settings=current_settings,
      products_cost=products_cost, total_cost=total_cost, worksheet_rows=worksheet_values
    )

    await post_row_dicts_to_spreadsheet(
      ss_properties=BreakdownProperties(id=spreadsheet_id),
      row_dicts=breakdown_values.row_dicts,
    )

    await post_row_dicts_to_spreadsheet(
      ss_properties=WorksheetPropertiesNonAts(id=spreadsheet_id),
      row_dicts=worksheet_values.row_dicts,
    )

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Posted Net Sales.", type="log"),
    )

    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Net Sales Calculated"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Changing Item Type validations.", type="log"),
    )

    validation_rows = await get_row_dicts_from_spreadsheet(
      ss_properties=ValidationProperties(id=spreadsheet_id),
    )

    types_validation = [[row["ProductTypeName"]] for row in validation_rows.row_dicts]
    cell_range = f"G2:G{len(types_validation) + 1}"

    await post_values(
      values=types_validation, spreadsheet_id=spreadsheet_id,
      sheet_name="Validation", cell_range=cell_range,
    )

  except Exception as e:
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error")
    )

    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

    await send_error_email(subject=f"PO #{po_id} Net Sales Error", error_message=str(e))

def add_gross_net_and_fees(
  breakdown_rows: List[Dict[str, Any]], current_settings: BreakdownNetSalesSettings,
) -> None:
  for row in breakdown_rows:
    msrp = float(row["Total MSRP"])
    confidence_adj = 1 - current_settings.confidence_discounts[row["Confidence"]]

    total_gross = 0.0
    total_net = 0.0

    for marketplace in current_settings.marketplace_groups:
      net_percentage = current_settings.net_sales_percentages[marketplace]
      market_share = float(row[f"{marketplace} Sales %"])
      market_discount = float(row[f"{marketplace} Start Discount"])

      gross = msrp * market_share * (1 - market_discount)
      net = gross * net_percentage

      total_gross += gross
      total_net += net

    total_gross *= confidence_adj
    total_net *= confidence_adj
    selling_fees = total_gross - total_net

    row["Projected Sales"] = total_gross
    row["Projected Fees"] = selling_fees
    row["Projected Net Sales"] = total_net

def add_all_projections(
  breakdown_rows: RowDicts, current_settings: BreakdownNetSalesSettings,
  products_cost: float, total_cost: float, worksheet_rows: RowDicts,
):
  ratio = total_cost / products_cost

  for row in breakdown_rows.row_dicts:
    weighted_cost = float(row["Total Cost"]) * ratio
    turnover_days = int(row["Sell-through"])
    turnover_months = turnover_days / 30

    holding_cost = calc_opportunity_cost(
      cost=weighted_cost, turnover_days=turnover_days,
      monthly_opportunity_cost=current_settings.monthly_opportunity_cost,
    )

    projected_profit = float(row["Projected Net Sales"]) - weighted_cost - holding_cost
    monthly_roi = (projected_profit / turnover_months) / (weighted_cost / 2)
    new_discount = weighted_cost / float(row["Total MSRP"])

    row["Holding Cost"] = holding_cost
    row["Monthly ROI"] = monthly_roi
    row["Weighted Cost"] = weighted_cost
    row["New Discount"] = new_discount
    row["Total Projected Profit"] = projected_profit

  for row in worksheet_rows.row_dicts:
    row["Weighted Cost"] = float(row["Unit Cost (USD)"]) * ratio

def calc_opportunity_cost(cost: float, turnover_days: int, monthly_opportunity_cost: int) -> float:
  daily_interest_rate = monthly_opportunity_cost / 100 / 30
  outstanding_cost = cost
  total_interest = 0.0
  daily_revenue = cost / turnover_days

  for _ in range(turnover_days):
    daily_interest = outstanding_cost * daily_interest_rate
    total_interest += daily_interest
    outstanding_cost += daily_interest
    outstanding_cost -= daily_revenue

  return total_interest