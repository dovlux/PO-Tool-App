from typing import List, Dict, Any

from api.services.po_utils.net_sales_validation import validate_for_net_sales
from api.crud.settings import get_breakdown_net_sales_settings
from api.crud.purchase_orders import update_purchase_order, add_log_to_purchase_order
from api.services.google_api.sheets_utils import post_row_dicts_to_spreadsheet
from api.models.purchase_orders import Log, UpdatePurchaseOrder
from api.models.sheets import BreakdownProperties
from api.models.settings import BreakdownNetSalesSettings

async def calculate_net_sales(po_id: int):
  try:
    current_settings = get_breakdown_net_sales_settings()

    breakdown_values = await validate_for_net_sales(po_id=po_id, current_settings=current_settings)
    if breakdown_values is None:
      return
    
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Adding Gross, Net, and Selling Fees.", type="log"),
    )

    add_gross_net_and_fees(
      breakdown_rows=breakdown_values.row_dicts, current_settings=current_settings,
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
    confidence_adj = current_settings.confidence_discounts[row["Confidence"]]

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