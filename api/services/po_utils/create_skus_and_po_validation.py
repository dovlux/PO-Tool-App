from typing import List, Dict, Set

from api.services.cached_data.brand_codes import get_updated_brand_codes
from api.services.cached_data.item_type_acronyms import get_updated_item_type_acronyms
from api.services.cached_data.valid_sizes import get_updated_valid_sizes
from api.services.google_api.sheets_utils import get_row_dicts_from_spreadsheet, post_row_dicts_to_spreadsheet
from api.models.sheets import SheetValues, WorksheetProperties

async def validate_worksheet_for_po(
  spreadsheet_id: str, is_ats: bool,
) -> SheetValues | None:
  worksheet_values = await get_row_dicts_from_spreadsheet(
    ss_properties=WorksheetProperties(id=spreadsheet_id),
  )

  has_new_skus = not all(row["ProductID"] for row in worksheet_values.row_dicts)
  if has_new_skus:
    brand_codes = get_updated_brand_codes()
    item_type_acronyms = get_updated_item_type_acronyms()
    valid_sizes = get_updated_valid_sizes()

    mpn_color_dict: Dict[str, List[str]] = {}
    for row in worksheet_values.row_dicts:
      if row["MPN"] not in mpn_color_dict:
        mpn_color_dict[row["MPN"]] = []
      mpn_color_dict[row["MPN"]].append(row["Color"])

  has_errors = False

  for row in worksheet_values.row_dicts:
    error_msgs: List[str] = []

    if not row["ProductID"]:
      error_msgs.append(
        validate_brand(
          brand=str(row["Brand"]), is_ats=is_ats, brand_codes=brand_codes # type: ignore
        )
      )
      error_msgs.append(validate_description(description=str(row["Description"])))
      error_msgs.append(
        validate_item_type(
          item_type=str(row["Item Type"]), is_ats=is_ats, item_types=item_type_acronyms # type: ignore
        )
      )
      error_msgs.append(validate_color(color=str(row["Color"]), mpn_colors=mpn_color_dict)) # type: ignore
      error_msgs.append(
        validate_size(size=str(row["Size"]), is_ats=is_ats, valid_sizes=valid_sizes) # type: ignore
      )
      error_msgs.append(validate_mpn(mpn=str(row["MPN"])))
      error_msgs.append(validate_retail(retail=str(row["Retail"])))

    error_msgs.append(validate_unit_cost(unit_cost=str(row["Unit Cost"])))
    error_msgs.append(validate_qty(qty=str(row["Qty"])))

    if not is_ats:
      error_msgs.append(validate_unit_cost(unit_cost=str(row["Unit Cost (USD)"]), usd=True))
      error_msgs.append(validate_weighted_cost(weighted_cost=str(row["Weighted Cost"])))
      error_msgs.append(validate_group(group=str(row["Group"])))

    error_msg_string = ". ".join(error_msgs)
    row["Errors"] = error_msg_string
    if error_msg_string:
      has_errors = True
    else:
      if not is_ats and not row["ProductID"]:
        row["Brand Code"] = brand_codes[row["Brand"]] # type: ignore
        row["Type Code"] = item_type_acronyms[row["Item Type"]] # type: ignore

  if has_errors:
    await post_row_dicts_to_spreadsheet(
      ss_properties=WorksheetProperties(id=spreadsheet_id),
      row_dicts=worksheet_values.row_dicts,
    )
    return
  
  else:
    return worksheet_values

def validate_brand(brand: str, is_ats: bool, brand_codes: Dict[str, str]) -> str:
  if not brand:
    return "Missing Brand"
  elif not is_ats and brand not in brand_codes:
    return "Invalid Brand"
  return ""

def validate_description(description: str) -> str:
  if not description:
    return "Missing Description"
  return ""

def validate_item_type(item_type: str, is_ats: bool, item_types: Dict[str, str]) -> str:
  if not item_type:
    return "Missing Item Type"
  elif not is_ats and item_type not in item_types:
    return "Invalid Item Type"
  return ""

def validate_color(color: str, mpn_colors: Dict[str, List[str]]) -> str:
  if not color:
    return "Missing Color"
  elif len(mpn_colors[color]) > 1:
    return "This MPN has more than one color assigned in this sheet"
  return ""

def validate_size(size: str, is_ats: bool, valid_sizes: Set[str]) -> str:
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