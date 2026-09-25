"""Read optional server-only configuration. Never expose secrets to the browser."""
import os
from pathlib import Path
def load_env():
 path=Path(__file__).resolve().parents[1]/'.env'
 if path.exists():
  for line in path.read_text(encoding='utf-8-sig').splitlines():
   if not line.strip() or line.lstrip().startswith('#') or '=' not in line:continue
   name,value=line.split('=',1);name=name.strip()
   if name in {'LLM_BASE_URL','LLM_API_KEY','LLM_MODEL','LOCAL_LLM','LOCAL_LLM_TIMEOUT','GEOCODER_URL','OVERPASS_URL','DATA_DIR','APP_ENV','ALLOWED_ORIGINS'}:
    os.environ.setdefault(name,value.strip().strip('"').strip("'"))
load_env()
