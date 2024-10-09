from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from firebase_admin import credentials, initialize_app # type: ignore

cred = credentials.Certificate("google-firebase-adminsdk.json")
initialize_app(credential=cred)

from api.services.cached_data.sales_reports import update_sales_reports
from api.services.cached_data.marketplaces import update_marketplaces
from api.services.cached_data.list_prices import update_list_prices
from api.services.cached_data.item_types import update_item_types
from api.routers.cache import router as cache_router
from api.routers.purchase_orders import router as po_router

@asynccontextmanager
async def lifespan(app: FastAPI):
  sales_report_update_task = asyncio.create_task(update_sales_reports(repeat=True))
  marketplaces_update_task = asyncio.create_task(update_marketplaces(repeat=True))
  list_prices_update_task = asyncio.create_task(update_list_prices(repeat=True))
  item_types_update_task = asyncio.create_task(update_item_types(repeat=True))

  yield

  sales_report_update_task.cancel()
  marketplaces_update_task.cancel()
  list_prices_update_task.cancel()
  item_types_update_task.cancel()

  try:
    await sales_report_update_task
    await marketplaces_update_task
    await list_prices_update_task
    await item_types_update_task
  except asyncio.CancelledError:
    pass

app = FastAPI(lifespan=lifespan)

app.include_router(cache_router)
app.include_router(po_router)