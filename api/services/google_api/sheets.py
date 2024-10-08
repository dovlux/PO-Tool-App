from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from google.oauth2 import service_account
from googleapiclient.discovery import build # type: ignore
from googleapiclient.errors import HttpError
from functools import lru_cache
from typing import Any, List, Dict
import asyncio

@lru_cache()
def get_sheets_service() -> Any:
  """
  Singleton function to initialize and return Google Sheets API client.
  Ensures that the client is only created once and reused for all requests.
  """
  # Create credentials
  credentials = service_account.Credentials.from_service_account_file(
    "google-api-keys-file.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
  )
  # Initialize the Google Drive API client
  return build(serviceName="sheets", version="v4", credentials=credentials)

async def get_values(
  spreadsheet_id: str,
  sheet_name: str,
  cell_range: str | None = None,
  retries: int = 3,
  sheets_service: Any = get_sheets_service(),
) -> List[List[Any]]:
  """
  Fetch values from a specified range in a Google Sheets spreadsheet.

  This function retrieves values from a specific range in a Google Sheets sheet. It handles
  retries in case of quota exceeded errors (HTTP 429) using exponential backoff, and manages
  other HTTP errors such as incorrect spreadsheet ID or missing permissions.

  Args:
    spreadsheet_id (str): The ID of the Google Sheets spreadsheet to retrieve values from.
    sheet_name (str): The name of the sheet in the spreadsheet to fetch data from.
    cell_range (str, optional): The A1 notation range in the sheet from which to retrieve values 
                              (e.g., 'A1:D10'). If not provided, the entire sheet is used.
    retries (int, optional): The number of retry attempts in case of quota-related errors (HTTP 429).
                            Defaults to 3.

  Returns:
    list[list[str]]: A 2D list containing the values from the specified cell range. Each inner
                          list represents a row of data.

  Raises:
    HTTPException: an error with a status code of 400 or 500, with a detail property.
 
  Example Usage:
    >>> get_values("your_spreadsheet_id", "Sheet1", "A1:B10")

    This example retrieves values from the range A1:B10 in "Sheet1" of the specified Google Spreadsheet.
  """
  attempt: int = 0

  print(
    f"Retrieving values from cells in '{cell_range or 'All Cells'}' range" +
    f" in {sheet_name} sheet from spreadsheet: {spreadsheet_id}..."
  )

  while attempt <= retries:
    try:
      # Call the Sheets API to fetch data from the specified range
      result = await run_in_threadpool(
          sheets_service.spreadsheets().values().get(
          spreadsheetId=spreadsheet_id,
          range=f"{sheet_name}{f"!{cell_range}" if cell_range else ""}",
          valueRenderOption='UNFORMATTED_VALUE',
        ).execute
      )

      # Extract values from the API response
      values: List[List[Any]] | None = result.get("values", None)

      # Raise an exception if no data is found in the specified range
      if values is None:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="No values found in specified spreadsheet range.",
        )
      
      print("Retrieved values from spreadsheet range.")
      return values # Return the fetched values
    
    except HTTPException:
      raise
    
    except HttpError as http_error:
      # Handle HTTP errors returned by the Sheets API
      await handle_http_exceptions(
        http_error=http_error,
        retries=retries,
        attempt=attempt,
      )
      attempt += 1
      
    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e),
      )
    
  return [[""]]

