from typing import List, Dict, Any, Set
import asyncio
from fastapi import HTTPException, status

from api.services.utils.get_aliases_dicts import get_aliases_dicts
from api.crud.purchase_orders import add_log_to_purchase_order, update_purchase_order
from api.services.utils.mpn_formatter import remove_special_chars, format_mpn
from api.crud.settings import get_ats_settings, update_ats_settings, get_ebay_discount_settings
from api.services.google_api.sheets_utils import post_row_dicts_to_spreadsheet
from api.services.lightspeed.upload_products_to_ls import upload_products_to_ls
from api.services.sellercloud.skus import create_skus as sc_create_skus
from api.services.sellercloud.jobs import set_job_priority_to_critical, get_job_information
from api.models.purchase_orders import Log, UpdatePurchaseOrder
from api.models.lightspeed import ImportProduct
from api.models.sellercloud import CreateProduct
from api.models.sheets import SheetValues, WorksheetPropertiesAts, WorksheetPropertiesNonAts
from api.models.settings import UpdateAtsSkuCreationSettings

async def create_or_find_skus(
  worksheet_values: SheetValues, po_id: int, is_ats: bool, po_name: str,
  sc_token: str, company_id: int,
) -> None:
  if is_ats:
    new_sku_data = create_skus_ats(worksheet_values=worksheet_values, po_id=po_id)
  else:
    new_sku_data = await create_or_find_skus_non_ats(worksheet_values=worksheet_values, po_id=po_id)
   
  # If no new skus were found (should only apply for non-ats POs)
  if new_sku_data is None:
    # Post updated worksheet rows to worksheet
    await post_to_worksheet(
      is_ats=is_ats, spreadsheet_id=worksheet_values.spreadsheet_id,
      row_dicts=worksheet_values.row_dicts,
    )
    return
  
  # Prepare new sku data for upload to Lightspeed
  ls_import_data = prepare_skus_for_lightspeed(new_sku_data=new_sku_data)

  # Upload products to lightspeed
  ls_results = await upload_products_to_ls(po_id=po_id, products=ls_import_data, po_name=po_name)

  # Create dict of skus to lightspeed system ids
  sku_to_ls_system_id: Dict[str, str] = {}
  for result in ls_results:
    sku_to_ls_system_id[result.sku] = result.system_id

  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Uploading products to SellerCloud.", type="log"),
  )

  sc_import_data = prepare_skus_for_sellercloud(
    worksheet_values=worksheet_values,
    ls_import_data=ls_import_data,
    sku_to_ls_system_id=sku_to_ls_system_id,
    is_ats=is_ats,
  )

  sc_job_id = await sc_create_skus(token=sc_token, company_id=company_id, products=sc_import_data)
  
  try:
    await set_job_priority_to_critical(token=sc_token, job_id=sc_job_id)
  except Exception as e:
    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal", message=f"Could not set priority to critical. {str(e)}", type="error",
      )
    )

  add_log_to_purchase_order(
    id=po_id, log=Log(user="Internal", message="Products uploaded to SellerCloud.", type="log"),
  )

  await post_to_worksheet(
    is_ats=is_ats, spreadsheet_id=worksheet_values.spreadsheet_id,
    row_dicts=worksheet_values.row_dicts,
  )

  # Post new products to Aliases/Created SKUs sheet

  is_job_completed = await wait_for_job_to_finish(po_id=po_id, job_id=sc_job_id, token=sc_token)

  if not is_job_completed:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Timed out while waiting for SKU creation job to finish.",
    )

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

def prepare_skus_for_lightspeed(new_sku_data: List[Dict[str, Any]]) -> List[ImportProduct]:
  ls_upload: List[ImportProduct] = []

  for row in new_sku_data:
    sku = str(row["ProductID"])
    mpn = format_mpn(str(row["MPN"]))
    color = str(row["Color"])
    brand = str(row["Brand"])
    description = str(row["Description"])
    size = str(row["Size"])
    msrp = str(row["Retail"])
    item_type = str(row["Item Type"])

    description = " ".join([sku, mpn, color, brand, description, "Size", size])

    ls_data = {
      "Description": description,
      "Custom SKU": sku,
      "Manufacturer SKU": mpn,
      "Brand": brand,
      "Default Cost": '',
      "Default - Price": msrp,
      "MSRP - Price": msrp,
      "Category": item_type,
    }

    ls_upload.append(ImportProduct(**ls_data))

  return ls_upload

