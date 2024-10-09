from pydantic import BaseModel
from datetime import datetime

class CachedDataUpdateStatus(BaseModel):
  update_time: datetime
  status: str