async def get_sheet_properties(
  spreadsheet_id: str,
  sheet_name: str,
  retries: int = 3,
  sheets_service: Any = get_sheets_service(),
) -> Dict[str, int | Dict[str, int]]:
  """
  Retrieve the sheet properties (sheetID, row and column count) for a specific sheet within a Google Sheets spreadsheet.

  Args:
    spreadsheet_id (str): The ID of the Google Sheets spreadsheet.
    sheet_name (str): The name of the sheet from which to fetch grid properties.

  Returns:
    dict: A dictionary containing the sheet grid properties of the specified sheet.

  Raises:
    HTTPException: If the sheet with the specified name is not found or any other exceptions occur.
  """
  attempt: int = 0

  print(f"Retrieving sheet grid properties for {sheet_name} sheet in spreadsheet: {spreadsheet_id}...")

  while attempt < retries:
    try:
      # Fetch metadata of sheets in specified spreadsheet
      sheet_metadata = await run_in_threadpool(
        sheets_service.spreadsheets().get(
          spreadsheetId=spreadsheet_id,
          fields="sheets(properties.gridProperties,properties.title,properties.sheetId)",
        ).execute
      )
      
      # Extract the relevant sheet's grid properties
      sheets = sheet_metadata.get("sheets", [])
      for sheet in sheets:
        properties = sheet.get("properties", {})
        if properties.get("title", "") == sheet_name:
          grid_properties: Dict[str, int] = properties.get("gridProperties", {})

          print("Retrieved sheet grid properties.")
          return {"sheet_id": properties.get("sheetId"), "grid_properties": grid_properties}
    
    except HttpError as http_error:
      # Handle HTTP errors returned by the Sheets API
      status_code = http_error.resp.status
      # Handle drive quota exceeded error
      if status_code == 429:
        if attempt < retries:
          wait_time = 2 ** attempt # Exponential backoff
          print(f"Sheets Quota exceeded. Will retry in {wait_time} seconds...")
          await asyncio.sleep(wait_time)
          attempt += 1
        else:
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sheets quota and max retries exceeded."
          )
      else:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=http_error.reason,
        )
      
    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e),
      )
    
  return {}

async def post_values(
  values: list[list[Any]],
  spreadsheet_id: str,
  sheet_name: str,
  cell_range: str | None = None,
  user_entered: bool = True,
  retries: int = 3,
  sheets_service: Any = get_sheets_service(),
) -> None:
  """
  Post values to a specified range in a Google Sheets spreadsheet.

  This function posts values to a specified range within a sheet in the Google Sheets 
  document. It handles retries in case of quota exceeded errors (HTTP 429) using exponential 
  backoff, and it manages other HTTP errors such as incorrect spreadsheet IDs or missing 
  permissions.

  Args:
    values (list[list[any]]): A 2D list of values to post into the sheet. Each inner list represents a row.
    spreadsheet_id (str): The ID of the Google Sheets spreadsheet where values should be posted.
    sheet_name (str): The name of the sheet within the spreadsheet where values should be posted.
    cell_range (str | None, optional): The A1 notation range in the sheet where the values should be posted 
                                      (e.g., 'A1:D10'). If not provided, the values will be posted starting 
                                      from the top-left cell.
    user_entered (bool, optional): If True, values are interpreted by Google Sheets, e.g., formulas are evaluated 
                                  and formats are applied. If False, values are input as-is. Defaults to True.
    retries (int, optional): The number of retry attempts in case of quota-related errors. Defaults to 3.

  Raises:
    HTTPException: Raised if a non-retriable HTTP error occurs (e.g., 404 for missing spreadsheet or sheet).

  Example Usage:
    >>> post_values([["Name", "Age"], ["Alice", "30"]], "your_spreadsheet_id", "Sheet1", "A1:B2", user_entered=True)
      
    This example posts two rows of values to the range A1:B2 in "Sheet1" of the specified Google Spreadsheet.
  """
  attempt: int = 0

  print(f"Posting values to {sheet_name} sheet of spreadsheet: {spreadsheet_id}...")

  while attempt <= retries:
    try:
      # Call the sheets API to post values in the specified range
      await run_in_threadpool(
        sheets_service.spreadsheets().values().update(
          spreadsheetId=spreadsheet_id,
          range=f"{sheet_name}{f"!{cell_range}" if cell_range else ""}",
          valueInputOption="USER_ENTERED" if user_entered else "RAW",
          body={"values": values},
        ).execute
      )

      print("Posted value to sheet.")
      return

    except HttpError as http_error:
      # Handle HTTP errors returned by the Sheets API
      await handle_http_exceptions(
        http_error=http_error,
        retries=retries,
        attempt=attempt,
      )
      attempt += 1

    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e),
      )
  
