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
    scheme_id: str='auto'
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

@app.get('/api/sectors')
def sectors(lang: Literal['en','ta','hi']='en'):
    """Sector -> activity taxonomy for the guided business-selection dropdown.
    Replaces the free-text business box (docs/TASKS.md Task 3.1)."""
    import json
    data=json.loads((Path(__file__).resolve().parents[1]/'data'/'taxonomy.json').read_text(encoding='utf8'))
    def localize(names):return names.get(lang) or names.get('en') or next(iter(names.values()),'')
    return {
        'version':data.get('version'),
        'sectors':[{
            'id':s['id'],'name':localize(s['names']),'emoji':s.get('emoji',''),
            'activities':[{
                'id':a['id'],'name':localize(a['names']),'unit':a.get('unit'),
                'typical_project_cost':a.get('typical_project_cost'),
                'questions':a.get('questions',[]),
                'required_facilities':a.get('required_facilities',[]),
                'licences':a.get('licences',[]),
            } for a in s.get('activities',[])],
        } for s in data.get('sectors',[])],
    }

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


# --- Task 2.9: statement upload routes ---

from fastapi import UploadFile, File

@app.post('/api/statements/upload')
async def upload_statement(file: UploadFile = File(...), owner: str = 'anonymous'):
    from statements import create_batch
    content = await file.read()
    if not content:
        raise HTTPException(422, detail='file_empty')
    batch = create_batch(owner, file.filename, content, file.content_type)
    return batch

@app.get('/api/statements/batches')
def list_statement_batches(owner: str = 'anonymous'):
    from statements import list_batches
    return {'batches': list_batches(owner)}

@app.get('/api/statements/batches/{batch_id}')
def get_statement_batch(batch_id: str, owner: str = 'anonymous'):
    from statements import get_batch
    batch = get_batch(owner, batch_id)
    if batch is None:
        raise HTTPException(404, detail='batch_not_found')
    return batch

class DraftUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    included: bool | None = None
    direction: Literal['in', 'out'] | None = None
    category: str | None = None
    amount: float | None = None
    entry_date: str | None = None

@app.patch('/api/statements/drafts/{draft_id}')
def patch_draft(draft_id: str, data: DraftUpdate, owner: str = 'anonymous'):
    from statements import update_draft
    try:
        result = update_draft(
            owner, draft_id,
            included=data.included,
            direction=data.direction,
            category=data.category,
            amount=data.amount,
            entry_date=data.entry_date,
        )
    except ValueError as e:
        raise HTTPException(422, detail=str(e))
    if result is None:
        raise HTTPException(404, detail='draft_not_found')
    return result

@app.post('/api/statements/batches/{batch_id}/confirm')
def confirm_statement_batch(batch_id: str, owner: str = 'anonymous'):
    from statements import confirm_batch
    try:
        result = confirm_batch(owner, batch_id)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))
    if result is None:
        raise HTTPException(404, detail='batch_not_found')
    return result

@app.post('/api/statements/batches/{batch_id}/discard')
def discard_statement_batch(batch_id: str, owner: str = 'anonymous'):
    from statements import discard_batch
    try:
        result = discard_batch(owner, batch_id)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))
    if not result:
        raise HTTPException(404, detail='batch_not_found')
    return {'status': 'discarded', 'batch_id': batch_id}


# --- Task 3.5: inventory plan route ---

class InventoryInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    activity_id: str = Field(min_length=1, max_length=100)
    facilities_owned: list[str] = Field(default_factory=list, max_length=20)
    quantity_overrides: dict[str, int] = Field(default_factory=dict)

@app.post('/api/inventory/plan')
def inventory_plan(data: InventoryInput):
    from inventory import plan
    try:
        return plan(
            data.activity_id,
            facilities_owned=data.facilities_owned,
            quantity_overrides=data.quantity_overrides,
        )
    except Exception as e:
        raise HTTPException(422, detail=str(e))


# --- Task 3.6: split finance into overview / allocation / repayment ---

class FinanceOverviewInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    margin: float = Field(ge=0.01, le=100000000)
    start_date: date = Field(default_factory=date.today)
    scheme_id: str = 'auto'
    project_cost: float | None = Field(default=None, ge=0, le=100000000)
    activity_id: str | None = None

class FinanceAllocationInput(FinanceOverviewInput):
    facilities_owned: list[str] = Field(default_factory=list, max_length=20)

@app.post('/api/finance/overview')
def finance_overview(data: FinanceOverviewInput):
    from finance_views import overview
    try:
        return overview(
            data.margin, data.start_date.isoformat(),
            data.scheme_id, data.project_cost, data.activity_id,
        )
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

@app.post('/api/finance/allocation')
def finance_allocation(data: FinanceAllocationInput):
    from finance_views import allocation
    try:
        return allocation(
            data.margin, data.start_date.isoformat(),
            data.scheme_id, data.project_cost,
            data.activity_id, data.facilities_owned,
        )
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

@app.post('/api/finance/repayment')
def finance_repayment(data: FinanceOverviewInput):
    from finance_views import repayment
    try:
        return repayment(
            data.margin, data.start_date.isoformat(),
            data.scheme_id, data.project_cost,
        )
    except ValueError as e:
        raise HTTPException(422, detail=str(e))


# --- Seasonality Engine ---

@app.get('/api/seasonality/{activity_id}')
def get_seasonality(activity_id: str, district: str | None = None):
    from seasonality import monthly_index, district_climate
    try:
        return {
            "activity_id": activity_id,
            "district": district,
            "climate": district_climate(district) if district else None,
            "monthly_index": monthly_index(activity_id, district)
        }
    except Exception as e:
        raise HTTPException(422, detail=str(e))


# --- Pricing Strategy Engine ---

class PricingStrategyInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    activity_id: str
    demand_score: int = Field(ge=0, le=100)
    competitor_count: int = Field(ge=0)
    competitor_within_1km: int = Field(ge=0)
    project_cost: float = Field(gt=0)
    loan: float = Field(ge=0)
    quarterly_payment: float = Field(ge=0)
    capacity_units_per_month: float = Field(gt=0)
    unit_label: str = Field(default="unit")
    sector_price_band: dict

@app.post('/api/pricing/strategy')
def post_pricing_strategy(data: PricingStrategyInput):
    from pricing import strategy as calc_strategy
    try:
        return calc_strategy(
            activity_id=data.activity_id,
            demand_score=data.demand_score,
            competitor_count=data.competitor_count,
            competitor_within_1km=data.competitor_within_1km,
            project_cost=data.project_cost,
            loan=data.loan,
            quarterly_payment=data.quarterly_payment,
            capacity_units_per_month=data.capacity_units_per_month,
            unit_label=data.unit_label,
            sector_price_band=data.sector_price_band
        )
    except Exception as e:
        raise HTTPException(422, detail=str(e))


# --- Alternatives Engine ---

class BetterActivitiesInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    location_id: str = Field(default="")
    lat: float
    lon: float
    chosen_activity_id: str
    chosen_demand_score: int = Field(ge=0, le=100)
    margin: float = Field(ge=0)
    radius_km: float = 10.0
    top_n: int = 3

class BetterLocationsInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chosen_activity_id: str
    chosen_lat: float
    chosen_lon: float
    chosen_demand_score: int = Field(ge=0, le=100)
    radius_km: float = 25.0
    top_n: int = 3

@app.post('/api/alternatives/activities')
def post_better_activities(data: BetterActivitiesInput):
    from alternatives import better_activities
    try:
        return better_activities(
            location_id=data.location_id,
            lat=data.lat,
            lon=data.lon,
            chosen_activity_id=data.chosen_activity_id,
            chosen_demand_score=data.chosen_demand_score,
            margin=data.margin,
            radius_km=data.radius_km,
            top_n=data.top_n
        )
    except Exception as e:
        raise HTTPException(422, detail=str(e))

