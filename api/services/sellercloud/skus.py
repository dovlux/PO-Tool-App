from typing import List

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
  existing_catalog = await get_catalog_info(token=token, skus=skus) # type: ignore
  return [product["ID"] for product in existing_catalog] # type: ignore
    