async def post_to_worksheet(is_ats: bool, spreadsheet_id: str, row_dicts: List[Dict[str, Any]]):
  ss_properties = WorksheetPropertiesAts(id=spreadsheet_id) if is_ats else WorksheetPropertiesNonAts(id=spreadsheet_id)
  await post_row_dicts_to_spreadsheet(
    ss_properties=ss_properties, row_dicts=row_dicts,
  )

def get_lightspeed_url(system_id: str) -> str:
  return f"https://us.merchantos.com/?name=item.listings.items&form_name=listing&description={system_id}"

def prepare_skus_for_sellercloud(
  worksheet_values: SheetValues,
  ls_import_data: List[ImportProduct],
  sku_to_ls_system_id: Dict[str, str],
  is_ats: bool,
) -> List[CreateProduct]:
  ls_sku_data = {data.custom_sku: data for data in ls_import_data}

  ebay_settings = get_ebay_discount_settings()
  ebay_discount = ebay_settings.discount

  skus_for_import: List[CreateProduct] = []

  for row in worksheet_values.row_dicts:
    sku = str(row["ProductID"])
    ls_data = ls_sku_data[sku]
    product_import = CreateProduct(
      ProductID=sku,
      ProductName=ls_data.Description,
      ManufacturerSKU=ls_data.manufacturer_sku,
      BrandName=ls_data.Brand,
      ListPrice=ls_data.default_price,
      WebsitePrice=ls_data.default_price if is_ats else str(row["SitePrice"]),
      SitePrice=ls_data.default_price if is_ats else str(row["SitePrice"]),
      BuyItNowPrice=str(round(float(ls_data.default_price if is_ats else row["SitePrice"]) * (1 - ebay_discount), 2)),
      ProductTypeName=ls_data.Category,
      LIGHTSPEED_SYSTEM_ID=sku_to_ls_system_id[sku],
      UPC=add_check_digit_for_upc(upc=sku_to_ls_system_id[sku]),
      ASSIGN_TO_ATS=is_ats,
    )

    skus_for_import.append(product_import)

    row["MPN"] = ls_data.manufacturer_sku

  return skus_for_import

def add_check_digit_for_upc(upc:str) -> str:
  char_list = list(upc)[::-1]
  total: int = 0

  i = 1

  for v in char_list:
    number = int(v)
    if i % 2 == 0:
      total += number
    else:
      total += number * 3
    i += 1

  check_digit = (int((total + 9) / 10) * 10) - total

  return upc + str(check_digit)

async def wait_for_job_to_finish(
  po_id: int, job_id: int, token: str, attempts: int = 10,
) -> bool:
  attempt: int = 1

  while attempt <= attempts:
    add_log_to_purchase_order(
      id=po_id, log=Log(
        user="Internal", message=f"Checking if job #{job_id} was completed.", type="log",
      ),
    )

    job_info = await get_job_information(token=token, job_id=job_id)
    status_code = int(job_info["Basic"]["Status"]) # type: ignore
    is_completed = status_code == 3

    if is_completed:
      add_log_to_purchase_order(
        id=po_id, log=Log(
          user="Internal", message="SC Job was completed successfully.", type="log",
        )
      )

      return True
    else:
      wait_time: int = 2 ** attempt
      await asyncio.sleep(wait_time)
      attempt += 1

  add_log_to_purchase_order(
    id=po_id, log=Log(
      user="Internal", message="Max attempts reached and SC job was not completed.", type="error",
    )
  )

  update_purchase_order(id=po_id, updates=UpdatePurchaseOrder(status="Internal Error"))

  return False