async def delete_rows(
    spreadsheet_id: str,
    sheet_id: int,
    start_index: int,
    end_index: int,
    retries: int = 3,
    sheets_service: Any = get_sheets_service(),
  ) -> None:
    """
    Delete a group of rows in a Google Sheets spreadsheet.

    Args:
      spreadsheet_id (str): The ID of the Google Sheets spreadsheet.
      sheet_id (int): The ID of the sheet where rows will be deleted.
      start_index (int): The index of the first row to delete (0-based index).
      end_index (int): The index of the row after the last row to delete (non-inclusive).

    Returns:
        None
    """
    # Create the request to delete the specified rows
    delete_request: Dict[str, List[Dict[str, Dict[str, Dict[str, int | str]]]]] = {
      "requests": [
        {
          "deleteDimension": {
            "range": {
              "sheetId": sheet_id,
              "dimension": "ROWS",
              "startIndex": start_index,
              "endIndex": end_index
            }
          }
        }
      ]
    }

    attempt: int = 0

    print("Deleting extra rows from sheet...")

    while attempt < retries:
      try:
        # Execute the batchUpdate request to delete the rows
        await run_in_threadpool(
          sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=delete_request,
          ).execute
        )

        print("Deleted extra rows.")
        return

      except HttpError as http_error:
        # Handle HTTP errors returned by the Sheets API
        status_code = http_error.resp.status
        # Handle drive quota exceeded error
        if status_code == 429:
          if attempt < retries:
            wait_time = 2 ** attempt # Exponential backoff
            print(f"Sheets Quota exceeded. Will retry in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            attempt += 1
          else:
            raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Sheets quota and max retries exceeded."
            )
        else:
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=http_error.reason,
          )
        
      except Exception as e:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=str(e),
        )

async def handle_http_exceptions(
  http_error: HttpError,
  retries: int,
  attempt: int,
) -> None:
  """
  Handle HTTP errors returned by the Google Sheets API.

  This function processes HTTP errors that may occur during interactions with
  the Google Sheets API, such as incorrect spreadsheet ID, missing sheet name, 
  permission issues, and quota exceeded errors. It also implements exponential 
  backoff for retries in case of quota-related errors.

  Args:
    http_error (HttpError): The error object returned by the Google Sheets API.
                          Contains detailed information about the HTTP error.
    retries (int): The maximum number of retries allowed when handling quota-exceeded errors (HTTP 429).
    attempt (int): The current attempt number. This is used to calculate the exponential backoff delay.

  Raises:
    HTTPException: Raises HTTPException when a non-retriable error (e.g., 404, 403, 400) occurs, or 
              when the retry limit is reached for quota-exceeded errors (HTTP 429).

  Error Handling:
    - 404: If the spreadsheet ID is not found, this function will raise an error and stop further retries.
    - 400: If the sheet name is invalid or doesn't exist, or if the posted values exceed the allowed range, 
          an error is raised with specific messaging for each case.
    - 403: If the user does not have permission to access the spreadsheet, an error is raised and no retries occur.
    - 429: If the quota limit is exceeded, the function implements exponential backoff and retries the operation
          up to the number of retries specified. After exceeding the retry limit, the error is raised.

  Example Usage:
    >>> handle_http_exceptions(http_error, "spreadsheet_id", "Sheet1", retries=3, attempt=1)

    If an HTTP 429 error is encountered during the first attempt, the function waits for 2^1 seconds (2 seconds) 
    before retrying. This delay increases exponentially with each subsequent retry attempt.
  """
  status_code: int = http_error.resp.status # get error status code
  error_message = http_error.resp.reason # get error message

  if status_code == 404:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Spreadsheet does not exist.",
    )
  elif status_code == 400:
    if "Requested writing within range" in error_message:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Data posted does not match specified range",
      )
    elif "Unable to parse range" in error_message:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Sheet with this name does not exist in spreadsheet."
      )
  elif status_code == 403:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="User does not have access to the spreadsheet.",
    )
  elif status_code == 429:
    # Handle Sheets quota exceeded error
    if attempt < retries:
      wait_time = 2 ** attempt # Exponential backoff
      print(f"Sheets Quota exceeded. Retrying in {wait_time} seconds...")
      await asyncio.sleep(wait_time)
    else:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Sheets quota and max retries exceeded."
      )
  else:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=error_message,
    )
