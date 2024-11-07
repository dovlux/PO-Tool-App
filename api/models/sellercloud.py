from pydantic import BaseModel

class CreateProduct(BaseModel):
  ProductID: str
  ProductName: str
  ManufacturerSKU: str
  BrandName: str
  ListPrice: str
  WebsitePrice: str
  SitePrice: str
  BuyItNowPrice: str
  ProductTypeName: str
  SiteCost: str = ""
  LightspeedPOSEnabled: str = "TRUE"
  LIGHTSPEED_SYSTEM_ID: str
  UPC: str
  ASSIGN_TO_ATS: bool

class PoAddProduct(BaseModel):
  ProductID: str
  QtyUnitsOrdered: int
  UnitPrice: float

class PoReceiveProduct(BaseModel):
  ID: str
  QtyToReceive: int