from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
import pandas as pd
from pandas import DataFrame
from io import BytesIO
from typing import Any, List, Dict

from api.services.google_api import sheets as sheets_services
from api.services.google_api import drive as drive_services
from api.models.sheets import SheetValues, SheetProperties

async def get_row_dicts_from_spreadsheet(ss_properties: SheetProperties) -> SheetValues:
  """
  Retrieve rows from a Google Sheets spreadsheet and convert them into a List of dictionaries.

  This function fetches all rows from a specified sheet within a Google Sheets spreadsheet, 
  validates that the required headers are present, and then maps each row's data to 
  dictionaries where the keys are the `required_headers`. If the sheet contains fewer 
  than two rows (no data), an exception is raised.

  Args:
    spreadsheet_id (str): The ID of the spreadsheet.
    sheet_name (str): The name of the sheet within the spreadsheet.
    required_headers (List[str]): A List of headers that must exist in the sheet, used as 
                                keys in the returned row dictionaries.

  Returns:
    Dict[str, List[Dict[str, str]] | List[str]: A dictionary with the headers from the sheet ("headers")
                                              and a List of dictionaries where each dictionary represents 
                                              a row of data, with keys from `required_headers` ("row_dicts").

  Raises:
    HTTPException: If the sheet has fewer than two rows (no data) or if the required headers 
              are not found in the actual headers.

  Example:
    >>> sheet_properties = get_row_dicts_from_spreadsheet(
          spreadsheet_id="spreadsheet_id",
          sheet_name="Sheet1",
          required_headers=["Name", "Age"]
        )
    >>> print(sheet_properties)
    {
      'headers': ['Name', 'Age'],
      'row_dicts': [{'Name': 'Alice', 'Age': '30'}, {'Name': 'Bob', 'Age': '25'}]
    }
  """
  spreadsheet_id = ss_properties.id
  sheet_name = ss_properties.sheet_name
  required_headers = ss_properties.required_headers
    
  # Get a List of all row data from spreadsheet (including headers) using get_values()
  all_row_values: List[List[Any]] = await sheets_services.get_values(
    spreadsheet_id=spreadsheet_id,
    sheet_name=sheet_name,
  )

  # Validate sheet contains at least two rows
  if len(all_row_values) < 2:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Sheet has no cell values in non-header rows.",
    )

  # Validate header row contains all required values
  validate_required_headers_(
    actual_headers=all_row_values[0],
    required_headers=required_headers,
    sheet_name=sheet_name,
  )

  # Create dicts for each row with headers from required_headers as the keys
  row_dicts: List[Dict[str, Any]] = create_row_dicts(
    required_headers=required_headers,
    actual_headers=all_row_values[0],
    rows=all_row_values[1:],
  )

  # Return actual header row and row dicts
  print("Validated and Converted all non-header rows into dicts.")
  return SheetValues(headers=all_row_values[0], row_dicts=row_dicts)

async def get_row_dicts_from_excel_sheet(file_properties: SheetProperties) -> SheetValues:
  """
  Retrieve rows from an Excel sheet in Google Drive and convert them into a List of dictionaries.

  This function fetches all rows from a specified Excel sheet within Google Drive, 
  validates that the required headers are present, and then maps each row's data to 
  dictionaries where the keys are the `required_headers`.

  Args:
    file_id (str): The ID of the Excel file.
    sheet_name (str): The name of the sheet within the spreadsheet.
    required_headers (List[str]): A List of headers that must exist in the sheet, used as 
                                keys in the returned row dictionaries.

  Returns:
    Dict[str, List[Dict[str, str]] | List[str]: A dictionary with the headers from the sheet ("headers")
                                              and a List of dictionaries where each dictionary represents 
                                              a row of data, with keys from `required_headers` ("row_dicts").
  """
  file_id = file_properties.id
  sheet_name = file_properties.sheet_name
  required_headers = file_properties.required_headers
  
  # Download excel file from Google Drive
  excel_file: BytesIO = await drive_services.download_xlsx_file(file_id=file_id)

  # Get DataFrame of file using pandas
  df: DataFrame = await run_in_threadpool(
    pd.read_excel, excel_file, sheet_name=sheet_name, header=0, # type: ignore
  )

  # Get List of row values from DataFrame
  row_values: List[List[str]] = df.values.tolist() # type: ignore
  # Get List of header names from DataFrame  
  actual_headers: List[str] = df.columns.tolist()

  # Validate header row contains all required values
  validate_required_headers_(
    actual_headers=actual_headers,
    required_headers=required_headers,
    sheet_name=sheet_name,
  )

  # Create dicts for each row with headers from required_headers as the keys
  row_dicts: List[Dict[str, str]] = create_row_dicts(
    required_headers=required_headers,
    actual_headers=actual_headers,
    rows=row_values,
  )

  # Return actual header row and row dicts
  print("Validated and Converted all non-header rows into dicts.")
  return SheetValues(headers=actual_headers, row_dicts=row_dicts)

