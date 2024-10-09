from pydantic import BaseModel

from api.models.drive import FileCopyData

class PurchaseOrderIn(BaseModel):
  name: str

class PurchaseOrderOut(PurchaseOrderIn):
  id: int
  spreadsheet_id: str
  status: str

class PurchaseOrderDb(PurchaseOrderOut):
  is_ats: bool

class NewPurchaseOrder(FileCopyData):
  new_file_name: str
  source_file_id: str = "1BUY7DhdLY0j443LJ6wh4YKWiBzH_qRD7yiw2tyxqcv0"
  placement_folder_id: str = "1CqJLJQn_0KYLriFgqUTlsgO_qzCAkhKm"
