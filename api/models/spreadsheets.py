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

class SalesReportProperties(SheetProperties):
  sheet_name: str = "Sheet1"
  required_headers: List[str] = [
    "Transaction Date", "Trans Type", "Order #", "Order Date", "Ship Date",
    "Marketplace", "Channel Order #", "SKU", "Qty", "Tax", "Discount", "Grand Total",
    "Accrual Refund", "Payments", "Refunds", "Adjustments",
    "Grand Total + Adjustmensts - Tax + Accrual Refunds", "Items Cost", "Shipping Cost",
    "Commission", "Profit", "Brand", "ProductName", "ProductTypeName", "Type", "Gender",
    "Age Since Received", "Vendor", "Sales Rep"
  ]

class MarketplaceProperties(SheetProperties):
  id: str = "1-WzeSkR_eoLCxLjn8A6-evvRboiFFslS"
  sheet_name: str = "Marketplaces"
  required_headers: List[str] = ["Marketplace", "Group"]

class ListPricesProperties(SheetProperties):
  id: str = "1FGzOvXv0q3EDxmUzSGvybBr8OUh2tOzXsVHb28p0v-Y"
  sheet_name: str = "Prices"
  required_headers: List[str] = ["ProductID", "ListPrice"]