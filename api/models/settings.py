from pydantic import BaseModel
from typing import Dict, List

class BreakdownNetSalesSettings(BaseModel):
  confidence_discounts: Dict[str, float]
  confidence_options: List[str]
  marketplace_groups: List[str]
  monthly_opportunity_cost: int
  net_sales_percentages: Dict[str, float]
  sales_history_months: int
  sell_through_options: List[str]

class UpdateBreakdownNetSalesSettings(BaseModel):
  confidence_discounts: Dict[str, float] | None = None
  confidence_options: List[str] | None = None
  marketplace_groups: List[str] | None = None
  monthly_opportunity_cost: int | None = None
  net_sales_percentages: Dict[str, float] | None = None
  sales_history_months: int | None = None
  sell_through_options: List[str] | None = None

class SellercloudSettings(BaseModel):
  username: str
  password: str
  default_company_id: int
  ats_company_id: int
  ats_vendor_id: int
  ats_warehouse_id: int

class LightspeedSettings(BaseModel):
  username: str
  password: str
  server_ip: str
  port: str

class AtsSkuCreationSettings(BaseModel):
  brand_code: str
  sku_number: int

class UpdateAtsSkuCreationSettings(BaseModel):
  sku_number: int

class EbayDiscountSettings(BaseModel):
  discount: float