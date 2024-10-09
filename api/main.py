from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from api.services.cached_data.sales_reports import update_sales_reports
from api.services.cached_data.marketplaces import update_marketplaces
from api.services.cached_data.list_prices import update_list_prices
from api.routers.cache import router as cache_router

@asynccontextmanager
async def lifespan(app: FastAPI):
  sales_report_update_task = asyncio.create_task(update_sales_reports(repeat=True))
  marketplaces_update_task = asyncio.create_task(update_marketplaces(repeat=True))
  list_prices_update_task = asyncio.create_task(update_list_prices(repeat=True))

  yield

  sales_report_update_task.cancel()
  marketplaces_update_task.cancel()
  list_prices_update_task.cancel()

  try:
    await sales_report_update_task
    await marketplaces_update_task
    await list_prices_update_task
  except asyncio.CancelledError:
    pass

app = FastAPI(lifespan=lifespan)

app.include_router(cache_router)