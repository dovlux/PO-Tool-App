import csv
import io
from typing import List

def csv_to_lists(csv_string: str) -> List[List[str]]:
  csv_file = io.StringIO(csv_string)
  reader = csv.reader(csv_file)
  data = [row for row in reader]
  return data