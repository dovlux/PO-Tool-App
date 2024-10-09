from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from api.models.response import ResponseMsg
from api.services.cached_data import sales_reports
from api.models.cache import SalesReportsUpdateStatus

router = APIRouter(prefix="/api/dev/cache", tags=["Cache"])

@router.get("/sales-reports/update", response_model=ResponseMsg)
async def update_sales_reports(background_tasks: BackgroundTasks):
  try:
    background_tasks.add_task(sales_reports.update_sales_reports, repeat=False)
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Failed to initiate update for sales reports. {str(e)}",
    )
  
  return ResponseMsg(message="Update initiated for sales reports.")

@router.get("/sales-reports/status", response_model=SalesReportsUpdateStatus)
def get_sales_reports_update_status():
  status = sales_reports.get_sales_reports_update_status()
  return status