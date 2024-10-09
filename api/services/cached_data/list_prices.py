from fastapi import HTTPException, status
from typing import Dict, Any
from datetime import datetime
import asyncio

from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.cache import UpdateStatus
from api.models.sheets import ListPricesProperties

skus_to_list_prices: Dict[str, Dict[str, Any]] = {"skus": {}}

list_price_update_status = UpdateStatus(
  update_time=datetime.now(),
  status="Pending Initial Update",
)

def get_updated_skus_to_list_prices() -> Dict[str, str]:
  """
  This function retrieves the global marketplaces variable and validates its data
  """
  # Check how long it has been since the last marketplace update
  current_time = datetime.now()
  time_since_update = current_time - list_price_update_status.update_time

  # Raise error if sales reports list is empty
  if not skus_to_list_prices["skus"]:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find list prices.",
    )
  
  # Raise error if sales reports are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="List Prices are not up-to-date",
    )
  
  return skus_to_list_prices["skus"]

def get_list_price_update_status() -> UpdateStatus:
  return list_price_update_status

async def update_list_prices(repeat: bool, retries: int = 3):
  """
  This function will be called on application startup to update the List Prices
  once a day. (Can be called manually as well)
  """
  while True:
    attempt: int = 0

    while attempt <= retries:
      try:
        print("Updating List Prices...")

        # Retrieve the List Price data from the List Prices spreadsheet
        list_price_sheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
          ss_properties=ListPricesProperties()
        )

        list_price_row_dicts = list_price_sheet_values.row_dicts

        # Compile list price sheet values into sku-to-list-price dict
        new_sku_to_list_price: Dict[str, str] = {}

        for list_price_row in list_price_row_dicts:
          sku: str = list_price_row["ProductID"]
          list_price: Any = list_price_row["ListPrice"]
          new_sku_to_list_price[sku] = list_price

        # Update the list price global variables
        skus_to_list_prices["skus"] = new_sku_to_list_price
        list_price_update_status.update_time = datetime.now()
        list_price_update_status.status = "Updated"
        print("List Prices finished updating.")

        break

      except Exception as e:
        attempt += 1
        if attempt == retries:
          print(f"Could not update List Prices. Error: {str(e)}. Will send error email.")
          list_price_update_status.status = "Error while updating"
          # Send an error email if sales report did not update
          await send_error_email(
            subject="PO Tool List Prices Update Error",
            error_message=str(e),
          )
        else:
          print(f"There was an error while updating (attempt: {attempt}). Retrying in 5 seconds...")
          await asyncio.sleep(5)
          continue

    if repeat:
      # Repeat once a day
      print("List Prices update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      break