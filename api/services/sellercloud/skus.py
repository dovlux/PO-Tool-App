from typing import List
import asyncio
import base64
import pandas as pd
from io import BytesIO
from fastapi import HTTPException, status

from api.models.sellercloud import CreateProduct
from api.services.sellercloud.base import sellercloud_api_call

async def get_catalog_info(token: str, skus: List[str]): # type: ignore
  endpoint = "Catalog?model.sKU=" + ",".join(skus)
  page_query = ""
  page_number = 1
  results = []

  while True:
    catalog_info = await sellercloud_api_call(
      method="get", endpoint=endpoint + page_query, token=token
    )

    page_number += 1

    results = [*results, *catalog_info["Items"]] # type: ignore

    total_results = catalog_info["TotalResults"] # type: ignore
    if len(results) == total_results: # type: ignore
      return results # type: ignore
    else:
      page_query = f"&model.pageNumber={page_number}"

async def check_if_skus_exist(token: str, skus: List[str]) -> List[str]:
  skus_by_ten = [skus[i:i+10] for i in range(0, len(skus), 10)]
  all_catalogs = await asyncio.gather(*( # type: ignore
    get_catalog_info(token=token, skus=sku_list) for sku_list in skus_by_ten # type: ignore
  ))

  flat_catalog_list = [product for catalog in all_catalogs for product in catalog] # type: ignore

  return [product["ID"] for product in flat_catalog_list] # type: ignore

async def create_skus(
  token: str, company_id: int, products: List[CreateProduct],
) -> int:
  try:
    df = pd.DataFrame([product.model_dump() for product in products])

    file_stream = BytesIO()
    with pd.ExcelWriter(file_stream, engine="openpyxl") as writer:
      df.to_excel(writer, index=False) # type: ignore
    file_stream.seek(0)
    file_contents = file_stream.read()

    blob = base64.b64encode(file_contents).decode()
    
    metadata = { # type: ignore
      "Metadata": {
        "CreateProductIfDoesntExist": True,
        "DoNotUpdateProducts": True,
        "CompanyIdForNewProduct": company_id,
      },
      "FileExtension": "xlsx",
      "Format": 2,
      "FileContents": blob,
    }

    response = await sellercloud_api_call(
      method="post", endpoint="Catalog/Imports/Custom", token=token, body=metadata, # type: ignore
    )

    job_id = response["ID"] # type: ignore

    return job_id # type: ignore

  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not create SKUs. Error: {str(e)}",
    )