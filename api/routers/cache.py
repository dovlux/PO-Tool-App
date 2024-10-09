from fastapi import APIRouter, BackgroundTasks

from api.models.response import ResponseMsg
from api.services.cached_data import sales_reports
from api.services.cached_data import marketplaces
from api.services.cached_data import list_prices
from api.models.cache import CachedDataUpdateStatus

router = APIRouter(prefix="/api/dev/cache", tags=["Cache"])

@router.get("/status", response_model=CachedDataUpdateStatus)
def get_all_update_statuses():
  return CachedDataUpdateStatus(
    sales_reports=sales_reports.get_sales_reports_update_status(),
    marketplaces=marketplaces.get_marketplaces_update_status(),
    list_prices=list_prices.get_list_price_update_status(),
  )

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