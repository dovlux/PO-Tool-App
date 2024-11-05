from fastapi import HTTPException, status
from typing import Dict, List
import asyncio

from api.services.google_api.sheets_utils import get_row_dicts_from_spreadsheet
from api.services.utils.mpn_formatter import remove_special_chars
from api.models.sheets import AliasesCreatedSkusProperties, SheetValues

async def get_aliases_dicts() -> Dict[str, Dict[str, List[str]]]:
  aliases_sheet_values = await get_aliases_values()
  brand_mpn_dict: Dict[str, List[str]] = {}
  brand_type_dict: Dict[str, List[str]] = {}

  for row in aliases_sheet_values.row_dicts:
    old_sku = str(row["Old Custom SKU"])
    mpn = str(row["MPN"])

    brand_code = get_brand_code(sku=old_sku)
    formatted_mpn = remove_special_chars(mpn=mpn)
    brand_type = get_brand_type_code(sku=old_sku)
    brand_mpn = brand_code + formatted_mpn

    if brand_mpn not in brand_mpn_dict:
      brand_mpn_dict[brand_mpn] = []
    brand_mpn_dict[brand_mpn].append(old_sku)

    if brand_type not in brand_type_dict:
      brand_type_dict[brand_type] = []
    brand_type_dict[brand_type].append(old_sku)

  return {
    "brand_mpn_dict": brand_mpn_dict,
    "brand_type_dict": brand_type_dict,
  }


async def get_aliases_values(retries: int = 5) -> SheetValues:
  attempt: int = 0
  aliases_values = SheetValues(headers=[], row_dicts=[], spreadsheet_id="")

  while attempt < retries:
    try:
      attempt += 1

      aliases_values = await get_row_dicts_from_spreadsheet(
        ss_properties=AliasesCreatedSkusProperties(),
      )

    except Exception as e:
      if attempt == retries:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Could not retrieve Aliases/Created SKUs values. {str(e)}",
        )
      else:
        wait_time: int = 2 ** attempt
        await asyncio.sleep(wait_time)

  return aliases_values

def get_brand_code(sku: str) -> str:
  return sku[:3]

def get_brand_type_code(sku: str) -> str:
  return sku[:8]