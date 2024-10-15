from fastapi import HTTPException, status
from typing import Dict, List
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import UpdateStatus
from api.models.sheets import MarketplaceProperties

marketplaces_to_groups: Dict[str, Dict[str, str]] = {"marketplaces": {}}

marketplaces_update_status = UpdateStatus(
  update_time=datetime(year=1899, month=1, day=1),
  status="Pending Initial Update",
)

def get_updated_marketplaces_to_groups() -> Dict[str, str]:
  """
  This function retrieves the global marketplaces variable and validates its data
  """
  # Check how long it has been since the last marketplace update
  current_time = datetime.now()
  time_since_update = current_time - marketplaces_update_status.update_time

  # Raise error if sales reports list is empty
  if not marketplaces_to_groups["marketplaces"]:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find marketplaces.",
    )
  
  # Raise error if sales reports are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Marketplaces are not up-to-date",
    )
  
  return marketplaces_to_groups["marketplaces"]

def get_marketplaces_update_status() -> UpdateStatus:
  return marketplaces_update_status

async def update_marketplaces(repeat: bool, retries: int = 5):
  """
  This function will be called on application startup to update the marketplaces
  once a day. (Can be called manually as well)
  """
  valid_marketplace_groups: List[str] = ["Ecom", "Retail", "Wholesale", "Scarce"]
  marketplaces_update_status.status = "Updating..."

  while True:
    attempt: int = 0

    while attempt < retries:
      try:
        print("Updating marketplaces...")

        # Retrieve the marketplace data from the marketplace xlsx file
        marketplace_sheet_values = await sheets_utils.get_row_dicts_from_excel_sheet(
          file_properties=MarketplaceProperties()
        )

        marketplace_row_dicts = marketplace_sheet_values.row_dicts

        # Compile marketplace sheet values into marketplace-to-group dict with customizations
        new_marketplace_to_groups: Dict[str, str] = {}
        invalid_marketplace_groups: List[str] = []

        for marketplace_row in marketplace_row_dicts:
          marketplace = marketplace_row["Marketplace"]
          group = marketplace_row["Group"]

          if marketplace == "Misc":
            group = "Wholesale"
          elif marketplace == "Scarce Website":
            group = "Scarce"

          if group in valid_marketplace_groups:
            new_marketplace_to_groups[marketplace] = group
          else:
            invalid_marketplace_groups.append(group)

        if invalid_marketplace_groups:
          print("There are invalid groups in marketplace sheet. Sending error email.")
          await send_error_email(
            subject="PO Tool Invalid Marketplace Groups",
            error_message="The following invalid groups were found in the marketplaces" +
            f" sheet: {', '.join(invalid_marketplace_groups)}",
          )

        # Update the sales reports global variables
        marketplaces_to_groups["marketplaces"] = new_marketplace_to_groups
        marketplaces_update_status.update_time = datetime.now()
        marketplaces_update_status.status = "Updated"
        print("Marketplaces finished updating.")

        break

      except Exception as e:
        attempt += 1
        if attempt == retries:
          print(f"Could not update marketplaces. Error: {str(e)}. Will send error email.")
          marketplaces_update_status.status = "Error while updating"
          # Send an error email if sales report did not update
          await send_error_email(
            subject="PO Tool Marketplaces Update Error",
            error_message=str(e),
          )
        else:
          print(f"There was an error while updating (attempt: {attempt}). Retrying in 5 seconds...")
          await asyncio.sleep(5)
          continue

    if repeat:
      # Repeat once a day
      print("Marketplaces update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      break