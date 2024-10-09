from pydantic import BaseModel

class FileCopyData(BaseModel):
  new_file_name: str
  source_file_id: str
  placement_folder_id: str
