from fastapi import HTTPException, status

def get_previous_status(current_status: str) -> str:
  if current_status == "Breakdown Created":
    return "Worksheet Created"
  elif current_status == "Net Sales Calculated" or current_status == "Errors in worksheet (Net Sales)":
    return "Breakdown Created"
  else:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Could not undo status: '{current_status}'.",
    )