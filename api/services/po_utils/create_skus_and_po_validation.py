from typing import List, Dict, Set
from fastapi import HTTPException

from api.services.cached_data.brand_codes import get_updated_brand_codes
from api.services.cached_data.item_type_acronyms import get_updated_item_type_acronyms
from api.services.cached_data.valid_sizes import get_updated_valid_sizes
from api.services.google_api.sheets_utils import get_row_dicts_from_spreadsheet, post_row_dicts_to_spreadsheet
from api.crud.purchase_orders import add_log_to_purchase_order
from api.services.utils.mpn_formatter import remove_special_chars
from api.models.sheets import SheetValues, WorksheetPropertiesNonAts, WorksheetPropertiesAts, BreakdownProperties
from api.models.purchase_orders import Log

async def validate_worksheet_for_po_non_ats(spreadsheet_id: str, po_id: int) -> SheetValues | None:
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Validating Worksheet data for PO.", type="log"),
  )

  # Retrieve values from worksheet sheet (with exception for empty worksheet)
  try:
    worksheet_values = await get_row_dicts_from_spreadsheet(
      ss_properties=WorksheetPropertiesNonAts(id=spreadsheet_id),
    )
  except HTTPException as e:
    if e.detail == "Sheet has no cell values in non-header rows.":
      add_log_to_purchase_order(
        id=po_id, log=Log(
          user="Internal", message="Worksheet is empty.", type="error"
        )
      )
      return
    else:
      raise

  # If there are rows without SKUs
  has_new_skus = not all(row["ProductID"] for row in worksheet_values.row_dicts)
  if has_new_skus:
    # Retrieve brand codes, item type codes, and valid sizes from cache
    brand_codes = get_updated_brand_codes()
    item_type_acronyms = get_updated_item_type_acronyms()
    valid_sizes = get_updated_valid_sizes()

    # Create a dict of all mpns and their product colors in the worksheet
    mpn_color_dict: Dict[str, Set[str]] = {}
    for row in worksheet_values.row_dicts:
      if row["MPN"] not in mpn_color_dict:
        mpn_color_dict[row["MPN"]] = set()
      mpn_color_dict[row["MPN"]].add(row["Color"])

    # Create a dict of all brand-mpns and their description and item types
    brand_mpn_description_item_type: Dict[str, Dict[str, str]] = {}
    for row in worksheet_values.row_dicts:
      brand_mpn_description_item_type[row["Brand"] + remove_special_chars(mpn=row["MPN"])] = {
        "description": row["Description"],
        "item_type": row["Item Type"],
      }

  # initialize a variable (is there any errors in the entire worksheet?)
  has_errors = False

  # Validate all rows in the worksheet
  for row in worksheet_values.row_dicts:
    # Initialize a list of error messages for current row
    error_msgs: List[str] = []

    # Validation for rows that do not have a SKU
    if not row["ProductID"]:
      # Validate brand
      error_msgs.append(
        validate_brand(
          brand=str(row["Brand"]), is_ats=False, brand_codes=brand_codes # type: ignore
        )
      )

      # Retrieve matching data for current row brand+mpn
      mpn_removed_chars = remove_special_chars(mpn=row["MPN"])
      matching_row_data = brand_mpn_description_item_type[row["Brand"] + mpn_removed_chars] # type: ignore
      
      # Validate description
      error_msgs.append(
        validate_description(
          description=str(row["Description"]),
          matching_description=matching_row_data["description"], # type: ignore
        )
      )

      # Validate item type
      error_msgs.append(
        validate_item_type(
          item_type=str(row["Item Type"]), is_ats=False,
          matching_item_type=matching_row_data["item_type"], # type: ignore
          item_types=item_type_acronyms, # type: ignore
        )
      )

      # Validate color
      error_msgs.append(
        validate_color(color=row["Color"], mpn_colors=mpn_color_dict[row["MPN"]]) # type: ignore
      )
      
      # Validate size
      error_msgs.append(
        validate_size(
          size=str(row["Size"]), is_ats=False,
          valid_sizes=valid_sizes,  # type: ignore
        )
      )

      # Validate MPN
      error_msgs.append(validate_mpn(mpn=str(row["MPN"])))
      
      # Validate msrp
      error_msgs.append(validate_retail(retail=str(row["Retail"])))

    # Validation for all rows (including ones that already have a SKU)

    # Validate unit cost
    error_msgs.append(validate_unit_cost(unit_cost=str(row["Unit Cost"])))
    
    # Validate qty
    error_msgs.append(validate_qty(qty=str(row["Qty"])))

    # Validate unit cost (usd)
    error_msgs.append(validate_unit_cost(unit_cost=str(row["Unit Cost (USD)"]), usd=True))
    
    # Validate weighted cost
    error_msgs.append(validate_weighted_cost(weighted_cost=str(row["Weighted Cost"])))
    
    # Validate group
    error_msgs.append(validate_group(group=str(row["Group"])))

    # Post updated error messages to errors column
    error_msg_string = ". ".join(msg for msg in error_msgs if msg)
    row["Errors"] = error_msg_string

    # If there are errors in current row
    if error_msg_string:
      has_errors = True # change has_errors (entire sheet) to True
    else:
      if not row["ProductID"]:
        # add brand and type code to rows for use when creating SKUs
        row["Brand Code"] = brand_codes[row["Brand"]] # type: ignore
        row["Type Code"] = item_type_acronyms[row["Item Type"]] # type: ignore

  # If there are no errors so-far in the worksheet
  if not has_errors:
    # Validate group data matches data in breakdown sheet
    has_errors = await validate_group_totals(
      spreadsheet_id=spreadsheet_id, worksheet_values=worksheet_values,
    )

  # If there are any errors in the worksheet
  if has_errors:
    # Post updated rows (with errors) back to worksheet
    await post_row_dicts_to_spreadsheet(
      ss_properties=WorksheetPropertiesNonAts(id=spreadsheet_id),
      row_dicts=worksheet_values.row_dicts,
    )

    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal", message="Errors found and posted to Worksheet.", type="error",
      ),
    )

    return
  
  else:
    return worksheet_values # Return updated worksheet values for SKU creation
  
