from pydantic import BaseModel
from typing import List, Dict, Any

class RowDicts(BaseModel):
  row_dicts: List[Dict[str, Any]]

class SheetValues(RowDicts):
  headers: List[str]

class SheetProperties(BaseModel):
  id: str
  sheet_name: str
  required_headers: List[str]