def validate_required_headers_(
  actual_headers: List[str],
  required_headers: List[str],
  sheet_name: str,
) -> None:
  """
  Validate that all required headers are present in the actual headers from a Google Sheet.

  This function checks if all the required headers are present in the actual headers 
  retrieved from the sheet. If any required headers are missing, an exception is raised.

  Args:
    actual_headers (List[str]): The headers retrieved from the sheet.
    required_headers (List[str]): The headers that are expected to be present in the sheet.
    sheet_name (str): The name of the sheet being validated.

  Returns:
    bool: True if all required headers are present. Raises an exception if headers are missing.

  Raises:
    Exception: If any of the `required_headers` are missing from `actual_headers`.
  """
  missing_headers: List[str] = [hdr for hdr in required_headers if hdr not in actual_headers]
  if missing_headers:
    error_message: str = f"'{sheet_name}' is missing expected headers: {', '.join(missing_headers)}."
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=error_message,
    )
  
def create_row_dicts(
  required_headers: List[str],
  actual_headers: List[str],
  rows: List[List[Any]],
) -> List[Dict[str, Any]]:
  """
  Convert rows of data into a List of dictionaries based on required headers.

  This function maps the required headers to their corresponding values in each row. 
  If a row is shorter than the actual headers, it pads the missing values with empty 
  strings. The result is a List of dictionaries where each dictionary represents a row, 
  with keys from the required headers.

  Args:
      required_headers (List[str]): A List of headers to be used as keys in the dictionaries.
      actual_headers (List[str]): The headers retrieved from the sheet, used to determine 
                                  the position of the required headers.
      rows (List[List[str]]): The rows of data retrieved from the sheet.

  Returns:
      List[Dict[str, Any]]: A List of dictionaries where each dictionary represents a row of data, 
                            with keys from `required_headers`.

  Example:
    >>> required_headers = ["Name", "Age"]
    >>> actual_headers = ["ID", "Name", "Age", "Location"]
    >>> rows = [["1", "Alice", "30"], ["2", "Bob", "25", "LA"]]
    >>> create_row_dicts(required_headers, actual_headers, rows)
    [{'Name': 'Alice', 'Age': '30'}, {'Name': 'Bob', 'Age': '25'}]
  
  Notes:
      - If a row is shorter than the actual headers, missing values are filled with empty strings.
      - The function assumes that the required headers exist in the actual headers.
  """
  # Get index of each required header in actual headers
  hdr_pos: Dict[str, int] = { hdr: actual_headers.index(hdr) for hdr in required_headers }
  # Return List of row dicts
  return [
    { hdr: (row[hdr_pos[hdr]] if hdr_pos[hdr] < len(row) else "") for hdr in required_headers }
    for row in rows
  ]

def row_dicts_to_lists(
  header_row: List[str],
  row_dicts: List[Dict[str, str]],
) -> List[List[str]]:
  """
  Convert a List of dictionaries into a List of Lists based on a specified header order.

  This function takes a List of dictionaries where keys are column headers and values 
  are the corresponding cell values, and converts it into a List of Lists. Each List 
  represents a row, and the values are ordered according to the provided `header_row`.
  If a dictionary is missing a value for a given header, an empty string is used.

  Args:
    header_row (List[str]): A List of header strings representing the order of columns 
                          in the output Lists.
    row_dicts (List[Dict[str, str]]): A List of dictionaries where each dictionary 
                                    represents a row of data, with keys corresponding 
                                    to column headers.

  Returns:
    List[List[str]]: A List of Lists, where each inner List represents a row of values 
                    ordered according to `header_row`.

  Example:
    >>> header_row = ["Name", "Age", "Location"]
    >>> row_dicts = [
          {"Name": "Alice", "Age": "30", "Location": "NY"},
          {"Name": "Bob", "Age": "25"}  # Missing Location
        ]
    >>> row_dicts_to_Lists(header_row, row_dicts)
    [['Alice', '30', 'NY'], ['Bob', '25', '']]

  Notes:
    - If a dictionary does not contain a value for a particular header, an empty string 
      is used in its place.
    - The order of the headers in `header_row` determines the order of values in the 
      resulting Lists.
  """
  return [[row.get(hdr, "") for hdr in header_row]  for row in row_dicts]

