"""One-time optional model setup; subsequent inference explicitly forbids network."""
from pathlib import Path
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[1]
snapshot_download('Qwen/Qwen3-0.6B',local_dir=ROOT/'models/qwen3-0.6b',allow_patterns=['*.json','*.safetensors','*.txt','*.jinja','LICENSE','README.md'],max_workers=3)
print('Local model ready.')
