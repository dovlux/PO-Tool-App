from fastapi import APIRouter
from typing import List, Dict

from api.crud.settings import get_sellercloud_settings
from api.services.sellercloud.base import get_token
from api.services.sellercloud.skus import get_catalog_info, check_if_skus_exist, create_skus
from api.services.sellercloud.jobs import set_job_priority_to_critical
from api.models.sellercloud import CreateProduct

router = APIRouter(prefix="/api/sellercloud", tags=["Sellercloud"])

@router.post("/get-token", response_model=Dict[str, str])
async def get_bearer_token():
  sc_settings = get_sellercloud_settings()
  bearer_token = await get_token(sc_settings=sc_settings)
  return { "token": bearer_token }

@router.post("/get-catalog-info")
async def get_product_catalog_info(skus: List[str]) -> List[str]:
  sc_settings = get_sellercloud_settings()
  token = await get_token(sc_settings=sc_settings)
  catalog_info = await get_catalog_info(token=token, skus=skus) # type: ignore
  return catalog_info # type: ignore

@router.post("/check-if-skus-exist")
async def get_existing_skus(skus: List[str]) -> List[str]:
  sc_settings = get_sellercloud_settings()
  token = await get_token(sc_settings=sc_settings)
  existing_skus = await check_if_skus_exist(token=token, skus=skus)
  return existing_skus

@router.post("/create-skus")
async def create_products(products: List[CreateProduct]) -> int:
  sc_settings = get_sellercloud_settings()
  token = await get_token(sc_settings=sc_settings)
  job_id = await create_skus(token=token, company_id=sc_settings.default_company_id, products=products)
  await set_job_priority_to_critical(token=token, job_id=job_id)
  print("Reached return")
  return job_id