async def post_row_dicts_to_spreadsheet(
  ss_properties: SheetProperties,
  row_dicts: List[Dict[str, Any]],
  clear_extra_rows: bool = True,
) -> None:
  """
  Post a List of row dictionaries to a Google Sheets spreadsheet and optionally clear extra rows.

  This function posts a List of dictionaries (`row_dicts`) to a specified Google Sheets spreadsheet. Each dictionary 
  is converted into a row of values, with keys corresponding to the headers in `header_row`. The values are posted 
  starting from row 2 in the specified sheet (just below the header). If `clear_extra_rows` is set to True, 
  it deletes any rows below the last posted row to maintain a clean spreadsheet.

  Args:
    spreadsheet_id (str): The ID of the Google Sheets spreadsheet where the data will be posted.
    sheet_name (str): The name of the sheet within the spreadsheet where data will be posted.
    header_row (List[str]): A List of strings representing the column headers. This defines the order of the 
                          values when posting the data.
    row_dicts (List[Dict[str, str]]): A List of dictionaries where each dictionary represents a row of data. 
                                    The keys of each dictionary should match the `header_row`.
    clear_extra_rows (bool, optional): A flag indicating whether to delete extra rows in the sheet after posting 
                                      the data. Defaults to True.

  Returns:
    None

  Raises:
    ValueError: If the sheet name is not found or if there are errors in retrieving sheet properties.

  Example:
    >>> post_row_dicts_to_spreadsheet(
            spreadsheet_id="your_spreadsheet_id",
            sheet_name="Sheet1",
            header_row=["Name", "Age", "Location"],
            row_dicts=[
                {"Name": "Alice", "Age": "30", "Location": "NY"},
                {"Name": "Bob", "Age": "25", "Location": "LA"}
            ],
            clear_extra_rows=True
        )
  
  Workflow:
    1. Converts `row_dicts` to a List of Lists (`row_Lists`) using `row_dicts_to_Lists` for posting.
    2. Determines the A1 notation range for posting data based on the size of the `header_row` and `row_dicts`.
    3. Posts the data to the specified range in the Google Sheets using `post_values`.
    4. Optionally, fetches the sheet's grid properties to determine the total row count and deletes any rows 
        beyond the last posted row if `clear_extra_rows` is True.

  Notes:
    - If `clear_extra_rows` is set to True and there are more rows in the sheet than posted, the extra rows 
      are deleted to ensure a clean sheet.
    - The function assumes that the sheet already contains headers in the first row. The posted data starts 
      from row 2 (A2).
  """
  spreadsheet_id = ss_properties.id
  sheet_name = ss_properties.sheet_name
  header_row = ss_properties.required_headers
  
  # Convert all row dicts to Lists of cell values
  row_lists: List[List[Any]] = row_dicts_to_lists(
    header_row=header_row,
    row_dicts=row_dicts
  )

  # Create range in A1Notation for posting range
  last_posting_column: str = index_to_column_letter(len(header_row))
  last_posting_row: int = len(row_lists) + 1
  cell_range: str = f"A2:{last_posting_column}{last_posting_row}"

  # Post all rows to spreadsheet
  await sheets_services.post_values(
    values=row_lists,
    spreadsheet_id=spreadsheet_id,
    sheet_name=sheet_name,
    cell_range=cell_range,
  )

  # Clear all extra rows if clear_extra_rows is selected
  if clear_extra_rows:
    # Fetch sheet Id and grid properties
    sheet_properties: Dict[str, int | Dict[str, int]] = await sheets_services.get_sheet_properties(
      spreadsheet_id=spreadsheet_id,
      sheet_name=sheet_name,
    )

    # Extract row count from sheet_properties
    row_count: int = sheet_properties["grid_properties"]["rowCount"] # type: ignore

    # If extra rows present in sheet, delete extra rows
    if row_count > last_posting_row:
      await sheets_services.delete_rows(
        spreadsheet_id=spreadsheet_id,
        sheet_id=sheet_properties["sheet_id"], # type: ignore
        start_index=last_posting_row,
        end_index=row_count, # type: ignore
      )

      print("Cleared extra data rows.")

def index_to_column_letter(index: int) -> str:
  letters: str = ""
  while index > 0:
    letters = chr(index % 26 + ord("A")) + letters
    index = index // 26
  return letters
