from api.services.sellercloud.base import sellercloud_api_call

async def set_job_priority_to_critical(token: str, job_id: int) -> None:
  endpoint = "QueuedJobs/Priority"
  body = { "ID": job_id, "Priority": 3 }

  await sellercloud_api_call(
    method="put", endpoint=endpoint, token=token, body=body,
  )