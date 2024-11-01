from fastapi import APIRouter, BackgroundTasks
from typing import List

from api.models.response import ResponseMsg
from api.services.cached_data import sales_reports
from api.services.cached_data import marketplaces
from api.services.cached_data import list_prices
from api.services.cached_data import item_types
from api.services.cached_data import brand_codes
from api.services.cached_data import item_type_acronyms
from api.services.cached_data import valid_sizes
from api.models.cache import UpdateStatusOut

router = APIRouter(prefix="/api/dev/cache", tags=["Developer > Cache"])

@router.get("/status", response_model=List[UpdateStatusOut])
def get_all_update_statuses():
  return [
    UpdateStatusOut(**sales_reports.get_sales_reports_update_status().model_dump(), name="sales_reports"),
    UpdateStatusOut(**marketplaces.get_marketplaces_update_status().model_dump(), name="marketplaces"),
    UpdateStatusOut(**list_prices.get_list_price_update_status().model_dump(), name="list_prices"), 
    UpdateStatusOut(**item_types.get_item_types_update_status().model_dump(), name="item_types"),
    UpdateStatusOut(**brand_codes.get_brand_codes_update_status().model_dump(), name="brand_codes"),
    UpdateStatusOut(**item_type_acronyms.get_item_type_acronyms_update_status().model_dump(), name="item_type_acronyms"),
    UpdateStatusOut(**valid_sizes.get_valid_sizes_update_status().model_dump(), name="valid_sizes"),
  ]

@router.get("/sales-reports/update", response_model=ResponseMsg)
async def update_sales_reports(background_tasks: BackgroundTasks):
  background_tasks.add_task(sales_reports.update_sales_reports, repeat=False)
  return ResponseMsg(message="Update initiated for sales reports.")

@router.get("/marketplaces/update", response_model=ResponseMsg)
async def update_marketplaces(background_tasks: BackgroundTasks):
  background_tasks.add_task(marketplaces.update_marketplaces, repeat=False)
  return ResponseMsg(message="Update initiated for marketplaces.")

@router.get("/list-prices/update", response_model=ResponseMsg)
async def update_list_prices(background_tasks: BackgroundTasks):
  background_tasks.add_task(list_prices.update_list_prices, repeat=False)
  return ResponseMsg(message="Update initiated for List Prices.")

@router.get("/item-types/update", response_model=ResponseMsg)
async def update_item_types(background_tasks: BackgroundTasks):
  background_tasks.add_task(item_types.update_item_types, repeat=False)
  return ResponseMsg(message="Update initiated for Item Types.")

@router.get("/brand-codes/update", response_model=ResponseMsg)
async def update_brand_codes(background_tasks: BackgroundTasks):
  background_tasks.add_task(brand_codes.update_brand_codes, repeat=False)
  return ResponseMsg(message="Update initiated for Brand Codes.")

@router.get("/item-type-acronyms/update", response_model=ResponseMsg)
async def update_item_type_acronyms(background_tasks: BackgroundTasks):
  background_tasks.add_task(item_type_acronyms.update_item_type_acronyms, repeat=False)
  return ResponseMsg(message="Update initiated for Item Type Acronyms.")

@router.get("/valid-sizes/update", response_model=ResponseMsg)
async def update_valid_sizes(background_tasks: BackgroundTasks):
  background_tasks.add_task(valid_sizes.update_valid_sizes, repeat=False)
  return ResponseMsg(message="Update initiated for Valid Sizes.")