async def validate_worksheet_for_po_ats(spreadsheet_id: str, po_id: int) -> SheetValues | None:
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Validating Worksheet data for PO.", type="log"),
  )

  # Retrieve worksheet values (with exception for empty worksheet)
  try:
    worksheet_values = await get_row_dicts_from_spreadsheet(
      ss_properties=WorksheetPropertiesAts(id=spreadsheet_id),
    )
  except HTTPException as e:
    if e.detail == "Sheet has no cell values in non-header rows.":
      add_log_to_purchase_order(
        id=po_id, log=Log(
          user="Internal", message="Worksheet is empty.", type="error"
        )
      )
      return
    else:
      raise

  # Create dict of mpns and their colors in the worksheet
  mpn_color_dict: Dict[str, Set[str]] = {}
  for row in worksheet_values.row_dicts:
    if row["MPN"] not in mpn_color_dict:
      mpn_color_dict[row["MPN"]] = set()
    mpn_color_dict[row["MPN"]].add(row["Color"])

  # Create dict of mpns and their description and item types
  mpn_description_item_type: Dict[str, Dict[str, str]] = {}
  for row in worksheet_values.row_dicts:
    mpn_description_item_type[remove_special_chars(mpn=row["MPN"])] = {
      "description": row["Description"],
      "item_type": row["Item Type"],
    }

  # Initialize has_errors variable (are there any errors in entire worksheet?)
  has_errors = False

  for row in worksheet_values.row_dicts:
    error_msgs: List[str] = []

    # Validate brand
    error_msgs.append(validate_brand(brand=str(row["Brand"]), is_ats=True))

    mpn_removed_chars = remove_special_chars(mpn=row["MPN"])
    matching_row_data = mpn_description_item_type[mpn_removed_chars]
      
    # Validate description
    error_msgs.append(
      validate_description(
        description=str(row["Description"]), matching_description=matching_row_data["description"],
      )
    )

    # Validate item type
    error_msgs.append(
      validate_item_type(
        item_type=str(row["Item Type"]), is_ats=True,
        matching_item_type=matching_row_data["item_type"],
      )
    )

    # Validate color
    error_msgs.append(
      validate_color(color=row["Color"], mpn_colors=mpn_color_dict[row["MPN"]])
    )
      
    # Validate size
    error_msgs.append(validate_size(size=str(row["Size"]), is_ats=True))

    # Validate mpn
    error_msgs.append(validate_mpn(mpn=str(row["MPN"])))
      
    # Validate msrp
    error_msgs.append(validate_retail(retail=str(row["Retail"])))

    # Validate unit cost
    error_msgs.append(validate_unit_cost(unit_cost=str(row["Unit Cost"])))
    
    # Validate qty
    error_msgs.append(validate_qty(qty=str(row["Qty"])))

    # Post final error messages to Errors column of current row
    error_msg_string = ". ".join(msg for msg in error_msgs if msg)
    row["Errors"] = error_msg_string

    if error_msg_string:
      has_errors = True

  # If there are any errors in entire worksheet
  if has_errors:
    # Post updated rows (with errors) to worksheet
    await post_row_dicts_to_spreadsheet(
      ss_properties=WorksheetPropertiesNonAts(id=spreadsheet_id),
      row_dicts=worksheet_values.row_dicts,
    )

    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal", message="Errors found and posted to Worksheet.", type="error",
      ),
    )

    return
  
  else:
    return worksheet_values # Return worksheet values for SKU creation

def validate_brand(brand: str, is_ats: bool, brand_codes: Dict[str, str] = {}) -> str:
  if not brand:
    return "Missing Brand"
  elif not is_ats and brand not in brand_codes:
    return "Invalid Brand"
  return ""

def validate_description(description: str, matching_description: str) -> str:
  if not description:
    return "Missing Description"
  elif description != matching_description:
    return "Different description found for same Brand & MPN on this sheet"
  return ""

