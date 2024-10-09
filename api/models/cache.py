from pydantic import BaseModel
from datetime import datetime

class SalesReportsUpdateStatus(BaseModel):
  update_time: datetime
  status: str