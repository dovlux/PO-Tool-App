from typing import List, Dict, Any

from api.services.po_utils.net_sales_validation import validate_for_net_sales
from api.crud.settings import get_breakdown_net_sales_settings
from api.crud.purchase_orders import update_purchase_order, add_log_to_purchase_order, get_purchase_order
from api.services.google_api.sheets_utils import post_row_dicts_to_spreadsheet
from api.models.purchase_orders import Log, UpdatePurchaseOrder
from api.models.sheets import BreakdownProperties
from api.models.settings import BreakdownNetSalesSettings

async def calculate_net_sales(po_id: int):
  try:
    current_settings = get_breakdown_net_sales_settings()

    po = get_purchase_order(id=po_id)

    breakdown_values = await validate_for_net_sales(po=po, current_settings=current_settings)
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
      breakdown_rows=breakdown_values.row_dicts, current_settings=current_settings,
      products_cost=products_cost, total_cost=total_cost,
    )

    await post_row_dicts_to_spreadsheet(
      ss_properties=BreakdownProperties(id=breakdown_values.spreadsheet_id),
      row_dicts=breakdown_values.row_dicts,
    )

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Posted Net Sales.", type="log"),
    )

    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Net Sales Calculated"))

  except Exception as e:
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error")
    )

    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

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
  breakdown_rows: List[Dict[str, Any]], current_settings: BreakdownNetSalesSettings,
  products_cost: float, total_cost: float,
):
  ratio = total_cost / products_cost

  for row in breakdown_rows:
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