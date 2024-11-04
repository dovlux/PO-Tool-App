from typing import List, Any
from pydantic import BaseModel
from fastapi import HTTPException

from api.models.sheets import WorksheetPropertiesNonAts, ValidationProperties, SheetValues
from api.models.purchase_orders import UpdatePurchaseOrder, Log
from api.crud.purchase_orders import get_purchase_order, update_purchase_order, add_log_to_purchase_order
from api.services.google_api import sheets_utils
from api.services.cached_data.item_types import get_updated_item_types_rows

class ValidationData(BaseModel):
  brands: List[str]
  general_types: List[str]

async def validate_worksheet_for_breakdown(po_id: int) -> SheetValues | None:
  """
  This function validates all user input in the PO Worksheet for breakdown
  """
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Validating worksheet contents.", type="log")
  )

  try:
    # Retrieve purchase order data and get the spreadsheet id of the worksheet.
    purchase_order = get_purchase_order(id=po_id)
    worksheet_id = purchase_order.spreadsheet_id

    if worksheet_id is None:
      raise Exception("Could not find spreadsheet associated with this purchase order.")

    # Retrieve values from the worksheet.
    try:
      worksheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
        ss_properties=WorksheetPropertiesNonAts(id=worksheet_id)
      )
    except HTTPException as e:
      if e.detail == "Sheet has no cell values in non-header rows.":
        update_purchase_order(
          id=po_id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Breakdown)")
        )

        add_log_to_purchase_order(
          id=po_id, log=Log(
            user="Internal", message="Worksheet is empty.", type="error"
          )
        )
        
        return
      else:
        raise

    worksheet_row_dicts = worksheet_values.row_dicts

    validation_data = await get_validation_data(worksheet_id=worksheet_id)

    has_errors = False

    # Validate each row in worksheet
    for row in worksheet_row_dicts:
      error_msgs: List[str] = []

      # validate brand
      brand: str = row["Brand"]
      if brand not in validation_data.brands:
        error_msgs.append("Invalid Brand")

      # validate item type
      item_type: str = row["Item Type"]
      if item_type not in validation_data.general_types:
        error_msgs.append("Invalid Type")
      else:
        item_types_rows = get_updated_item_types_rows()
        item_type_data = next(
          (item_row for item_row in item_types_rows.row_dicts
          if item_row["ProductTypeName"] == item_type),
          None
        )
        if item_type_data is None:
          error_msgs.append("Unknown Type")
        else:
          row["Category"] = item_type_data.get("Reporting Category", "")
          row["Gender"] = item_type_data.get("Gender", "")

      # validate retail, unit cost, and qty
      for column in ["Retail", "Unit Cost", "Qty"]:
        value = row[column]
        if is_valid_float(value=value):
          num = float(value)
          if num <= 0:
            error_msgs.append(f"{column} must be greater than zero")
        else:
          error_msgs.append(f"{column} requires a number")

      # validate grade
      grade: str = row["Grade"]
      if not grade:
        error_msgs.append("Invalid Grade")
        
      row["Errors"] = ". ".join(error_msgs)

      if error_msgs:
        has_errors = True

    if has_errors:
      await sheets_utils.post_row_dicts_to_spreadsheet(
        ss_properties=WorksheetPropertiesNonAts(id=worksheet_id),
        row_dicts=worksheet_row_dicts,
      )

      update_purchase_order(
        id=po_id, updates=UpdatePurchaseOrder(status="Errors in worksheet (Breakdown)")
      )

      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Errors found and posted to worksheet.", type="error")
      )

    else:
      add_log_to_purchase_order(
        id=po_id, log=Log(user="Internal", message="Worksheet content validated", type="log")
      )

      return worksheet_values
    
  except Exception as e:
    update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message=str(e), type="error")
    )

async def get_validation_data(worksheet_id: str) -> ValidationData:
  # Retrieve validation data from validation sheet in PO worksheet.
  validation_values = await sheets_utils.get_row_dicts_from_spreadsheet(
    ss_properties=ValidationProperties(id=worksheet_id)
  )
  validation_row_dicts = validation_values.row_dicts

  brands: set[str] = set()
  general_types: set[str] = set()

  for row in validation_row_dicts:
    brand: str = row["Brand"]
    if brand:
      brands.add(brand)

    general_type: str = row["General Types"]
    if general_type:
      general_types.add(general_type)

  return ValidationData(brands=list(brands), general_types=list(general_types))

def is_valid_float(value: Any) -> bool:
  try:
    float(value)
    return True
  except ValueError:
    return False

