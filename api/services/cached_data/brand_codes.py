from fastapi import HTTPException, status
from typing import Dict
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import UpdateStatus
from api.models.sheets import BrandCodesProperties

brand_codes: Dict[str, Dict[str, str]] = {"brand_codes": {}}

brand_codes_update_status = UpdateStatus(
  update_time=datetime(year=1899, month=1, day=1),
  status="Pending Initial Update",
)

def get_updated_brand_codes() -> Dict[str, str]:
  """
  This function retrieves the global brand_codes variable and validates its data
  """
  # Check how long it has been since the last marketplace update
  current_time = datetime.now()
  time_since_update = current_time - brand_codes_update_status.update_time

  # Raise error if brand codes dict is empty
  if not brand_codes["brand_codes"]:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find Brand Codes.",
    )
  
  # Raise error if brand codes are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Brand Codes are not up-to-date",
    )
  
  return brand_codes["brand_codes"]

def get_brand_codes_update_status() -> UpdateStatus:
  return brand_codes_update_status

async def update_brand_codes(repeat: bool, retries: int = 5):
  """
  This function will be called on application startup to update the Brand Codes
  once a day. (Can be called manually as well)
  """
  brand_codes_update_status.status = "Updating..."
  
  while True:
    attempt: int = 0

    while attempt < retries:
      try:
        print("Updating Brand Codes...")

        # Retrieve the Brand Codes rows from the SKU/PO Tool  spreadsheet
        brand_codes_sheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
          ss_properties=BrandCodesProperties()
        )

        brand_codes_dict: Dict[str, str] = {}

        for row in brand_codes_sheet_values.row_dicts:
          brand_codes_dict[row["Brand"]] = row["Brand Code"]

        # Update the Item Types global variables
        brand_codes["brand_codes"] = brand_codes_dict
        brand_codes_update_status.update_time = datetime.now()
        brand_codes_update_status.status = "Updated"
        print("Brand Codes finished updating.")

        break

      except Exception as e:
        attempt += 1
        if attempt == retries:
          print(f"Could not update Brand Codes. Error: {str(e)}. Will send error email.")
          brand_codes_update_status.status = "Error while updating"
          # Send an error email if Brand Codes did not update
          await send_error_email(
            subject="PO Tool Brand Codes Update Error",
            error_message=str(e),
          )
        else:
          print(f"There was an error while updating Brand Codes (attempt: {attempt}). Retrying in 5 seconds...")
          await asyncio.sleep(5)
          continue

    if repeat:
      # Repeat once a day
      print("Brand Codes update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      break