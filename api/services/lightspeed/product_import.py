from typing import List
from fastapi import HTTPException, status
import pandas as pd
from io import BytesIO
import aiohttp

from api.models.lightspeed import ImportProduct, ImportResults
from api.models.sheets import RowDicts
from api.models.settings import LightspeedSettings
from api.services.utils.csv_to_lists import csv_to_lists
from api.services.google_api.sheets_utils import create_row_dicts

async def import_products(
  products: List[ImportProduct], ls_settings: LightspeedSettings,
) -> ImportResults:
  try:
    df = pd.DataFrame([product.model_dump(by_alias=True) for product in products])

    file_stream = BytesIO()
    with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
      df.to_excel(writer, index=False) # type: ignore
    file_stream.seek(0)
    file_contents = file_stream.read()

    url = f"http://{ls_settings.server_ip}:{ls_settings.port}/"
    url += f"import?username={ls_settings.username}&password={ls_settings.password}"

    form_data = aiohttp.FormData()
    form_data.add_field(
      "file", file_contents, filename="products.xlsx",
      content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    async with aiohttp.ClientSession() as session:
      async with session.post(url=url, data=form_data) as response:
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
      detail=f"Could not import to Lightspeed. Error: {str(e)}",
    )