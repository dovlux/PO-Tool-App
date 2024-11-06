from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime, timezone

from api.models.drive import FileCopyData

class PurchaseOrderIn(BaseModel):
  name: str
  is_ats: bool
  currency: Literal["USD", "EUR", "JPY", "GBP"]

class Log(BaseModel):
  user: str
  message: str
  type: Literal["user", "log", "error"]
  date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdditionalFees(BaseModel):
  shipping_fees: float
  customs_fees: float
  other_fees: float

class PurchaseOrderDB(PurchaseOrderIn):
  date_created: str
  status: str
  logs: List[Log]
  spreadsheet_id: str | None = None
  additional_fees: AdditionalFees | None = None
  currency_conversion: float = 1
  po_id: int | None = None

class PurchaseOrderOut(PurchaseOrderDB):
  id: int

class NewPurchaseOrderNonAts(FileCopyData):
  new_file_name: str
  source_file_id: str = "1cmFc3w0yJ76IzyBHZh2dQJ6xtP41XaokVd_GpwvrOLE"
  placement_folder_id: str = "19XENhjGC9zouuPdXD50tc9rM8I6PzKHi"

class NewPurchaseOrderAts(FileCopyData):
  new_file_name: str
  source_file_id: str = "1qUePOnteM1rN4DhNbCdjyDhsvE8IJqqTcwKX14vWCDU"
  placement_folder_id: str = "1YSxpBt-4naMhW6RJ5Ol_vSlCsHN4XXon"

class UpdatePurchaseOrder(BaseModel):
  status: str | None = None
  spreadsheet_id: str | None = None
  additional_fees: AdditionalFees | None = None
  po_id: int | None = None

class UndoPurchaseOrderStatus(BaseModel):
  status: str

class UpdatePurchaseOrderLog(BaseModel):
  logs: List[Log]

class UpdatePurchaseOrderPoId(BaseModel):
  po_id: int