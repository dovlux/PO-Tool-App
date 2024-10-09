from typing import List, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio

from api.services.google_api import drive as drive_services
from api.services.google_api import sheets_utils
from api.services.utils.send_emails import send_error_email
from api.models.spreadsheets import SheetProperties, RowDicts
from api.models.cache import SalesReportsUpdateStatus

# Global variables for sales reports
sales_reports_rows: Dict[str, RowDicts] = { "row_dicts": RowDicts(row_dicts=[]) }

sales_reports_update_status = SalesReportsUpdateStatus(
  update_time=datetime.now(),
  status="Pending Initial Update",
)

def get_updated_sales_reports_rows() -> RowDicts:
  """
  This function retrieves the global sales reports variable and validates its data
  """
  # Check how long it has been since the last sales reports update
  current_time = datetime.now()
  time_since_update = current_time - sales_reports_update_status.update_time

  # Raise error if sales reports list is empty
  if not sales_reports_rows["row_dicts"].row_dicts:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not find sales reports",
    )
  
  # Raise error if sales reports are not up-to-date
  if time_since_update.total_seconds() / 86400 > 1.05:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Sales reports are not up-to-date",
    )
  
  return sales_reports_rows["row_dicts"]

def get_sales_reports_update_status() -> SalesReportsUpdateStatus:
  return sales_reports_update_status

async def update_sales_reports(repeat: bool):
  """
  This function will be called on application startup to update the sales reports
  once a day. (Can be called manually as well)
  """
  months_span: int = 6
  run_update: bool = True

  while run_update:
    try:
      print("Updating the sales reports...")

      # Retrieve the latest file ids based on months_span
      file_ids = await get_sales_report_file_ids(
        root_folder_id="1YVeKul5kUUb4hr-bI8M20h2D94JM2W5w",
        months_span=months_span,
      )

      # Retrieve the relevant sales rows from the file ids
      sales_rows = await get_sales_reports_rows(
        file_ids=file_ids, months_span=months_span
      )

      # Update the sales reports global variables
      sales_reports_rows["row_dicts"] = sales_rows
      sales_reports_update_status.update_time = datetime.now()
      sales_reports_update_status.status = "Updated"
      print("Sales reports finished updating.")

    except Exception as e:
      print(f"Could not update sales reports. Error: {str(e)}. Will send error email.")
      sales_reports_update_status.status = "Error while updating"
      # Send an error email if sales report did not update
      await send_error_email(
        subject="PO Tool Sales Report Update Error",
        error_message=str(e),
      )

    if repeat:
      # Repeat once a day
      print("Sales Reports update will run again in one day.")
      await asyncio.sleep(86400)
    else:
      run_update = False

async def get_sales_reports_rows(file_ids: List[str], months_span: int) -> RowDicts:
  """
  This function retrieves all sales reports rows from the given file ids and filters out
  the latest rows that are included in the months_span
  """
  all_sales_rows: List[Dict[str, Any]] = []

  for file_id in file_ids:
    # Retrieve sheet and sales row values for current sheet
    sheet_values = await sheets_utils.get_row_dicts_from_spreadsheet(
      ss_properties=SheetProperties(
        id=file_id,
        sheet_name="Sheet1",
        required_headers=[
          "Transaction Date", "Trans Type", "Order #", "Order Date", "Ship Date",
          "Marketplace", "Channel Order #", "SKU", "Qty", "Tax", "Discount", "Grand Total",
          "Accrual Refund", "Payments", "Refunds", "Adjustments",
          "Grand Total + Adjustmensts - Tax + Accrual Refunds", "Items Cost", "Shipping Cost",
          "Commission", "Profit", "Brand", "ProductName", "ProductTypeName", "Type", "Gender",
          "Age Since Received", "Vendor", "Sales Rep"
        ],
      )
    )
    sales_rows = sheet_values.row_dicts

    # Add sales row data to all_sales_rows
    all_sales_rows.extend(sales_rows)
  
  # Find start date of timespan
  base_date = datetime(1899, 12, 30).date()
  order_dates = [
    base_date + timedelta(days=sales_row["Order Date"])
    for sales_row in all_sales_rows
    if sales_row["Order Date"]
  ]
  latest_date = max(order_dates)
  start_date = latest_date - relativedelta(months=months_span)

  # Filter out irrelevant sales rows
  relevant_sales_rows = [
    sales_row for sales_row in all_sales_rows
    if sales_row["Order Date"]
    and (base_date + timedelta(days=sales_row["Order Date"]) >= start_date)
    and sales_row["Marketplace"]
  ]

  print("Retrieved all relevant sales rows from files.")
  return RowDicts(row_dicts=relevant_sales_rows)

