from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from google.oauth2 import service_account
from googleapiclient.discovery import build #type: ignore
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from typing import Dict, List, Any
from functools import lru_cache
import io
import asyncio

@lru_cache()
def get_drive_service() -> Any:
  """
  Singleton function to initialize and return Google Drive API client.
  Ensures that the client is only created once and reused for all requests.
  """
  # Create credentials
  credentials = service_account.Credentials.from_service_account_file(
    "google-api-keys-file.json",
    scopes=["https://www.googleapis.com/auth/drive"],
  )
  # Initialize the Google Drive API client
  return build(serviceName="drive", version="v3", credentials=credentials)

async def get_folder_contents(
    folder_id: str,
    retries: int = 3,
    drive_service: Any = get_drive_service(),
  ) -> Dict[str, List[Dict[str, str]]]:
  """
  Fetch the contents of a specified Google Drive folder, including subfolders and spreadsheets.
  
  This function connects to the Google Drive API using service account credentials, 
  retrieves the list of files in the specified folder, and filters out subfolders and 
  Google Spreadsheets. If no files are found in the folder, a custom exception 
  (`NoFilesFoundError`) is raised. The function also includes error handling for 
  common issues like rate limiting and resource not found (404 errors). 

  It makes use of exponential backoff when encountering rate-limiting errors (HTTP 429), 
  retrying the request up to a specified number of times. The files are returned in 
  a structured format with their name and ID, allowing further operations on these files.

  Args:
    folder_id (str): The ID of the folder in Google Drive.
    retries (int, optional): The number of retries allowed in case of certain errors (default is 3).

  Returns:
    dict: A dictionary containing the lists of subfolders and spreadsheets in the folder. 
        The dictionary has two keys: "folders" and "spreadsheets", both of which map to 
        lists of dictionaries. Each dictionary contains 'name' and 'id' for the files.
        
  Raises:
    HttpException: Code 400 for empty folder, and Code 500 for other errors.

  Example:
    >>> get_folder_contents(folder_id="your-folder-id")
    {
      'folders': [{'name': 'Subfolder1', 'id': 'subfolder-id1'}],
      'spreadsheets': [{'name': 'Spreadsheet1', 'id': 'spreadsheet-id1'}]
    }
  """
  results: Dict[str, List[Dict[str, str]]] = { "folders": [], "spreadsheets": [], }
  attempt: int = 0

  # Check if folder exists and is accesible
  try:
    await run_in_threadpool(drive_service.files().get(fileId=folder_id).execute)
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Could not access folder.",
    )

  print(f"Retrieving contents of folder with ID: {folder_id}...")

  while attempt <= retries:
    try:
      # Call the Drive API to fetch contents from the specified folder
      response = await run_in_threadpool(
        drive_service.files().list(
          q=f"'{folder_id}' in parents",
          fields="files(name, id, mimeType)",
        ).execute
      )

      # Extract files data from API response 
      files = response.get("files", [])

      # Raise an exception if no files were found in the specified folder
      if not files:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="No folders or spreadsheets found in specified folder",
        )
      
      # Append folder and spreadsheet file data to results
      for file in files:
        file_info: Dict[str, str] = { "name": file.get("name", ""), "id": file.get("id", ""), }
        if file.get("mimeType") == "application/vnd.google-apps.folder":
          results["folders"].append(file_info)
        elif file.get("mimeType") == "application/vnd.google-apps.spreadsheet":
          results["spreadsheets"].append(file_info)

      print("Retrieved folder contents.")
      return results # Return the fetched contents

    except HttpError as http_error:
      # Handle HTTP errors returned by the Drive API
      status_code = http_error.resp.status
      # Handle drive quota exceeded error
      if status_code == 429:
        if attempt < retries:
          wait_time = 2 ** attempt # Exponential backoff
          print(f"Drive Quota exceeded. Will retry in {wait_time} seconds...")
          await asyncio.sleep(wait_time)
          attempt += 1
        else:
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Drive quota and max retries exceeded."
          )
      else:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=http_error.reason,
        )

    except HTTPException:
      raise

    except Exception as e:
      # Handle all other errors not specifically handled
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e),
      )
    
  return results

