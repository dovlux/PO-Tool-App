import freecurrencyapi # type: ignore

client = freecurrencyapi.Client("fca_live_dEJSxj0K3ZrLgwczOfedAcsFx32PNdxPkJDaUxkT")

def get_exchange_rate(currency: str) -> float:
  response = client.latest(base_currency="USD", currencies=[currency]) # type: ignore
  data = response["data"] # type: ignore
  conversion_rate = data[currency] # type: ignore
  return conversion_rate # type: ignore