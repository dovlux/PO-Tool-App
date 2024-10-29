from fastapi import APIRouter

from api.services.currency_api.currency_queries import get_exchange_rate
from api.models.response import CurrencyExchange

router = APIRouter(prefix="/api/currency-exchange", tags=["Currency Conversion"])

@router.get("/{currency}", response_model=CurrencyExchange)
def get_conversion_rate(currency: str):
  rate = get_exchange_rate(currency=currency)
  return CurrencyExchange(rate=rate)