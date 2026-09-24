"""Isolated local open-model inference. Parent enforces a wall-clock timeout."""
import sys,json
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
torch.set_num_threads(4)
path=Path(__file__).resolve().parents[1]/'models/qwen3-0.6b'
request=json.loads(sys.stdin.read())
tok=AutoTokenizer.from_pretrained(path,local_files_only=True)
model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,dtype=torch.float32)
prompt=tok.apply_chat_template(request['messages'],tokenize=False,add_generation_prompt=True,enable_thinking=False)
inputs=tok(prompt,return_tensors='pt',truncation=True,max_length=2048)
with torch.inference_mode():
 output=model.generate(**inputs,max_new_tokens=700,do_sample=False,pad_token_id=tok.eos_token_id)
print(tok.decode(output[0][inputs['input_ids'].shape[1]:],skip_special_tokens=True))
