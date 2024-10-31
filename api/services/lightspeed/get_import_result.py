from fastapi import HTTPException, status
import aiohttp

from api.models.settings import LightspeedSettings
from api.models.sheets import RowDicts
from api.models.lightspeed import ImportResults
from api.services.google_api.sheets_utils import create_row_dicts
from api.services.utils.csv_to_lists import csv_to_lists

async def get_import_result(
  job_id: int, ls_settings: LightspeedSettings,
) -> ImportResults:
  try:
    url = f"http://{ls_settings.server_ip}:{ls_settings.port}/"
    url += f"importresult/?username={ls_settings.username}&password={ls_settings.password}"
    url += f"&jobId={job_id}"

    async with aiohttp.ClientSession() as session:
      async with session.get(url=url) as response:
        status_code = response.status
        response_text = await response.text()

        if status_code != 200:
          try:
            script_logs = await response.json()
            script_logs = script_logs.get("scriptlogs", []) # type: ignore
            if not script_logs:
              raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not find 'scriptlogs' in response.",
              )
            return ImportResults(completed=False, logs=script_logs)
          except Exception as e:
            raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail=f"Could not upload products to Lightspeed. Error: {str(e)}"
            )
        else:
          results = csv_to_lists(csv_string=response_text)
          row_dicts = create_row_dicts(
            required_headers=["System ID", "Custom SKU"],
            actual_headers=results[0],
            rows=results[1:],
          )
          return ImportResults(completed=True, row_dicts=RowDicts(row_dicts=row_dicts))

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve import results. Error {str(e)}",
    )