from fastapi import APIRouter
from typing import List, Dict

from api.services.sellercloud.base import get_token
from api.services.sellercloud.skus import get_catalog_info

router = APIRouter(prefix="/api/sellercloud", tags=["Sellercloud"])

@router.post("/get-token", response_model=Dict[str, str])
async def get_bearer_token():
  bearer_token = await get_token()
  return { "token": bearer_token }

@router.post("/get-catalog-info")
async def get_product_catalog_info(skus: List[str]):
  token = await get_token()
  catalog_info = await get_catalog_info(token=token, skus=skus)
  return catalog_info