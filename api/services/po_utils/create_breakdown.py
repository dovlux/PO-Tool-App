from fastapi import HTTPException, status
from typing import Dict, Any

from api.crud.settings import get_breakdown_net_sales_settings
from api.services.po_utils.breakdown_validation import validate_worksheet_for_breakdown
from api.services.cached_data.sales_reports import get_updated_sales_reports_rows
from api.services.cached_data.marketplaces import get_updated_marketplaces_to_groups
from api.crud.purchase_orders import update_purchase_order, add_log_to_purchase_order, get_purchase_order
from api.models.sheets import RelevantSalesProperties, WorksheetProperties, RowDicts, BreakdownProperties
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
    id=po_id, log=Log(user="Internal", message="Creating breakdown.", type="log"),
  )
  
  try:
    # Retrieve recents sales reports for breakdown
    sales_reports_rows = get_updated_sales_reports_rows().row_dicts
    
    groups: set[str] = set()
    brand_gender_types: set[str] = set()
    group_to_brand_gender_type: dict[str, str] = {}

    # Get brand_gender_type, group, total cost, and total msrp for each row in worksheet
    for row in worksheet_values.row_dicts:
      brand_gender_type: str = f"{row['Brand'].lower()} {row['Gender']} {row['Category']}"
      brand_gender_types.add(brand_gender_type)
      row["BrandGenderType"] = brand_gender_type

      group: str = f"{row['Brand']} {row['Item Type']} {row['Grade']}"
      groups.add(group)
      row["Group"] = group

      group_to_brand_gender_type[group] = brand_gender_type

      row["Total Cost"] = float(row["Unit Cost"]) * int(row["Qty"])
      row["Total Msrp"] = float(row["Retail"]) * int(row["Qty"])

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Compiled worksheet data.", type="log"),
    )

    # Get relevant sales for products in the PO
    relevant_sales_rows = [
      sales_row for sales_row in sales_reports_rows
      if sales_row["Order Date"]
      and sales_row["Brand Gender Category"] in brand_gender_types
    ]

    # Retrieve marketplace-to-group dict
    current_settings = get_breakdown_net_sales_settings()
    marketplace_groups = current_settings.marketplace_groups
    marketplace_to_groups = get_updated_marketplaces_to_groups()

    # Get sales and msrp data by marketplace for each brand-gender-type
    brand_gender_type_data = {
      brand_gndr_type: {
        "totals": { "total_sales": 0.0 },
        **{
          marketplace: { "total_sales": 0.0, "total_msrp": 0.0 }
          for marketplace in marketplace_groups
        }
      } for brand_gndr_type in brand_gender_types
    }

    # Add sales data from each sales row to brand-gender-type-data
    for row in relevant_sales_rows:
      sales = row["Grand Total + Adjustmensts - Tax + Accrual Refunds"]
      msrp = row["MSRP"]
      marketplace = marketplace_to_groups[row["Marketplace"]]

      entry_to_update = brand_gender_type_data[row["Brand Gender Category"]]
      entry_to_update["totals"]["total_sales"] += sales
      entry_to_update[marketplace]["total_sales"] += sales
      entry_to_update[marketplace]["total_msrp"] += msrp

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Compiled relevant sales data.", type="log"),
    )

    # Calculate Discount, Market Share, and Profit-to-Msrp for each marketplace
    for brand_gndr_type in brand_gender_types:
      sales_data = brand_gender_type_data[brand_gndr_type]
      total_sales = sales_data["totals"]["total_sales"]
      market_share = 0.0

      for marketplace in marketplace_groups:
        marketplace_data = sales_data[marketplace]
        sales = marketplace_data["total_sales"]
        msrp = marketplace_data["total_msrp"]

        if not total_sales:
          marketplace_data["market_share"] = 0.25
        else:
          marketplace_data["market_share"] = 0 if not sales else round(sales / total_sales, 2)
        market_share += marketplace_data["market_share"]
        marketplace_data["discount"] = round(1 - (0 if not sales else sales / msrp), 2)

      # Ensure sum of market share equals 1
      if market_share != 1:
        remainder = 1 - market_share
        marketplace_with_highest_share = max(
          sales_data, key=lambda k: sales_data[k]["market_share"]
        )
        sales_data[marketplace_with_highest_share]["market_share"] += remainder

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Compiled relevant market data.", type="log"),
    )

    # Initialize list of row_dicts for Breakdown sheet
    breakdown_row_dicts = RowDicts(row_dicts=[])

    # Add data for each product group to breakdown-row-dicts
    for group in groups:
      brand_gender_type = group_to_brand_gender_type[group]

      total_cost = sum(
        (row["Total Cost"] for row in worksheet_values.row_dicts
        if row["Group"] == group), 0.0
      )

      total_msrp = sum(
        (row["Total Msrp"] for row in worksheet_values.row_dicts
        if row["Group"] == group), 0.0
      )

      row_dict: Dict[str, Any] = {
        "Product Group": group,
        "Total Cost": total_cost,
        "Total MSRP": total_msrp,
      }

      # Add marketplace data to row-dict
      for marketplace in marketplace_groups:
        market_data = brand_gender_type_data[brand_gender_type][marketplace]
        row_dict[f"{marketplace} Start Discount"] = market_data["discount"]
        row_dict[f"{marketplace} Sales %"] = market_data["market_share"]

      # Add compiled row-dict to breakdown-row-dicts
      breakdown_row_dicts.row_dicts.append(row_dict)

    # Sort breakdown rows based on Group names
    sorted_row_dicts = sorted(breakdown_row_dicts.row_dicts, key=lambda x: x["Product Group"])

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Compiled breakdown rows.", type="log"),
    )

    # Post Breakdown to breakdown sheet
    await sheets_utils.post_row_dicts_to_spreadsheet(
      ss_properties=BreakdownProperties(id=worksheet_values.spreadsheet_id),
      row_dicts=sorted_row_dicts,
    )

    # Post relevant sales to relevant sales sheet
    await sheets_utils.post_row_dicts_to_spreadsheet(
      ss_properties=RelevantSalesProperties(id=worksheet_values.spreadsheet_id),
      row_dicts=relevant_sales_rows,
    )

    # Post updated worksheet to worksheet
    await sheets_utils.post_row_dicts_to_spreadsheet(
      ss_properties=WorksheetProperties(id=worksheet_values.spreadsheet_id),
      row_dicts=worksheet_values.row_dicts,
    )

    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Breakdown Created"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="Breakdown Created.", type="log")
    )

  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))
    
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error")
    )