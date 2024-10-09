from fastapi import HTTPException, status
from typing import Dict, List
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import CachedDataUpdateStatus
from api.models.spreadsheets import MarketplaceProperties

marketplaces_to_groups: Dict[str, Dict[str, str]] = {"marketplaces": {}}

marketplaces_update_status = CachedDataUpdateStatus(
  update_time=datetime.now(),
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

def get_marketplaces_update_status() -> CachedDataUpdateStatus:
  return marketplaces_update_status

async def update_marketplaces(repeat: bool):
  """
  This function will be called on application startup to update the marketplaces
  once a day. (Can be called manually as well)
  """
  run_update: bool = True
  valid_marketplace_groups: List[str] = ["Ecom", "Retail", "Wholesale", "Scarce"]

  while run_update:
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

        if group not in valid_marketplace_groups:
          invalid_marketplace_groups.append(group)

      # Update the sales reports global variables
      marketplaces_to_groups["marketplaces"] = new_marketplace_to_groups
      marketplaces_update_status.update_time = datetime.now()
      marketplaces_update_status.status = "Updated"
      print("Marketplaces finished updating.")

    except Exception as e:
      print(f"Could not update marketplaces. Error: {str(e)}. Will send error email.")
      marketplaces_update_status.status = "Error while updating"
      # Send an error email if sales report did not update
      await send_error_email(
        subject="PO Tool Marketplaces Update Error",
        error_message=str(e),
      )

    if repeat:
      # Repeat once a day
      print("Marketplaces update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      run_update = False