from fastapi import HTTPException, status
from typing import List

from api.models.purchase_orders import PurchaseOrderOut, Log
from api.models.lightspeed import  ImportProduct
from api.models.sheets import RowDicts
from api.services.lightspeed.product_import import import_products
from api.services.lightspeed.get_import_result import get_import_result
from api.crud.purchase_orders import add_log_to_purchase_order
from api.crud.settings import get_lightspeed_settings

async def upload_products_to_ls(
  po: PurchaseOrderOut, products: List[ImportProduct], max_attempts: int = 5,
) -> RowDicts:

  ls_settings = get_lightspeed_settings()

  attempt: int = 1
  job_created = False
  job_id: int = 0

  while attempt <= max_attempts:
    if not job_created:
      add_log_to_purchase_order(
        id=po.id, log=Log(
          user="Internal", message=f"Uploading products to Lightspeed (Attempt: {attempt}).", type="log"
        ),
      )
      try:
        attempt += 1
        results = await import_products(products=products, ls_settings=ls_settings)
        is_completed = results.completed

        if is_completed:
          add_log_to_purchase_order(
            id=po.id, log=Log(user="Internal", message="Product uploaded successfully (LS).", type="log"),
          )
          return results.row_dicts
        else:
          add_log_to_purchase_order(
            id=po.id, log=Log(
              user="Internal", message=f"Failed to complete upload. Logs: {results.logs}", type="error"
            ),
          )
          log_string  = "".join(results.logs)

          if "Job ID" in log_string:
            job_created = True
            log_with_job_id = next(log for log in results.logs if "Job ID" in log)
            job_id = int(log_with_job_id[8:])

      except Exception as e:
        add_log_to_purchase_order(
          id=po.id, log=Log(user="Internal", message=f"Failed to upload. {str(e)}", type="error"),
        )

    else:
      add_log_to_purchase_order(
        id=po.id, log=Log(
          user="Internal", message="Retrieving Lightspeed import results.", type="log"
        ),
      )

      try:
        attempt += 1
        results = await get_import_result(job_id=job_id, ls_settings=ls_settings)
        is_completed = results.completed

        if is_completed:
          add_log_to_purchase_order(
            id=po.id, log=Log(user="Internal", message="Product uploaded successfully (LS).", type="log"),
          )
          return results.row_dicts
        else:
          add_log_to_purchase_order(
            id=po.id, log=Log(
              user="Internal",
              message=f"Failed to retrieve upload results. Logs: {results.logs}",
              type="error"
            ),
          )

      except Exception as e:
        add_log_to_purchase_order(
          id=po.id, log=Log(
            user="Internal", message=f"Failed to retrieve upload results. {str(e)}", type="log"
          )
        )

  raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Lightspeed upload failed.",
  )