async def get_sales_report_file_ids(root_folder_id: str, months_span: int) -> List[str]:
  """
  This function finds the IDs of the latest sales report spreadsheets based on the months span.
  """
  latest_months_file_data: List[Dict[str, str]] = []

  # Get contents of the root sales reports folder
  print("Getting contents of Sales Reports root folder...")
  root_sales_folder_contents = await drive_services.get_folder_contents(
    folder_id=root_folder_id,
  )

  # Get folder information of the latest two years
  print("Finding year folders of the latest two years...")
  latest_years_data = get_latest_folders(folder_contents=root_sales_folder_contents)

  # Get month spreadsheet contents from the latest year folder
  print("Getting month files from the latest year...")
  latest_year_folder_contents = await drive_services.get_folder_contents(
    folder_id=latest_years_data["latest_year"]["id"],
  )
  latest_year_month_files = latest_year_folder_contents["spreadsheets"]

  # Add the ids of the latest months sales reports to results (based on months_span)
  print(f"Getting spreadsheet IDs of the latest {months_span + 1} sales reports...")
  if len(latest_year_month_files) >= months_span + 1:
    # If latest year has enough months for the required months_span

    # Get the end and start month number starting from the latest month number
    end_month_number = max([int(month_file["name"][:2]) for month_file in latest_year_month_files])
    start_month_number = end_month_number - months_span
    
    # Add the latest month spreadsheet ids to results
    latest_months_file_data = [
      month_file for month_file in latest_year_month_files
      if int(month_file["name"][:2]) >= start_month_number
    ]
  else:
    # If latest year does not contain enough month files

    # Add all month ids from the latest year to results
    latest_months_file_data = [month_file for month_file in latest_year_month_files]

    # Get month spreadsheet contents from the previous year folder
    print("Getting month files from the previous year...")
    previous_year_folder_contents = await drive_services.get_folder_contents(
      folder_id=latest_years_data["previous_year"]["id"],
    )
    previous_year_month_files = previous_year_folder_contents["spreadsheets"]

    # Get the end and start month number starting from the latest month number (for previous year)
    end_month_number = max([int(month_file["name"][:2]) for month_file in previous_year_month_files])
    start_month_number = end_month_number - (months_span - len(latest_months_file_data))

    # Add the previous year month spreadsheet ids to results (if included in months_span)
    latest_months_file_data += [
      month_file for month_file in previous_year_month_files
      if int(month_file["name"][:2]) >= start_month_number
    ]

  print(f"Retrieved latest month files: {' '.join(month['name'] for month in latest_months_file_data)}")
  return [month_file["id"] for month_file in latest_months_file_data]

def get_latest_folders(
  folder_contents: Dict[str, List[Dict[str, str]]]
) -> Dict[str, Dict[str, str]]:
  """
  Finds the latest folder date by their name, and returns the folder information.

  Args:
    folder_contents (dict[str, list[dict[str, str]]]): The contents of the folder from which to
        get the latest folder.

  Returns:
    Dict[str, Dict[str, str]]: The info of the latest year and previous year folder.
  """
  folders = folder_contents["folders"]

  latest_year = None
  previous_year = None
  latest_year_folder = {"name": "", "id": ""}
  previous_year_folder = {"name": "", "id": ""}

  for folder in folders:
    folder_year = int(folder["name"])
    if latest_year is None or folder_year > latest_year:
      previous_year = latest_year
      previous_year_folder = latest_year_folder
      latest_year = folder_year
      latest_year_folder = folder
    elif previous_year is None or folder_year > previous_year:
      previous_year = folder_year
      previous_year_folder = folder

  return {"latest_year": latest_year_folder, "previous_year": previous_year_folder}