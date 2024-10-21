from fastapi import APIRouter

from api.models import settings as settings_models
from api.crud import settings as settings_crud
from api.models.response import ResponseMsg

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/breakdown-net-sales", response_model=settings_models.BreakdownNetSalesSettings)
def get_breakdown_net_sales_settings():
  settings = settings_crud.get_breakdown_net_sales_settings()
  return settings

@router.put("/breakdown-net-sales", response_model=ResponseMsg)
def update_breakdown_net_sales_settings(updates: settings_models.UpdateBreakdownNetSalesSettings):
  message = settings_crud.update_breakdown_net_sales_settings(updates=updates)
  return message