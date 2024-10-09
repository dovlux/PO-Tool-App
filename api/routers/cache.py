from fastapi import APIRouter, BackgroundTasks

from api.models.response import ResponseMsg
from api.services.cached_data import sales_reports
from api.services.cached_data import marketplaces
from api.models.cache import CachedDataUpdateStatus

router = APIRouter(prefix="/api/dev/cache", tags=["Cache"])

@router.get("/sales-reports/update", response_model=ResponseMsg)
async def update_sales_reports(background_tasks: BackgroundTasks):
  background_tasks.add_task(sales_reports.update_sales_reports, repeat=False)
  return ResponseMsg(message="Update initiated for sales reports.")

@router.get("/sales-reports/status", response_model=CachedDataUpdateStatus)
def get_sales_reports_update_status():
  status = sales_reports.get_sales_reports_update_status()
  return status

@router.get("/marketplaces/update", response_model=ResponseMsg)
async def update_marketplaces(background_tasks: BackgroundTasks):
  background_tasks.add_task(marketplaces.update_marketplaces, repeat=False)
  return ResponseMsg(message="Update initiated for marketplaces.")

@router.get("/marketplaces/status", response_model=CachedDataUpdateStatus)
def get_marketplaces_update_status():
  status = marketplaces.get_marketplaces_update_status()
  return status