def validate_item_type(
  item_type: str, is_ats: bool, matching_item_type: str, item_types: Dict[str, str] = {},
) -> str:
  if not item_type:
    return "Missing Item Type"
  elif not is_ats and item_type not in item_types:
    return "Invalid Item Type"
  elif item_type != matching_item_type:
    return "Different item type found for same Brand & MPN on this sheet"
  return ""

def validate_color(color: str, mpn_colors: Set[str]) -> str:
  if not color:
    return "Missing Color"
  elif len(mpn_colors) > 1:
    return "This MPN has more than one color assigned in this sheet"
  return ""

def validate_size(size: str, is_ats: bool, valid_sizes: Set[str] = set()) -> str:
  if not size:
    return "Missing Size"
  elif not is_ats and size not in valid_sizes:
    return "Invalid Size"
  return ""

def validate_mpn(mpn: str) -> str:
  return "" if mpn else "Missing MPN"

def validate_retail(retail: str) -> str:
  if not retail:
    return "Missing Retail"
  else:
    try:
      msrp = float(retail)
      if msrp <= 0:
        raise ValueError
    except ValueError:
      return "Retail is not a valid number"
  return ""

def validate_unit_cost(unit_cost: str, usd: bool = False) -> str:
  col_name = " (USD)" if usd else ""
  if not unit_cost:
    return f"Missing Unit Cost{col_name}"
  else:
    try:
      cost = float(unit_cost)
      if cost <= 0:
        raise ValueError
    except ValueError:
      return f"Unit Cost{col_name} is not a valid number"
  return ""

def validate_weighted_cost(weighted_cost: str) -> str:
  if not weighted_cost:
    return "Missing Weighted Cost"
  else:
    try:
      cost = float(weighted_cost)
      if cost <= 0:
        raise ValueError
    except ValueError:
      return "Weighted Cost is not a valid number"
  return ""

def validate_qty(qty: str) -> str:
  if not qty:
    return "Missing Qty"
  else:
    try:
      quantity = int(qty)
      if quantity <= 0:
        raise ValueError
    except ValueError:
      return "Qty is not a valid number"
  return ""

def validate_group(group: str) -> str:
  return "" if group else "Missing Group"

async def validate_group_totals(
  spreadsheet_id: str, worksheet_values: SheetValues,
) -> bool:
  has_errors: bool = False

  # Validate that the groups and numbers (cost & msrp) match the breakdown sheet
  
  # Create set of groups in worksheet
  worksheet_groups = set([row["Group"] for row in worksheet_values.row_dicts])

  # Create dict of cost, msrp, and weighted cost totals for worksheet groups
  worksheet_group_totals: Dict[str, Dict[str, float]] = {}

  for group in worksheet_groups:
    total_cost = sum(
      float(row["Unit Cost (USD)"]) * int(row["Qty"]) for row in worksheet_values.row_dicts
      if row["Group"] == group
    )
    total_msrp = sum(
      float(row["Retail"]) * int(row["Qty"]) for row in worksheet_values.row_dicts
      if row["Group"] == group
    )
    total_weighted_cost = sum(
      float(row["Weighted Cost"]) * int(row["Qty"]) for row in worksheet_values.row_dicts
      if row["Group"] == group
    )

    # Add current group totals to group-totals dict
    worksheet_group_totals[group] = {
      "cost": total_cost,
      "msrp": total_msrp,
      "weighted_cost": total_weighted_cost,
    }

  # Retrieve breakdown sheet values
  breakdown_values = await get_row_dicts_from_spreadsheet(
    ss_properties=BreakdownProperties(id=spreadsheet_id),
  )

  # Create list of breakdown groups, and a dict of the group totals
  breakdown_groups: List[str] = []
  breakdown_group_totals: Dict[str, Dict[str, float]] = {}

  # Populate the breakdown data from the breakdown rows
  for row in breakdown_values.row_dicts:
    group: str = row["Product Group"]
    breakdown_groups.append(group)
    breakdown_group_totals[group] = {
      "cost": float(row["Total Cost"]),
      "msrp": float(row["Total MSRP"]),
      "weighted_cost": float(row["Weighted Cost"]),
    }

  for row in worksheet_values.row_dicts:
    error_msgs: List[str] = []

    group = row["Group"]

    if group not in worksheet_groups:
      error_msgs.append("Group not found in Breakdown")
    else:
      current_group_totals = worksheet_group_totals[group]
      matching_totals = breakdown_group_totals[group]

      if current_group_totals["cost"] != matching_totals["cost"]:
        error_msgs.append("Unit Cost (USD) does not match cost totals for this group in breakdown")
      if current_group_totals["msrp"] != matching_totals["msrp"]:
        error_msgs.append("Retail totals for this group does not match total MSRP in breakdown")
      if current_group_totals["weighted_cost"] != matching_totals["weighted_cost"]:
        error_msgs.append("Weighted Cost totals for this group does not match breakdown totals")

    error_msg_string = ". ".join(msg for msg in error_msgs if msg)
    row["Errors"] = error_msg_string

    if error_msg_string:
      has_errors = True

  return has_errors