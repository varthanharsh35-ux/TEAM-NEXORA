from pathlib import Path
import threading,time
GEOCODE_LOCK=threading.Lock();GEOCODE_CACHE={};GEOCODE_LAST=0.0
from typing import Literal
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ConfigDict, field_validator
from finance import calculate
import config

app=FastAPI(title='GramSahayak',version='2.0')
class FinanceInput(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    margin: float=Field(ge=0.01,le=100000000)
    start_date: date=Field(default_factory=date.today)
    @field_validator('margin',mode='before')
    @classmethod
    def numeric_margin(cls,value):
        if isinstance(value,bool):raise ValueError('invalid_margin')
        return value
    @field_validator('start_date')
    @classmethod
    def bounded_date(cls,value):
        if not 2000<=value.year<=2100:raise ValueError('invalid_date')
        return value
class ReportInput(FinanceInput):
    margin: float=Field(ge=0,le=100000000)
    person_name: str=Field(default='',max_length=100)
    business_name: str=Field(default='',max_length=120)
    funding_mode: Literal['legacy','savings','loan']='legacy'
    location: str=Field(min_length=2,max_length=200)
    business: str=Field(min_length=2,max_length=500)
    language: Literal['en','ta','hi']='en'
    radius: Literal[5,10,15]=15
    category: str='auto'
    scheme_id: Literal['auto','micro','term','nbcfdc']='auto'
    community: Literal['unspecified','sc','st','obc','general']='unspecified'
    facilities: list[Literal['space','power','three_phase','water','storage','cold','transport','equipment']]=Field(default_factory=list,max_length=8)
    gender: Literal['unspecified','female','male','other_gender']='unspecified'
    age: int | None=Field(default=None,ge=18,le=100)
    household_income: float | None=Field(default=None,ge=0,le=1000000000)
    district: str=''
    lat: float | None=Field(default=None,ge=8,le=13.7)
    lon: float | None=Field(default=None,ge=76,le=80.5)
@app.exception_handler(RequestValidationError)
async def invalid(request,exc):
    return JSONResponse(status_code=422,content={'error':'invalid_input','fields':[str(e['loc'][-1]) for e in exc.errors()]})
@app.get('/api/health')
def health():return {'status':'ok','version':'2.0'}
@app.post('/api/finance')
def finance(data:FinanceInput):
    try:return calculate(data.margin,data.start_date.isoformat())
    except ValueError as e:raise HTTPException(422,detail=str(e))

class ActualLoan(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    principal:float=Field(gt=0,le=100000000)
    rate:float=Field(ge=0,le=50)
    tenure:int=Field(ge=3,le=360)
    grace:int=Field(ge=0,le=36)
    start_date:date
@app.post('/api/loans/schedule')
def actual_loan(data:ActualLoan):
    if data.tenure%3 or data.grace%3 or data.grace>=data.tenure or not 2000<=data.start_date.year<=2100:raise HTTPException(422,detail='invalid_input')
    from finance import schedule_loan
    return schedule_loan(data.principal,data.rate/100,data.tenure,data.grace,data.start_date)
@app.post('/api/reports')
def report(data:ReportInput):
    from advisory import build_report
    return build_report(data.model_dump(mode='json'))
@app.post('/api/schemes')
def scheme_screen(data:ReportInput):
    from schemes import screen
    return screen(data.model_dump(mode='json'))

@app.get('/api/locations')
def locations(q:str='',district:str=''):
    from intelligence import search_locations
    return search_locations(q[:200],district)
@app.get('/api/coverage')
def coverage():
    from intelligence import coverage_data
    return coverage_data()

@app.get('/api/map/search')
def map_search(q:str):
    if not 2<=len(q.strip())<=200:raise HTTPException(422,detail='invalid_input')
    from geography import search
    return search(q.strip())

@app.get('/api/map/nearby')
def map_nearby(
    lat: float | None = None,
    lon: float | None = None,
    category: str | None = None,
    radius_km: float = 15,
    location_id: str | None = None,
    activity_id: str | None = None,
):
    import json
    import math
    from geography import nearby

    def fail(code, reason):
        raise HTTPException(422, detail={
            'error': code,
            'message_key': f'errors.{code}',
            'status': 'unresolved',
            'detail': {'reason': reason},
            'candidates': [],
        })

    if activity_id and category and activity_id != category:
        fail('invalid_input', 'conflicting_activity_parameters')
    if location_id is not None:
        if lat is not None or lon is not None:
            fail('invalid_input', 'use_location_id_or_coordinates')
        # Resolve only coordinate-bearing registry rows. Task 1.1 supplies them;
        # missing coordinates must never acquire an invented district centroid.
        root = Path(__file__).resolve().parents[1] / 'data'
        location = None
        for filename in ('villages.json', 'blocks.json', 'districts.json'):
            try:
                rows = json.loads((root / filename).read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            location = next((row for row in rows if row.get('id') == location_id), None)
            if location is not None:
                break
        if location is None or location.get('lat') is None or location.get('lon') is None:
            fail('location_unresolved', 'location_coordinates_unavailable')
        try:
            lat = float(location['lat'])
            lon = float(location['lon'])
        except (TypeError, ValueError):
            fail('location_unresolved', 'location_coordinates_invalid')
    if lat is None or lon is None:
        fail('invalid_input', 'location_id_or_coordinate_pair_required')
    if not math.isfinite(lat) or not math.isfinite(lon):
        fail('invalid_input', 'non_finite_coordinates')
    if not (8 <= lat <= 13.7 and 76 <= lon <= 80.5):
        fail('outside_coverage', 'coordinates_outside_supported_bounds')
    return nearby(lat, lon, activity_id or category or 'other', radius_km=radius_km)

@app.get('/api/map/cached')
def cached_places(lat:float,lon:float,category:str='other'):
    from geography import cached
    row=cached(f'nearby:{lat:.4f}:{lon:.4f}:{category}')
    return {**row[0],'cached':True} if row else None

@app.get('/api/geocode')
def geocode(lat:float,lon:float):
    global GEOCODE_LAST
    import httpx
    if not (8<=lat<=13.7 and 76<=lon<=80.5):raise HTTPException(422,detail='outside_state')
    key=(round(lat,4),round(lon,4))
    with GEOCODE_LOCK:
        if key in GEOCODE_CACHE:return GEOCODE_CACHE[key]
        if time.monotonic()-GEOCODE_LAST<1:raise HTTPException(429,detail='map_failed')
        GEOCODE_LAST=time.monotonic()
    try:
        with httpx.Client(timeout=8) as c:
            response=c.get('https://nominatim.openstreetmap.org/reverse',params={'lat':lat,'lon':lon,'format':'jsonv2','accept-language':'en'},headers={'User-Agent':'GramSahayak-SIH26091-prototype/2.0'})
            response.raise_for_status();data=response.json()
        address=data.get('address',{})
        if address.get('state')!='Tamil Nadu':raise HTTPException(422,detail='outside_state')
        from intelligence import district_of
        label=data.get('display_name','');district=district_of(label)
        result={'location':label[:200],'district':district['id'] if district else ''}
        with GEOCODE_LOCK:
            if len(GEOCODE_CACHE)>=500:GEOCODE_CACHE.pop(next(iter(GEOCODE_CACHE)))
            GEOCODE_CACHE[key]=result
        return result
    except HTTPException:raise
    except Exception:raise HTTPException(503,detail='map_failed')
@app.get('/api/reports/{report_id}')
def saved_report(report_id:str):
    from advisory import read_report
    result=read_report(report_id)
    if result is None:raise HTTPException(404,detail='report_missing')
    return result

@app.post('/api/reports/{report_id}/advice/{language}')
def advice(report_id:str,language:Literal['en','ta','hi']):
    from llm import queue
    result=queue(report_id,language)
    if result is None:raise HTTPException(404,detail='report_missing')
    return result

from accounts import router as account_router
app.include_router(account_router)

dist=Path(__file__).resolve().parents[1]/'frontend'/'dist'
if dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount('/',StaticFiles(directory=dist,html=True),name='website')
