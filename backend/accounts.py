"""Local demo accounts. Passwords and session tokens are never stored in plaintext."""
import hashlib,hmac,json,re,secrets,sqlite3,time,threading
from contextlib import contextmanager
from pathlib import Path
from fastapi import APIRouter,HTTPException,Request,Response
from pydantic import BaseModel,Field,ConfigDict,field_validator
from typing import Literal
import os
from storage import database_path
DB=database_path('accounts.sqlite3')
router=APIRouter(prefix='/api/account');LOCK=threading.Lock();ATTEMPTS={}
@contextmanager
def db():
 c=sqlite3.connect(DB,timeout=15);c.row_factory=sqlite3.Row
 try:
  with c:
   c.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY,email TEXT UNIQUE,salt TEXT,password TEXT,recovery TEXT,state TEXT DEFAULT '{}')")
   c.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY,user_id TEXT,expires REAL)')
   yield c
 finally:c.close()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def password_hash(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),310000).hex()
def origin_check(request):
 origin=request.headers.get('origin')
 allowed={str(request.base_url).rstrip('/')}
 allowed.update(value.strip().rstrip('/') for value in os.getenv('ALLOWED_ORIGINS','').split(',') if value.strip())
 if os.getenv('APP_ENV') != 'production':allowed.update({'http://localhost:5173','http://127.0.0.1:5173'})
 if origin and origin not in allowed:raise HTTPException(403,detail='account_denied')
def throttle(request):
 origin_check(request);key=request.client.host if request.client else 'local';now=time.monotonic()
 with LOCK:
  ATTEMPTS[key]=[t for t in ATTEMPTS.get(key,[]) if now-t<60]
  if len(ATTEMPTS[key])>=12:raise HTTPException(429,detail='account_wait')
  ATTEMPTS[key].append(now)
def user(request):
 token=request.cookies.get('gs_session','')
 if not token:raise HTTPException(401,detail='account_login_needed')
 with db() as c:
  row=c.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.token=? AND sessions.expires>?',(digest(token),time.time())).fetchone()
 if not row:raise HTTPException(401,detail='account_login_needed')
 return dict(row)
def session(response,uid):
 token=secrets.token_urlsafe(32)
 with db() as c:
  c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),));c.execute('INSERT INTO sessions VALUES (?,?,?)',(digest(token),uid,time.time()+604800))
 response.set_cookie('gs_session',token,max_age=604800,httponly=True,samesite='strict',secure=os.getenv('APP_ENV')=='production',path='/')
class Credentials(BaseModel):
 model_config=ConfigDict(extra='forbid')
 email:str=Field(min_length=5,max_length=254)
 password:str=Field(min_length=10,max_length=128)
 gender:Literal['unspecified','female','male','other_gender']='unspecified'
 community:Literal['unspecified','sc','st','obc','general']='unspecified'
 @field_validator('email')
 @classmethod
 def email_format(cls,v):
  v=v.strip().lower()
  if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',v):raise ValueError('invalid_email')
  return v
class Reset(Credentials):recovery:str=Field(min_length=20,max_length=120)
class Workspace(BaseModel):
 model_config=ConfigDict(extra='forbid')
 profile:dict=Field(default_factory=dict)
 report:dict|None=None
 entries:list[dict]=Field(default_factory=list,max_length=10000)
 plans:list[dict]=Field(default_factory=list,max_length=20)
 history:list[dict]=Field(default_factory=list,max_length=20)
 loans:list[dict]=Field(default_factory=list,max_length=30)
@router.get('/session')
def current(request:Request):
 try:u=user(request);return {'email':u['email']}
 except HTTPException:return {'email':None}
@router.post('/register')
def register(data:Credentials,request:Request,response:Response):
 throttle(request);uid=secrets.token_hex(16);salt=secrets.token_hex(16);recovery=secrets.token_urlsafe(24)
 try:
  with db() as c:c.execute('INSERT INTO users(id,email,salt,password,recovery,state) VALUES (?,?,?,?,?,?)',(uid,data.email,salt,password_hash(data.password,salt),digest(recovery),json.dumps({'profile':{'gender':data.gender,'community':data.community}} if data.gender!='unspecified' or data.community!='unspecified' else {})))
 except sqlite3.IntegrityError:raise HTTPException(409,detail='account_exists')
 session(response,uid);return {'email':data.email,'recovery':recovery}
@router.post('/login')
def login(data:Credentials,request:Request,response:Response):
 throttle(request)
 with db() as c:row=c.execute('SELECT * FROM users WHERE email=?',(data.email,)).fetchone()
 salt=row['salt'] if row else '00'*16;check=password_hash(data.password,salt)
 if not row or not hmac.compare_digest(check,row['password']):raise HTTPException(401,detail='account_invalid')
 session(response,row['id']);return {'email':row['email']}
@router.post('/logout')
def logout(request:Request,response:Response):
 origin_check(request)
 with db() as c:c.execute('DELETE FROM sessions WHERE token=?',(digest(request.cookies.get('gs_session','')),))
 response.delete_cookie('gs_session',path='/');return {'ok':True}
@router.post('/reset')
def reset(data:Reset,request:Request):
 throttle(request)
 with db() as c:
  row=c.execute('SELECT * FROM users WHERE email=?',(data.email,)).fetchone()
  if not row or not hmac.compare_digest(row['recovery'],digest(data.recovery.strip())):raise HTTPException(401,detail='account_invalid')
  salt=secrets.token_hex(16);recovery=secrets.token_urlsafe(24)
  c.execute('UPDATE users SET salt=?,password=?,recovery=? WHERE id=?',(salt,password_hash(data.password,salt),digest(recovery),row['id']));c.execute('DELETE FROM sessions WHERE user_id=?',(row['id'],))
 return {'recovery':recovery}
@router.get('/workspace')
def workspace(request:Request):return json.loads(user(request)['state'])
@router.post('/workspace')
def save_workspace(data:Workspace,request:Request):
 origin_check(request);u=user(request);body=data.model_dump_json()
 if len(body.encode())>1000000:raise HTTPException(413,detail='account_too_large')
 with db() as c:c.execute('UPDATE users SET state=? WHERE id=?',(body,u['id']))
 return {'ok':True}
