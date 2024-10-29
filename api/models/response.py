from pydantic import BaseModel

class ResponseMsg(BaseModel):
  message: str

class CurrencyExchange(BaseModel):
  rate: float