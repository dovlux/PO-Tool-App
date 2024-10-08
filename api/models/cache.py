from pydantic import BaseModel
from datetime import datetime

class UpdateStatus(BaseModel):
  update_time: datetime
  status: str

class UpdateStatusOut(UpdateStatus):
  name: str