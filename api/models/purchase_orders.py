from pydantic import BaseModel

from api.models.drive import FileCopyData

class PurchaseOrderIn(BaseModel):
  name: str
  is_ats: bool

class PurchaseOrderDB(PurchaseOrderIn):
  date_created: str
  status: str
  spreadsheet_id: str | None = None

class PurchaseOrderOut(PurchaseOrderDB):
  id: int

class NewPurchaseOrderNonAts(FileCopyData):
  new_file_name: str
  source_file_id: str = "1BUY7DhdLY0j443LJ6wh4YKWiBzH_qRD7yiw2tyxqcv0"
  placement_folder_id: str = "1CqJLJQn_0KYLriFgqUTlsgO_qzCAkhKm"

class NewPurchaseOrderAts(FileCopyData):
  new_file_name: str
  source_file_id: str = "1Bw1osidVZlmZUFEtiXS6TE-XI-aHN_hXNrCqsZspJOo"
  placement_folder_id: str = "1CqJLJQn_0KYLriFgqUTlsgO_qzCAkhKm"

class UpdatePurchaseOrder(BaseModel):
  status: str | None = None
  spreadsheet_id: str | None = None