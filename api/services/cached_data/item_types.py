from fastapi import HTTPException, status
from typing import Dict
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import UpdateStatus
from api.models.sheets import ItemTypesProperties, RowDicts

item_types_rows: Dict[str, RowDicts] = {"item_types": RowDicts(row_dicts=[])}

item_types_update_status = UpdateStatus(
  update_time=datetime(year=1899, month=1, day=1),
  status="Pending Initial Update",
)

def get_updated_item_types_rows() -> RowDicts:
  """
  This function retrieves the global Item Types variable and validates its data
  """
  # Check how long it has been since the last marketplace update
  current_time = datetime.now()
  time_since_update = current_time - item_types_update_status.update_time

  # Raise error if item types list is empty
  if not item_types_rows["item_types"].row_dicts:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find Item Types.",
    )
  
  # Raise error if sales reports are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Item Types are not up-to-date",
    )
  
  return item_types_rows["item_types"]

def get_item_types_update_status() -> UpdateStatus:
  return item_types_update_status

async def update_item_types(repeat: bool, retries: int = 5):
  """
  This function will be called on application startup to update the Item Types
  once a day. (Can be called manually as well)
  """
  item_types_update_status.status = "Updating..."
  
  while True:
    attempt: int = 0

    while attempt < retries:
      try:
        print("Updating Item Types...")

        # Retrieve the Item Types rows from the Item Types spreadsheet
        item_types_sheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
          ss_properties=ItemTypesProperties()
        )

        item_types_row_dicts = item_types_sheet_values

        # Update the Item Types global variables
        item_types_rows["item_types"] = item_types_row_dicts
        item_types_update_status.update_time = datetime.now()
        item_types_update_status.status = "Updated"
        print("Item Types finished updating.")

        break

      except Exception as e:
        attempt += 1
        if attempt == retries:
          print(f"Could not update Item Types. Error: {str(e)}. Will send error email.")
          item_types_update_status.status = "Error while updating"
          # Send an error email if Item Types did not update
          await send_error_email(
            subject="PO Tool Item Types Update Error",
            error_message=str(e),
          )
        else:
          print(f"There was an error while updating Item Types (attempt: {attempt}). Retrying in 5 seconds...")
          await asyncio.sleep(5)
          continue

    if repeat:
      # Repeat once a day
      print("Item Types update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      break