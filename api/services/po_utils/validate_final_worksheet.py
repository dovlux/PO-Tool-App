from typing import List

from api.services.google_api.sheets_utils import get_row_dicts_from_spreadsheet, post_row_dicts_to_spreadsheet
from api.models.sheets import SheetValues, WorksheetProperties

async def validate_worksheet_for_po(
  spreadsheet_id: str, is_ats: bool,
) -> SheetValues | None:
  worksheet_values = await get_row_dicts_from_spreadsheet(
    ss_properties=WorksheetProperties(id=spreadsheet_id),
  )

  has_errors = False

  for row in worksheet_values.row_dicts:
    error_msgs: List[str] = []

    if not row["ProductID"]:
      if (is_ats and not row["Sizes"]) or (not is_ats and not row["Size"]):
        error_msgs.append("Missing Size")
      if not row["Brand"]:
        error_msgs.append("Missing Brand")
      if not row["Description"]:
        error_msgs.append("Missing Description")
      if not row["Color"]:
        error_msgs.append("Missing Color")
      if not row["Item Type"]:
        error_msgs.append("Missing Item Type")
      if not row["Retail"]:
        error_msgs.append("Missing ")