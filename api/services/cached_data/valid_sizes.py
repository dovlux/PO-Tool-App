from fastapi import HTTPException, status
from typing import Dict, Set
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import UpdateStatus
from api.models.sheets import ValidSizesProperties

valid_sizes: Dict[str, Set[str]] = {"valid_sizes": set()}

valid_sizes_update_status = UpdateStatus(
  update_time=datetime(year=1899, month=1, day=1),
  status="Pending Initial Update",
)

def get_updated_valid_sizes() -> Set[str]:
  """
  This function retrieves the global valid_sizes variable and validates its data
  """
  # Check how long it has been since the last valid_sizes update
  current_time = datetime.now()
  time_since_update = current_time - valid_sizes_update_status.update_time

  # Raise error if valid sizes set is empty
  if not valid_sizes["valid_sizes"]:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find Valid Sizes.",
    )
  
  # Raise error if brand codes are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Valid Sizes are not up-to-date",
    )
  
  return valid_sizes["valid_sizes"]

def get_valid_sizes_update_status() -> UpdateStatus:
  return valid_sizes_update_status

async def update_valid_sizes(repeat: bool, retries: int = 5):
  """
  This function will be called on application startup to update the Valid Sizes
  once a day. (Can be called manually as well)
  """
  valid_sizes_update_status.status = "Updating..."
  
  while True:
    attempt: int = 0

    while attempt < retries:
      try:
        print("Updating Valid Sizes...")

        # Retrieve the Valid Sizes rows from the SKU/PO Tool  spreadsheet
        valid_sizes_sheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
          ss_properties=ValidSizesProperties()
        )

        valid_sizes_set: Set[str] = set()

        for row in valid_sizes_sheet_values.row_dicts:
          valid_sizes_set.add(row["Size"])

        # Update the Valid Sizes global variables
        valid_sizes["valid_sizes"] = valid_sizes_set
        valid_sizes_update_status.update_time = datetime.now()
        valid_sizes_update_status.status = "Updated"
        print("Valid Sizes finished updating.")

        break

      except Exception as e:
        attempt += 1
        if attempt == retries:
          print(f"Could not update Valid Sizes. Error: {str(e)}. Will send error email.")
          valid_sizes_update_status.status = "Error while updating"
          # Send an error email if Valid Sizes did not update
          await send_error_email(
            subject="PO Tool Valid Sizes Update Error",
            error_message=str(e),
          )
        else:
          print(f"There was an error while updating Valid Sizes (attempt: {attempt}). Retrying in 5 seconds...")
          await asyncio.sleep(5)
          continue

    if repeat:
      # Repeat once a day
      print("Valid Sizes update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      break