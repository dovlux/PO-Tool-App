import re

def remove_special_chars(mpn: str) -> str:
  # Remove non-word characters
  mpn = re.sub(r'\W', '', mpn)
  # Remove leading or trailing underscores
  mpn = re.sub(r'^_+|_+$', '', mpn)
  # Remove multiple underscores
  mpn = re.sub(r'_+', '', mpn)
  # Convert to uppercase
  return mpn.upper()

def format_mpn(mpn: str):
  # Replace non-word characters with underscores
  mpn = re.sub(r'\W', '_', mpn)
  # Remove leading or trailing underscores
  mpn = re.sub(r'^_+|_+$', '', mpn)
  # Replace multiple underscores with a single one
  mpn = re.sub(r'_+', '_', mpn)
  # Convert to uppercase
  return mpn.upper()