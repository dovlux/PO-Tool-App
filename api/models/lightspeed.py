from pydantic import BaseModel, Field
from typing import List

from api.models.sheets import RowDicts

class ImportProduct(BaseModel):
  Description: str
  custom_sku: str = Field(..., alias="Custom SKU")
  manufacturer_sku: str = Field(..., alias="Manufacturer SKU")
  Brand: str
  default_cost: str = Field("", alias="Default Cost")
  default_price: str = Field(..., alias="Default - Price")
  msrp_price: str = Field(..., alias="MSRP = Price")
  Category: str

class ImportResults(BaseModel):
  completed: bool
  row_dicts: RowDicts = RowDicts(row_dicts=[])
  logs: List[str] = []
