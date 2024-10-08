from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import asyncio

from api.services.cached_data.sales_reports import update_sales_reports, get_updated_sales_reports_rows

@asynccontextmanager
async def lifespan(app: FastAPI):
  asyncio.create_task(update_sales_reports())

  yield

app = FastAPI(lifespan=lifespan)

@app.get("/sales-reports/")
async def get_sales_reports() -> Dict[str, List[Dict[str, Any]]]:
  return {"sales_report_rows": get_updated_sales_reports_rows()[:5]}