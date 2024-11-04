from typing import List, Dict, Any, Set

from api.services.utils.get_aliases_dicts import get_aliases_dicts
from api.crud.purchase_orders import add_log_to_purchase_order
from api.services.utils.mpn_formatter import remove_special_chars
from api.crud.settings import get_ats_settings, update_ats_settings
from api.services.google_api.sheets_utils import post_row_dicts_to_spreadsheet
from api.models.purchase_orders import Log
from api.models.sheets import SheetValues, WorksheetPropertiesAts, WorksheetPropertiesNonAts
from api.models.settings import UpdateAtsSkuCreationSettings

async def create_or_find_skus(
  worksheet_values: SheetValues, po_id: int, is_ats: bool,
) -> None:
  if is_ats:
    new_sku_data = create_skus_ats(worksheet_values=worksheet_values, po_id=po_id)
  else:
    new_sku_data = await create_or_find_skus_non_ats(worksheet_values=worksheet_values, po_id=po_id)
  
  ss_properties = WorksheetPropertiesAts(id=worksheet_values.spreadsheet_id) if is_ats else WorksheetPropertiesNonAts(id=worksheet_values.spreadsheet_id)
  await post_row_dicts_to_spreadsheet(
    ss_properties=ss_properties, row_dicts=worksheet_values.row_dicts,
  )
  
  if new_sku_data is None:
    return

def create_skus_ats(
  worksheet_values: SheetValues, po_id: int,
) -> List[Dict[str, Any]]:
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Assigning SKUs.", type="log"),
  )

  unique_mpns: Set[str] = set([row["MPN"] for row in worksheet_values.row_dicts])
  mpn_to_parent_sku: Dict[str, str] = {}

  for mpn in unique_mpns:
    mpn_to_parent_sku[mpn] = create_new_ats_parent_sku()

  new_skus: List[str] = []
  new_skus_data: List[Dict[str, Any]] = []

  for row in worksheet_values.row_dicts:
    parent_sku = mpn_to_parent_sku[row["MPN"]]
    row["ProductID"] = parent_sku + "/" + row["Size"]
    if row["ProductID"] in new_skus:
      continue
    new_skus.append(row["ProductID"])
    new_skus_data.append(row)
  
  add_log_to_purchase_order(
    id=po_id, log=Log(
      user="Internal", message=f"Found {len(new_skus)} new SKUs. Preparing for upload", type="log",
    ),
  )

  return new_skus_data

async def create_or_find_skus_non_ats(
  worksheet_values: SheetValues, po_id: int,
) -> List[Dict[str, Any]] | None:
  if all(row["ProductID"] for row in worksheet_values.row_dicts):
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="No rows with missing SKUs found.", type="log"),
    )

    return
  
  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Assigning SKUs.", type="log"),
  )
  
  aliases_dicts = await get_aliases_dicts()
  brand_mpn_dict = aliases_dicts["brand_mpn_dict"]
  brand_type_dict = aliases_dicts["brand_type_dict"]

  # Assign SKUs for all rows without SKUs
  for row in worksheet_values.row_dicts:
    if not row["ProductID"]:
      brand_mpn: str = row["Brand Code"] + remove_special_chars(mpn=row["MPN"])
      brand_type: str = row["Brand Code"] + "-" + row["Type Code"]

      if brand_mpn in brand_mpn_dict:
        row["existing_skus"] = brand_mpn_dict[brand_mpn]
        row["parent_sku"] = get_parent_from_sku(sku=row["existing_skus"][0])
      elif brand_type in brand_type_dict:
        highest_existing_parent_sku_number = get_highest_number_from_list_of_skus(
          skus=brand_type_dict[brand_type]
        )
        new_sku_number = highest_existing_parent_sku_number + 1
        row["parent_sku"] = brand_type + "-" + pad_sku_number(sku=str(new_sku_number), zeros=4)
        brand_type_dict[brand_type].append(row["parent_sku"])
      else:
        row["parent_sku"] = brand_type + "-0001"
        brand_type_dict[brand_type] = [row["parent_sku"]]

      row["new_sku"] = row["parent_sku"] + "/" + str(row["Size"])

  new_skus: List[str] = []
  new_skus_data: List[Dict[str, Any]] = []

  for row in worksheet_values.row_dicts:
    if "new_sku" in row:
      row["ProductID"] = row["new_sku"]
      if "existing_skus" in row and row["new_sku"] in row["existing_skus"]:
        continue
      if row["new_sku"] in new_skus:
        continue
      new_skus.append(row["new_sku"])
      new_skus_data.append(row)

  if not new_skus:
    add_log_to_purchase_order(
      id=po_id, log=Log(user="Internal", message="No new skus found.", type="log"),
    )

    return
  
  add_log_to_purchase_order(
    id=po_id, log=Log(
      user="Internal", message=f"Found {len(new_skus)} new SKUs. Preparing for upload", type="log",
    ),
  )

  return new_skus_data

def get_parent_from_sku(sku: str) -> str:
  return sku.split("/")[0]

def get_sku_number(sku: str) -> int:
  parent = sku.split("/")[0]
  num_string = parent.split("-")[2]
  return int(num_string)

def get_highest_number_from_list_of_skus(skus: List[str]) -> int:
  all_numbers: List[int] = []

  for sku in skus:
    sku_number = get_sku_number(sku=sku)
    all_numbers.append(sku_number)

  return max(all_numbers)

def pad_sku_number(sku: str, zeros: int) -> str:
  return sku.zfill(zeros)

def create_new_ats_parent_sku() -> str:
  ats_settings = get_ats_settings()
  latest_number = ats_settings.sku_number
  new_number = latest_number + 1
  update_ats_settings(UpdateAtsSkuCreationSettings(sku_number=new_number))

  return f"{ats_settings.brand_code}-{pad_sku_number(str(new_number), zeros=8)}"