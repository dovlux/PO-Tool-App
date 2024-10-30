import httpx
from typing import Literal, Dict, Any
from fastapi import HTTPException, status

from api.models.settings import SellercloudSettings

url_header = "https://lux.api.sellercloud.com/rest/api/"

async def sellercloud_api_call(
  method: Literal["get", "post", "put", "delete"],
  endpoint: str, token: str, body: Dict[str, Any] | None = None,
):
  headers = { "Authorization": f"Bearer {token}"}
  url = url_header + endpoint

  async with httpx.AsyncClient() as client:
    if method == "get":
      response = await client.get(url=url, headers=headers)
    elif method == "post":
      response = await client.post(url=url, json=body, headers=headers)
    elif method == "put":
      response = await client.put(url=url, json=body, headers=headers)
    else:
      response = await client.delete(url=url, headers=headers)

    if response.status_code == 200:
      if method != "put":
        data = response.json()
        return data
    else:
      response.raise_for_status()

async def get_token(sc_settings: SellercloudSettings) -> str:
  url = url_header + "token"
  body = { "username": sc_settings.username, "password": sc_settings.password }

  try:
    async with httpx.AsyncClient() as client:
      response = await client.post(url=url, json=body)

      if response.status_code == 200:
        data = response.json()
        return data["access_token"]
      else:
        response.raise_for_status()
        return ""
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not retrieve access token from sellercloud. Error: {str(e)}",
    )