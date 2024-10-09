from pydantic import BaseModel
from datetime import datetime

class UpdateStatus(BaseModel):
  update_time: datetime
  status: str

class CachedDataUpdateStatus(BaseModel):
  sales_reports: UpdateStatus
  marketplaces: UpdateStatus
  list_prices: UpdateStatus