async def download_xlsx_file(
  file_id: str,
  retries: int = 3,
  drive_service: Any = get_drive_service(),
) -> io.BytesIO:
  attempt: int = 0

  print(f"Retrieving contents of xlsx file: {file_id}...")

  while attempt < retries:
    try:
      # Run blocking I/O operation in a threadpool to avoid blocking the event loop
      request = await run_in_threadpool(drive_service.files().get_media, file_id)

      file = io.BytesIO()
      downloader = MediaIoBaseDownload(file, request=request)

      done: bool = False
      while not done:
        # Download chunks in threadpool
        await run_in_threadpool(downloader.next_chunk)

      file.seek(0)

      print("Retrieved xlsx file contents.")
      return file
    
    except HttpError as http_error:
      # Handle HTTP errors returned by the Drive API
      status_code = http_error.resp.status
      # Handle drive quota exceeded error
      if status_code == 429:
        if attempt < retries:
          wait_time = 2 ** attempt # Exponential backoff
          print(f"Drive Quota exceeded. Will retry in {wait_time} seconds...")
          await asyncio.sleep(wait_time)
          attempt += 1
        else:
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Drive quota and max retries exceeded."
          )
      else:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=http_error.reason,
        )
    
    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
      )
    
  return io.BytesIO()

async def create_copy_of_file(
  source_file_id: str,
  new_file_name: str,
  placement_folder_id: str,
  retries: int = 3,
  drive_service: Any = get_drive_service(),
) -> str:
  """
  Create a copy of a specified Google Drive file and place it in a target folder with a new name.

  This function uses the Google Drive API to copy a file (specified by its file ID) to a target folder 
  (specified by its folder ID) and renames the copy. The function returns the ID of the newly created file.

  Args:
      source_file_id (str): The ID of the source file that you want to copy.
      new_file_name (str): The name for the newly created copy of the file.
      placement_folder_id (str): The ID of the folder where the new file will be placed.

  Returns:
      str: The ID of the newly created file.
  """
  attempt: int = 0

  print(f"Creating copy of file: {source_file_id}...")
  
  while attempt < retries:
    try:
      # Call Drive API to make copy of specified source file
      new_file = await run_in_threadpool(
        drive_service.files().copy(
          fileId=source_file_id,
          body={ "name": new_file_name, "parents": [placement_folder_id] },
        ).execute
      )

      # get id of created file
      new_file_id = new_file.get("id")

      print("Created file copy.")
      return new_file_id # Return the id of created file
    
    except HttpError as http_error:
      # Handle HTTP errors returned by the Drive API
      status_code = http_error.resp.status
      # Handle drive quota exceeded error
      if status_code == 429:
        if attempt < retries:
          wait_time = 2 ** attempt # Exponential backoff
          print(f"Drive Quota exceeded. Will retry in {wait_time} seconds...")
          await asyncio.sleep(wait_time)
          attempt += 1
        else:
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Drive quota and max retries exceeded."
          )
      else:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=http_error.reason,
        )
      
    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
      )
      
  return ""

async def create_permissions(
  resource_id: str,
  emails_to_permit: list[str],
  permission_type: str,
  send_notifications: bool = False,
  retries: int = 3,
  drive_service: Any = get_drive_service(),
) -> None:
  """
  Create permissions for a Google Drive resource (file or folder) and grant access to specified users.

  This function assigns the specified permission type (e.g., "reader", "writer") to a list of email addresses 
  for the given Google Drive resource (file or folder). For each email, it makes an API request to 
  grant the specified permissions. Optionally, it can send notification emails to the users.

  Args:
    resource_id (str): The ID of the Google Drive resource (file or folder) for which permissions are being set.
    emails_to_permit (list[str]): A list of email addresses to whom the specified permissions will be granted.
    permission_type (str): The type of permission to grant (e.g., "reader", "writer", "commenter").
    send_notifications (bool, optional): Whether to send notification emails to the users (default is False).

  Returns:
    None: This function does not return anything. It performs the action of granting permissions 
        and raises exceptions if the API request fails.

  Raises:
    HttpException: If an error occurs during the API call to Google Drive to create the permissions.
  
  Notes:
    - The `permission_type` parameter should be one of the valid Google Drive roles like 
      "reader", "writer", or "commenter".
    - If `send_notifications` is set to True, Google will notify the users via email that 
      they have been granted access.
    - The function calls the Google Drive API for each email in the list.
  """
  for email in emails_to_permit:
    body = { "type": "user", "role": permission_type, "emailAddress": email }

    attempt: int = 0

    print(f"Creating permissions for resource: {resource_id}...")

    while attempt < retries:
      try:
        # Call Drive API to create user permissions for specified resource
        await run_in_threadpool(
          drive_service.permissions().create(
            fileId=resource_id,
            body=body,
            fields="id",
            sendNotificationEmail=send_notifications,
          ).execute
        )

        print("Created permissions successfully")

      except HttpError as http_error:
        # Handle HTTP errors returned by the Drive API
        status_code = http_error.resp.status
        # Handle drive quota exceeded error
        if status_code == 429:
          if attempt < retries:
            wait_time = 2 ** attempt # Exponential backoff
            print(f"Drive Quota exceeded. Will retry in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            attempt += 1
          else:
            raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Drive quota and max retries exceeded."
            )
        else:
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=http_error.reason,
          )
        
      except Exception as e:
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=str(e)
        )