@app.post('/api/alternatives/locations')
def post_better_locations(data: BetterLocationsInput):
    from alternatives import better_locations
    try:
        return better_locations(
            chosen_activity_id=data.chosen_activity_id,
            chosen_lat=data.chosen_lat,
            chosen_lon=data.chosen_lon,
            chosen_demand_score=data.chosen_demand_score,
            radius_km=data.radius_km,
            top_n=data.top_n
        )
    except Exception as e:
        raise HTTPException(422, detail=str(e))


# --- Cash Flow Tracker ---

class TrackerEntryInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: str
    kind: Literal['income', 'expense']
    category: str
    amount: float = Field(gt=0)
    note: str = ""

@app.post('/api/tracker/entries')
def post_tracker_entry(data: TrackerEntryInput, user_id: str = 'anonymous'):
    from tracker import add_entry
    try:
        return add_entry(user_id, data.date, data.kind, data.category, data.amount, data.note)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

@app.delete('/api/tracker/entries/{entry_id}')
def delete_tracker_entry(entry_id: str, user_id: str = 'anonymous'):
    from tracker import delete_entry
    deleted = delete_entry(user_id, entry_id)
    if not deleted:
        raise HTTPException(404, detail="entry_not_found")
    return {"status": "deleted", "entry_id": entry_id}

@app.get('/api/tracker/summary')
def get_tracker_summary(user_id: str = 'anonymous', from_date: str | None = None, to_date: str | None = None):
    from tracker import summary
    try:
        return summary(user_id, from_date, to_date)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

class LoanPlanInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scheme_id: str
    sanctioned: float = Field(gt=0)
    schedule: list
    disbursement_date: str

@app.post('/api/tracker/loan_plan')
def post_loan_plan(data: LoanPlanInput, user_id: str = 'anonymous'):
    from tracker import save_loan_plan
    try:
        return save_loan_plan(user_id, data.scheme_id, data.sanctioned, data.schedule, data.disbursement_date)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

@app.get('/api/tracker/loan_status')
def get_tracker_loan_status(user_id: str = 'anonymous'):
    from tracker import get_loan_status
    status = get_loan_status(user_id)
    return status or {}


# --- Debt Portfolio Engine ---

class DebtLoanInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lender: str
    facility_type: Literal['term_loan', 'mudra', 'overdraft', 'cc', 'informal']
    status: Literal['active', 'closed', 'npa'] = 'active'
    principal: float = Field(gt=0)
    annual_rate: float = Field(ge=0)
    tenure_months: int = Field(gt=0)
    disbursement_date: str
    grace_months: int = Field(default=0, ge=0)

@app.post('/api/debt/loans')
def post_debt_loan(data: DebtLoanInput, user_id: str = 'anonymous'):
    from debt import add_loan
    try:
        return add_loan(
            user_id, data.lender, data.facility_type, data.status,
            data.principal, data.annual_rate, data.tenure_months,
            data.disbursement_date, data.grace_months
        )
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

@app.get('/api/debt/loans')
def get_debt_loans(user_id: str = 'anonymous'):
    from debt import list_loans
    return list_loans(user_id)

@app.post('/api/debt/loans/{loan_id}/close')
def post_close_debt_loan(loan_id: str, user_id: str = 'anonymous'):
    from debt import close_loan
    closed = close_loan(user_id, loan_id)
    if not closed:
        raise HTTPException(404, detail="loan_not_found")
    return {"status": "closed", "loan_id": loan_id}


# --- Data Freshness & Pipeline Ingest ---

@app.get('/api/freshness')
def get_freshness():
    from ingest.cli import status as get_ingest_status
    records = get_ingest_status()
    return {
        "status": "ok",
        "datasets": records,
        "as_of": date.today().isoformat()
    }

from accounts import router as account_router
app.include_router(account_router)

dist=Path(__file__).resolve().parents[1]/'frontend'/'dist'
if dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount('/',StaticFiles(directory=dist,html=True),name='website')
