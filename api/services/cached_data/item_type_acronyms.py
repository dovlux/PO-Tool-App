from fastapi import HTTPException, status
from typing import Dict
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import UpdateStatus
from api.models.sheets import ItemTypeAcronymsProperties

item_type_acronyms: Dict[str, Dict[str, str]] = {"item_type_acronyms": {}}

item_type_acronyms_update_status = UpdateStatus(
  update_time=datetime(year=1899, month=1, day=1),
  status="Pending Initial Update",
)

def get_updated_item_type_acronyms() -> Dict[str, str]:
  """
  This function retrieves the global item_type_acronyms variable and validates its data
  """
  # Check how long it has been since the last Item Type Acronyms update
  current_time = datetime.now()
  time_since_update = current_time - item_type_acronyms_update_status.update_time

  # Raise error if item type acronyms dict is empty
  if not item_type_acronyms["item_type_acronyms"]:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find Item Type Acronyms.",
    )
  
  # Raise error if item type acronyms are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Item Type Acronyms are not up-to-date",
    )
  
  return item_type_acronyms["item_type_acronyms"]

def get_item_type_acronyms_update_status() -> UpdateStatus:
  return item_type_acronyms_update_status

async def update_item_type_acronyms(repeat: bool, retries: int = 5):
  """
  This function will be called on application startup to update the Item Type Acronyms
  once a day. (Can be called manually as well)
  """
  item_type_acronyms_update_status.status = "Updating..."
  
  while True:
    attempt: int = 0

    while attempt < retries:
      try:
        print("Updating Item Type Acronyms...")

        # Retrieve the Item Type Acronyms rows from the SKU/PO Tool  spreadsheet
        item_type_acronyms_sheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
          ss_properties=ItemTypeAcronymsProperties()
        )

        item_type_acronyms_dict: Dict[str, str] = {}

        for row in item_type_acronyms_sheet_values.row_dicts:
          item_type_acronyms_dict[row["ProductTypeName"]] = row["SKU Acronym"]

        # Update the Item Type Acronyms global variables
        item_type_acronyms["item_type_acronyms"] = item_type_acronyms_dict
        item_type_acronyms_update_status.update_time = datetime.now()
        item_type_acronyms_update_status.status = "Updated"
        print("Item Type Acronyms finished updating.")

        break

      except Exception as e:
        attempt += 1
        if attempt == retries:
          print(f"Could not update Item Type Acronyms. Error: {str(e)}. Will send error email.")
          item_type_acronyms_update_status.status = "Error while updating"
          # Send an error email if Item Type Acronyms did not update
          await send_error_email(
            subject="PO Tool Item Type Acronyms Update Error",
            error_message=str(e),
          )
        else:
          print(f"There was an error while updating Item Type Acronyms (attempt: {attempt}). Retrying in 5 seconds...")
          await asyncio.sleep(5)
          continue

    if repeat:
      # Repeat once a day
      print("Item Type Acronyms update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      break