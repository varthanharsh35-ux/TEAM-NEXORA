import {useState,useEffect,useRef,lazy,Suspense} from 'react';
import {useTranslation} from 'react-i18next';
import {Sprout,MapPin,ArrowRight,ArrowLeft,Wallet,FileText,Calculator,BookOpen,Printer,Download,Check,Info,AlertTriangle,ChevronDown,Mic,RefreshCw,Users,Store,ShieldCheck,Landmark,TrendingUp,GitCompare,Database} from 'lucide-react';
import Account from './Account';
import Nearby from './Nearby';
import Schemes from './Schemes';
import Tracker,{saveRepaymentPlan} from './Tracker';
import {Facilities} from './Profile';
import History from './History';
import Compare from './Compare';
import NavHelper from './NavHelper';
import {api,restore,persist} from './api';
const categories=['dairy','retail','food','tailoring','agriculture','poultry','fish','repair','craft','manufacturing','transport','services','other'];
const sourceLinks=[['source_directory','https://www.tnrd.tn.gov.in/databases/Villages.pdf'],['source_districts','https://lokbhavan.tn.gov.in/districts-of-tamil-nadu/'],['source_nabard','https://www.nabard.org/auth/writereaddata/tender/pub_0602250348211363.pdf'],['source_scheme','https://nsfdc.nic.in/faqs']];
const initial={person_name:'',business_name:'',funding_mode:'savings',location:'',business:'',margin:'100000',radius:15,category:'auto',district:'',community:'unspecified',facilities:[],scheme_id:'auto',gender:'unspecified',age:null,household_income:null,start_date:new Date().toLocaleDateString('en-CA')};
const LocationMap=lazy(()=>import('./LocationMap'));
function today(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
initial.start_date=today();
function Icon({as:Component,...props}){return <Component aria-hidden="true" size={20} strokeWidth={1.8} {...props}/>}
function Notice({children,danger=false}){return <div className={`notice ${danger?'warning':''}`}><Icon as={danger?AlertTriangle:Info}/><div>{children}</div></div>}
function Section({icon,title,children,className=''}){return <section className={`panel ${className}`}><h2><Icon as={icon}/>{title}</h2>{children}</section>}
function Metric({label,value,detail,accent=false}){return <div className={`metric ${accent?'accent':''}`}><span>{label}</span><strong>{value}</strong>{detail&&<small>{detail}</small>}</div>}
export default function App(){
 const {t,i18n}=useTranslation();const lang=i18n.language;
 const [form,setForm]=useState(()=>({...initial,...restore('gs-draft',{}),radius:15}));
 const [report,setReport]=useState(()=>{const r=restore('gs-report',null);return r?.version===2?r:null});
 const [editing,setEditing]=useState(false),[tab,setTab]=useState('plan'),[error,setError]=useState(''),[busy,setBusy]=useState(false),[coverage,setCoverage]=useState(null),[online,setOnline]=useState(false),[suggestions,setSuggestions]=useState([]),[voice,setVoice]=useState(false),[storageError,setStorageError]=useState(false);
 const [history,setHistory]=useState(()=>restore('gs-history',[]));const [showMap,setShowMap]=useState(false);const [stage,setStage]=useState('welcome');
 const seq=useRef(0),aborter=useRef(null),timer=useRef(null),recognizer=useRef(null),reportHeading=useRef(null);
 const n=(v,dec=0)=>new Intl.NumberFormat(`${lang}-IN`,{maximumFractionDigits:dec}).format(v);
 const money=(v)=>new Intl.NumberFormat(`${lang}-IN`,{style:'currency',currency:'INR',maximumFractionDigits:2}).format(v);
 const date=(d)=>new Intl.DateTimeFormat(`${lang}-IN`,{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${d.slice(0,10)}T12:00:00`));
 const snapshot=()=>({profile:form,report,entries:restore('gs-entries',[]),plans:restore('gs-repayment-plans',[]),history,loans:restore('gs-loans',[])});
 const loadWorkspace=state=>{seq.current++;aborter.current?.abort();clearTimeout(timer.current);setBusy(false);const next={...initial,...state.profile};setForm(next);setReport(state.report?.version===2?state.report:null);setHistory(state.history||[]);persist('gs-history',state.history||[]);persist('gs-loans',state.loans||[]);setEditing(false);setError('');persist('gs-draft',next);persist('gs-report',state.report||null);persist('gs-entries',state.entries||[]);persist('gs-repayment-plans',state.plans||[])};
 const change=(k,v)=>setForm(f=>({...f,[k]:v}));
 useEffect(()=>{if(!persist('gs-draft',form))setStorageError(true)},[form]);
 useEffect(()=>{const open=()=>document.querySelectorAll('details.print-open').forEach(d=>d.open=true);window.addEventListener('beforeprint',open);return()=>window.removeEventListener('beforeprint',open)},[]);
 useEffect(()=>{api('/coverage').then(setCoverage).catch(()=>{});api('/health').then(()=>setOnline(true)).catch(()=>setOnline(false));return()=>{aborter.current?.abort();clearTimeout(timer.current);recognizer.current?.abort()}},[]);
 useEffect(()=>{const on=()=>api('/health').then(()=>setOnline(true)).catch(()=>setOnline(false));window.addEventListener('online',on);window.addEventListener('offline',on);return()=>{window.removeEventListener('online',on);window.removeEventListener('offline',on)}},[]);
 useEffect(()=>{
  if(form.location.trim().length<3){setSuggestions([]);return}
  const ctrl=new AbortController(),id=setTimeout(()=>api(`/locations?q=${encodeURIComponent(form.location)}&district=${encodeURIComponent(form.district)}`,undefined,ctrl.signal).then(setSuggestions).catch(()=>{}),350);
  return()=>{clearTimeout(id);ctrl.abort()};
 },[form.location,form.district]);
 // Generation is non-blocking. Each language retains its own advice; fallback is instant.
 useEffect(()=>{
  if(!report?.id||!online)return;
  let stopped=false,poll;
  const id=report.id;
  const update=r=>{if(!stopped){setReport(prev=>prev?.id===id?r:prev);persist('gs-report',r)}};
  api(`/reports/${id}/advice/${lang}`,{}).then(r=>{update(r);if(r.ai_status?.[lang]?.state!=='done'){
   const started=Date.now();poll=setInterval(()=>{if(Date.now()-started>600000){clearInterval(poll);return}api(`/reports/${id}`).then(v=>{update(v);if(v.ai_status?.[lang]?.state==='done')clearInterval(poll)}).catch(()=>clearInterval(poll))},4000);
  }}).catch(()=>{});
  return()=>{stopped=true;clearInterval(poll)};
 },[report?.id,lang,online]);
 const run=async(data=form,focus=true)=>{
  setError('');if(!data.location.trim()||!data.business.trim()||!Number.isFinite(Number(data.margin))||Number(data.margin)<0||Number(data.margin)>100000000||!data.start_date){setError('invalid_input');return}
  const current=++seq.current;aborter.current?.abort();aborter.current=new AbortController();setBusy(true);
  try{
   if(data.lat==null){try{const found=await api(`/map/search?q=${encodeURIComponent(data.location)}`,undefined,aborter.current.signal);if(found.items.length===1){const {lat,lon,district,location}=found.items[0];data={...data,lat,lon,district,location}}}catch{}}
   const r=await api('/reports',{...data,margin:Number(data.margin),radius:15,language:lang},aborter.current.signal);
   if(current!==seq.current)return;setReport(r);setForm({...r.input,margin:String(r.input.margin)});setEditing(false);setOnline(true);if(!persist('gs-report',r))setStorageError(true);const saved=[r,...restore('gs-history',[]).filter(x=>x.id!==r.id)].slice(0,20);setHistory(saved);persist('gs-history',saved);api('/account/workspace',{...snapshot(),profile:r.input,report:r,history:saved}).catch(()=>{});
   if(focus){setTab('plan');setTimeout(()=>reportHeading.current?.focus(),0)}
  }catch(e){if(current===seq.current){setError(e.message);if(e.message==='server_error')setOnline(false)}}
  finally{if(current===seq.current)setBusy(false)}
 };
 const example=()=>setForm({...initial,location:t('example_location'),business:'dairy',category:'dairy',district:'Madurai',margin:'100000'});
 const clear=()=>{seq.current++;aborter.current?.abort();clearTimeout(timer.current);setBusy(false);setReport(null);setEditing(false);setForm({...initial});setError('');setTab('plan');persist('gs-report',null)};
 const openHistory=r=>{seq.current++;aborter.current?.abort();setBusy(false);setReport(r);setForm({...r.input,margin:String(r.input.margin)});persist('gs-report',r);setEditing(false);setTab('plan')};
 const print=()=>{document.querySelectorAll('details.print-open').forEach(d=>d.open=true);window.print()};
 const download=()=>{
  const fields=['month','due_date','opening','interest','principal','payment','balance'];
  const lines=[fields.map(x=>t(x)),...report.finance.schedule.map(r=>fields.map(k=>k==='due_date'?date(r[k]):n(r[k],2)))];
  const csv='\ufeff'+lines.map(row=>row.map(v=>`"${String(v).replaceAll('"','""')}"`).join(',')).join('\r\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`${t('brand')}-${t('schedule')}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 const f=report?.finance,m=report?.metrics;
 const ai=report?.ai_status?.[lang],advice=report?.advice?.[lang];
 const text=key=>advice?.[key]||t(`advice.${key}`);
 const showForm=!report||editing;
 const errKey=['invalid_input','clarify','ambiguous','outside_state','server_error','voice_error','report_missing','scheme_project_limit'].includes(error)?error:'invalid_input';
 return <>
  <a className="skip-link" href="#main">{t('skip')}</a>
  <div className="masthead"><div><span>{t('prototype')}</span><span>{t('not_government')}</span></div></div>
  <header className="header"><div className="header-inner"><a href="#" className="brand" onClick={e=>{e.preventDefault();setTab('plan')}}><span className="brand-icon"><Icon as={Sprout} size={28}/></span><span><b>{t('brand')}</b><small>{t('tagline')}</small></span></a>
   <nav hidden={stage!=='app'} aria-label={t('nav_plan')}>{[['plan',FileText],['finance',Calculator],['sources',BookOpen],['profile',Users],['schemes',Landmark],['allocation',Wallet],['repayment',Calculator],['tracker',BookOpen],['compare',GitCompare],['account',ShieldCheck]].map(([key,icon])=><button key={key} className={tab===key?'active':''} onClick={()=>setTab(key)}><Icon as={icon}/>{t(`nav_${key}`)}</button>)}</nav>
   <div className="languages" role="group" aria-label={t('language')}>{[['en','english'],['ta','tamil'],['hi','hindi']].map(([code,label])=><button key={code} lang={code} aria-pressed={lang===code} onClick={()=>i18n.changeLanguage(code)}>{t(label)}</button>)}</div>
  </div></header>
  <main id="main" className="main">
   {stage==='welcome'&&<section className="panel welcome"><div className="eyebrow">{t('brand')}</div><h1>{t('headline')}</h1><p>{t('welcome_intro')}</p><div className="report-grid">{['benefit_market','benefit_finance','benefit_action'].map(k=><article key={k}><h2>{t(k)}</h2><p>{t(`${k}_desc`)}</p></article>)}</div><button className="primary" onClick={()=>{setStage('app');setTab('account')}}>{t('get_started')}<Icon as={ArrowRight}/></button></section>}{stage==='app'&&<>
   {tab==='account'&&<Account snapshot={snapshot} onLoad={loadWorkspace} onContinue={()=>{setTab('plan');setEditing(true);}}/>}
   {tab==='schemes'&&<Schemes form={report?.input||form} onProfile={()=>{setTab('plan');setEditing(true)}} onUse={async id=>{await run({...report?.input||form,scheme_id:id},false);setTab('finance')}}/>}
   {tab==='tracker'&&<Tracker/>}
   {tab==='compare'&&<Compare report={report} history={history}/>}
   {tab==='profile'&&<History history={history} onOpen={openHistory}/>}
   {storageError&&<Notice danger>{t('storage_error')}</Notice>}
   {error&&<div role="alert"><Notice danger>{t(errKey)}</Notice></div>}
   {report&&!online&&<Notice>{t('cached')}</Notice>}
   {tab==='plan'&&showForm&&<>
    <div className="intro"><div className="eyebrow">{t('eyebrow')}</div><h1>{t('headline')}</h1><p>{t('intro')}</p></div>
    <div className="intake-grid"><form className="intake panel" onSubmit={e=>{e.preventDefault();run()}} noValidate>
     <div className="panel-heading"><span className="step-number">01</span><div><h2>{t('new_plan')}</h2><p>{t('required_hint')}</p></div></div>
     <label htmlFor="person-name">{t('person_name')}</label><input id="person-name" maxLength={100} autoComplete="name" value={form.person_name||''} onChange={e=>change('person_name',e.target.value)}/><label htmlFor="business-name">{t('business_name')}</label><input id="business-name" maxLength={120} value={form.business_name||''} onChange={e=>change('business_name',e.target.value)}/><label htmlFor="location"><Icon as={MapPin}/>{t('location')}</label>
     <input id="location" autoComplete="off" maxLength={200} list="places" value={form.location} onChange={e=>setForm(f=>({...f,location:e.target.value,district:'',lat:null,lon:null}))} placeholder={t('location_placeholder')} aria-describedby="location-help"/>
     <datalist id="places">{suggestions.map((s,i)=><option key={`${s.id||s.name}-${i}`} value={`${s.name}, ${s.district}`}/>)}</datalist>
     <small id="location-help" className="field-hint">{t('location_hint')}</small>
     <button type="button" className="map-toggle" onClick={()=>setShowMap(v=>!v)} aria-expanded={showMap}><Icon as={MapPin}/>{t('map_label')}</button>
     {showMap&&<Suspense fallback={<p>{t('map_loading')}</p>}><LocationMap radius={15} value={form} onChoose={({location,district,lat,lon})=>setForm(f=>({...f,location,district,lat,lon}))}/></Suspense>}
     <label htmlFor="business"><Icon as={Store}/>{t('business')}</label>
     <select id="business" value={form.category==='auto'?'':form.category} onChange={e=>setForm(f=>({...f,category:e.target.value,business:e.target.value}))} aria-describedby="business-help"><option value="">{t('choose_business')}</option>{categories.map(c=><option key={c} value={c}>{t(`sector.${c}`)}</option>)}</select>
     <small id="business-help" className="field-hint">{t('business_select_hint')}</small>
     <fieldset className="funding-choice"><legend>{t('funding_choice')}</legend>{['savings','loan'].map(k=><label key={k}><input type="radio" name="funding" value={k} checked={form.funding_mode===k} onChange={()=>change('funding_mode',k)}/>{t(`funding_${k}`)}</label>)}</fieldset><label htmlFor="margin"><Icon as={Wallet}/>{t(form.funding_mode==='loan'?'own_contribution':'savings_amount')}</label><div className="currency-input"><span aria-hidden="true">₹</span><input id="margin" inputMode="decimal" type="number" min="0" max="100000000" step="0.01" value={form.margin} onChange={e=>change('margin',e.target.value)} aria-describedby="margin-help"/></div>
     <small id="margin-help" className="field-hint">{t('margin_hint')}</small>
     <details className="options"><summary>{t('more_options')}<Icon as={ChevronDown}/></summary><div className="form-grid">
      <div><label htmlFor="district">{t('district')}</label><select id="district" value={form.district} onChange={e=>change('district',e.target.value)}><option value="">{t('choose_district')}</option>{coverage?.district_list.map(d=><option key={d.id} value={d.id}>{d.names[lang]}</option>)}</select></div>

      <div><label htmlFor="community">{t('community')}</label><select id="community" value={form.community} onChange={e=>change('community',e.target.value)}>{['unspecified','sc','st','obc','general'].map(c=><option key={c} value={c}>{t(c)}</option>)}</select></div>
      <div><label htmlFor="start-date">{t('start_date')}</label><input id="start-date" type="date" value={form.start_date} onChange={e=>change('start_date',e.target.value)}/></div>
     <div><label htmlFor="intake-gender">{t('gender')}</label><select id="intake-gender" value={form.gender} onChange={e=>change('gender',e.target.value)}>{['unspecified','female','male','other_gender'].map(k=><option key={k} value={k}>{t(k)}</option>)}</select></div><div><label htmlFor="intake-income">{t('household_income')}</label><input id="intake-income" type="number" min="0" value={form.household_income??''} onChange={e=>change('household_income',e.target.value===''?null:Number(e.target.value))}/></div></div></details><Facilities form={form} change={change}/>
     {editing&&<small className="field-hint">{t('edit_hint')}</small>}
     <button className="primary submit" type="submit" disabled={busy}>{busy?<Icon as={RefreshCw} className="spin"/>:<Icon as={FileText}/>}<span>{t(busy?'loading':'generate')}</span><Icon as={ArrowRight}/></button>
     <button type="button" className="example" onClick={example}>{t('example')}</button><p className="privacy">{t('privacy')}</p>
    </form><aside className="intake-aside"><div className="coverage-pill"><Icon as={ShieldCheck}/>{t('coverage_badge')}</div><h2>{t('what_you_get')}</h2>{[['benefit_market',MapPin],['benefit_finance',Calculator],['benefit_action',TrendingUp]].map(([key,icon],index)=><div className="benefit" key={key}><div className="benefit-icon"><Icon as={icon} size={25}/></div><div><small>0{index+1}</small><h3>{t(key)}</h3><p>{t(`${key}_desc`)}</p></div></div>)}<div className="aside-note"><Icon as={Info}/><p>{t('data_note')}</p></div><details className="existing"><summary>{t('existing')}</summary><p>{t('existing_desc')}</p></details></aside></div>
   </>}
   {report&&['plan','finance','allocation','repayment','sources'].includes(tab)&&<div className={tab==='plan'&&showForm?'report-wrap editing-report':'report-wrap'}>
    <div className="report-header"><div><div className="eyebrow">{t('report')} · {date(report.created_at)}</div><h1 ref={reportHeading} tabIndex={-1}>{report.input.business_name||t('business_plan')}</h1><p>{t('report_subtitle')}</p></div><div className="actions"><button onClick={()=>{setForm({...report.input,margin:String(report.input.margin)});setEditing(true);setTab('plan');window.scrollTo({top:0,behavior:'smooth'})}}><Icon as={MapPin}/>{t('edit')}</button><button onClick={print} title={t('print_tip')}><Icon as={Printer}/>{t('print')}</button><button onClick={clear}><Icon as={RefreshCw}/>{t('reset')}</button></div></div>
    <div className="report-context print-only"><span><Icon as={MapPin}/>{report.input.location} · {n(report.input.radius)} {t('km')}</span><span>{t('equity')}: <b>{money(report.input.margin)}</b></span><span className="badge">{t('estimated')}</span></div>
    <div className="print-only"><p>{t('input_preserved')}: {report.business.method==='user'?t(`sector.${report.business.category}`):report.input.business}</p></div>
    <div className={`report-section ${tab!=='plan'||showForm?'screen-hidden':''}`}>
     <div className={`verdict ${report.verdict}`}><div className="verdict-icon"><Icon as={Sprout} size={30}/></div><div><h2>{t('plan_readiness')}: {n(report.readiness?.score??0)} / {n(10)}</h2><p>{t('score_note')}</p><ul>{Object.entries(report.readiness?.checks||{}).map(([key,passed])=><li key={key}>{t(`check_${key}`)}: <b>{t(passed?'check_ready':'check_needed')}</b></li>)}</ul></div></div>
     {report.readiness&&<Section icon={Check} title={t('readiness')}><p>{t(report.readiness.missing.length?'readiness_missing':'readiness_ready')}</p><div className="district-chips">{report.readiness.missing.map(k=><span key={k}>{t(`facility.${k}`)}</span>)}</div><small>{t('readiness_note')}</small></Section>}
     {report.business.uncertain&&<Notice danger>{t('uncertain')}</Notice>}
     <Notice>{t(report.location.status==='district_proxy'?'district_proxy':'historical')}</Notice>
     <div className="metrics-grid window-grid"><Metric label={t('households')} value={n(m.households)} detail={t('estimated')}/><Metric label={t('price')} value={money(m.price)} detail={t(`unit_${m.unit}`)}/><Metric label={t('competitors')} value={n(m.competitors)} detail={t('estimated')}/><Metric label={t('net_after_debt')} value={money(m.net_after_debt)} detail={t('estimated')} accent/></div>
     <div className="ai-status" role="status"><span className="status-dot"/>{t(ai?.state==='pending'?'ai_pending':ai?.provider==='api'?'ai_api':ai?.provider==='local'?'ai_local':ai?.state==='done'?'ai_fallback':'ai_curated')}</div>
     <div className="report-grid"><Section icon={Users} title={t('market')}><p>{report.input.location} · {t('radius_fixed')}</p><p>{text('market')}</p><p>{t(`channels_${report.business.category}`)}</p><div className="inline-stat"><span>{t('households')}</span><b>{n(m.households)}</b></div><div className="region"><small>{t('local_economy')}</small><p>{t(`region.${report.location.district.region}`)}</p></div></Section><Section icon={TrendingUp} title={t('opportunity')}><p>{text('opportunity')}</p><div className="next-step"><Icon as={Check}/>{t('benefit_action_desc')}</div></Section>
      <Section icon={ShieldCheck} title={t('swot')} className="full"><div className="swot-grid">{['strengths','weaknesses','opportunity','threats'].map(k=><div key={k} className={`swot ${k}`}><h3>{t(k)}</h3><p>{text(k)}</p></div>)}</div></Section>
      <Section icon={Store} title={t('competition')}><div className="two-stats"><Metric label={t('competitors')} value={n(m.competitors)}/><Metric label={t('block_competitors')} value={n(m.block_competitors)}/></div><p>{text('competition')}</p><small>{t('competitor_map_note')}</small></Section>
      <Section icon={Wallet} title={t('pricing')}><div className="price-callout">{money(m.price_low)} – {money(m.price_high)}<small>{t('price_range')} · {t(`unit_${m.unit}`)}</small></div><p>{text('pricing')}</p><small>{t('price_disclaimer')}</small></Section>
     </div><Section icon={AlertTriangle} title={t('threat_identification')}><p>{text('threats')}</p><p>{t(`risk_${report.business.category}`)}</p><p>{t('spatial_risk_note')}</p><Nearby key={report.id} report={report}/></Section><p className="fineprint">{t('ai_disclaimer')}</p><button className="primary next-finance" onClick={()=>{setTab('finance');window.scrollTo({top:0,behavior:'smooth'})}}><Icon as={Calculator}/>{t('nav_finance')}<Icon as={ArrowRight}/></button>
    </div>
    <div className={`report-section ${tab!=='finance'?'screen-hidden':''}`}>
     <div className="section-intro"><h2>{t('finance_intro')}</h2></div>
     {report.funding&&<Section icon={Wallet} title={t(f.scheme==='self_funded'?'self_funded':'funding_plan')}><p>{t(f.scheme==='self_funded'?'savings_enough':f.funding_gap>0?'contribution_needed':'savings_and_loan')}</p><dl className="cost-list">{[['savings_amount',report.funding.savings],['savings_used',report.funding.used],['savings_left',report.funding.remaining],['funding_gap',f.funding_gap]].map(([key,value])=><div key={key}><dt>{t(key)}</dt><dd>{money(value)}</dd></div>)}</dl></Section>}
     <p>{t('finance_plain')}</p><p>{t('selected_scheme')}: <b>{t(f.scheme)}</b></p>{f.scheme==='nbcfdc'&&<Notice>{t('nbcfdc_note')}</Notice>}<p className="fineprint">{t('low_budget')}</p>{busy&&<p role="status">{t('loading')}</p>}
     <div className="metrics-grid window-grid"><Metric label={t('loan')} value={money(f.loan)} detail={t('estimated')} accent/><Metric label={t('project_cost')} value={money(f.project_cost)} detail={t('estimated')}/><Metric label={t('quarterly_payment')} value={money(f.quarterly_payment)} detail={t('calculated')}/><Metric label={t('equity')} value={money(f.margin)} detail={t('savings_used')}/></div>
     {f.scheme==='self_funded'?<Notice>{t('no_repayment')}</Notice>:
f.scheme==='outside'?
<Notice danger>{t('outside_note')}</Notice>:<><Section icon={Landmark} title={t(f.scheme)} className="scheme"><div className="scheme-facts"><div><small>{t('rate')}</small><b>{n(f.annual_rate,1)}%</b></div><div><small>{t('tenure')}</small><b>{n(f.tenure_months)} {t('months')}</b></div><div><small>{t('moratorium')}</small><b>{n(f.moratorium_months)} {t('months')}</b></div></div><p>{t('moratorium_note',{grace:n(f.moratorium_months),first:n(f.moratorium_months+3),last:n(f.tenure_months)})}</p><small>{t('interest_assumption')}</small></Section>{f.cap_applied&&<Notice danger>{t('cap_note')}</Notice>}</>}
     <div className="report-grid"><Section icon={Wallet} title={t('operating')}><dl className="cost-list">{['revenue','fixed_cost','variable_cost','monthly_cost','operating_profit','net_after_debt','working_capital','working_allocated','working_gap','starter_cost','established_cost'].map(k=><div key={k} className={k==='net_after_debt'?'total':''}><dt>{t(k)}</dt><dd>{money(m[k])}</dd></div>)}</dl><div className="inline-stat"><span>{t('break_even_units')}</span><b>{m.break_even_units===null?t('no_break_even'):n(m.break_even_units)}</b></div><div className="stress"><span>{t('downside')}</span><b>{money(m.downside_profit)}</b></div></Section>
      <div><Section icon={Landmark} title={t('eligibility')}><p>{t('eligibility_desc')}</p><span className="badge">{t(report.scheme_screening?.schemes.find(s=>s.id===f.scheme)?.status||'need_details')}</span><p>{t(report.input.community==='sc'?'agency_sc':'agency_other')}</p><div className="source-links"><a href={report.scheme_screening?.schemes.find(s=>s.id===f.scheme)?.source||'https://nsfdc.nic.in/faqs'} target="_blank" rel="noreferrer">{t('official_details')} ↗</a><a href={report.input.community==='sc'?'https://tahdco.com/':'https://www.bcmbcmw.tn.gov.in/'} target="_blank" rel="noreferrer">{t('local_access')} ↗</a></div><small>{t('application_note')}</small></Section></div>
     </div>
     <Schemes form={report.input} onProfile={()=>{setTab('plan');setEditing(true)}} onUse={async id=>{await run({...report.input,scheme_id:id},false);setTab('finance')}}/><Nearby key={report.id} report={report} mode="bank" scheme={f.scheme}/>
     <Section icon={TrendingUp} title={t('projection')}><p>{t('projection_note')}</p><div className="projection-chart" role="img" aria-label={t('projection')}><div className="chart-legend"><span className="sales">{t('revenue')}</span><span className="cost">{t('costs')}</span></div><div className="chart-bars">{m.projection.map(row=><div className="chart-column" key={row.month}><div className="bar-pair"><i style={{height:`${Math.max(2,row.revenue/Math.max(...m.projection.flatMap(x=>[x.revenue,x.costs]),1)*120)}px`}}/><i style={{height:`${Math.max(2,row.costs/Math.max(...m.projection.flatMap(x=>[x.revenue,x.costs]),1)*120)}px`}}/></div><span>{n(row.month)}</span></div>)}</div><small>{t('month')}</small></div><details className="print-open"><summary>{t('projection')} · {t('monthly')}</summary><div className="table-wrap" tabIndex={0}><table><caption>{t('projection')}</caption><thead><tr>{['month','revenue','costs','repayment','cash','balance'].map(k=><th scope="col" key={k}>{t(k)}</th>)}</tr></thead><tbody>{m.projection.map(row=><tr key={row.month}>{['month','revenue','costs','repayment','cash','balance'].map(k=><td key={k}>{k==='month'?n(row[k]):money(row[k])}</td>)}</tr>)}</tbody></table></div></details></Section>

    </div>
    <div className={`report-section ${tab!=='allocation'?'screen-hidden':''}`}><h2>{t('nav_allocation')}</h2><p>{t('inventory_note')}</p>{report.budget&&<Section icon={Wallet} title={t('starter_inventory')}><dl className="cost-list">{report.budget.items.map(item=><div key={item.key}><dt>{item.key==='tools'?t(`tools_${report.business.category}`):t(`inventory_${item.key}`)}{item.provided&&<small> · {t('already_available')}</small>}</dt><dd>{money(item.amount)}</dd></div>)}<div className="total"><dt>{t('project_cost')}</dt><dd>{money(report.budget.project_cost)}</dd></div></dl></Section>}</div>
    <div className={`report-section repayment-section ${tab!=='repayment'?'screen-hidden':''}`}><h2>{t('nav_repayment')}</h2><p>{t('selected_scheme')}: {t(f.scheme)}</p><p>{t('planned_not_sanctioned')}</p><button onClick={()=>{if(saveRepaymentPlan(report)){setTab('tracker')}else setStorageError(true)}} disabled={!f.schedule.length}>{t('track_plan')}</button>     {f.schedule.length>0&&<Section icon={Calculator} title={t('schedule')}><div className="schedule-summary"><span>{t('total_interest')}: <b>{money(f.total_interest)}</b></span><span>{t('total_repayment')}: <b>{money(f.total_repayment)}</b></span><button onClick={download}><Icon as={Download}/>{t('csv')}</button></div><div className="table-wrap repayment-table" tabIndex={0}><table><caption>{t('schedule')}</caption><thead><tr>{['month','due_date','opening','interest','principal','payment','balance'].map(k=><th scope="col" key={k}>{t(k)}</th>)}</tr></thead><tbody>{f.schedule.map(row=><tr key={row.month} className={row.moratorium?'grace-row':''}><th scope="row">{n(row.month)}{row.moratorium&&<small>{t('grace')}</small>}</th><td>{date(row.due_date)}</td>{['opening','interest','principal','payment','balance'].map(k=><td key={k}>{money(row[k])}</td>)}</tr>)}</tbody></table></div></Section>}</div>
   </div>}
   {!report&&['finance','allocation','repayment'].includes(tab)&&<div className="empty"><Icon as={Calculator} size={48}/><h1>{t('empty')}</h1><button className="primary" onClick={()=>setTab('plan')}>{t('back')}<Icon as={ArrowRight}/></button></div>}
   <div className={`report-section sources ${tab!=='sources'?'screen-hidden':''}`}><div className="section-intro"><div><div className="eyebrow">03 · {t('nav_sources')}</div><h1>{t('sources_title')}</h1><p>{t('sources_intro')}</p></div></div><div className="report-grid"><Section icon={MapPin} title={t('coverage')}><p>{coverage?t('coverage_detail',{districts:n(coverage.districts),blocks:n(coverage.blocks),villages:n(coverage.villages)}):t('data_unavailable')}</p><small>{t('named_places')}</small><div className="district-chips">{coverage?.district_list.map(d=><span key={d.id}>{d.names[lang]}</span>)}</div></Section><Section icon={BookOpen} title={t('nav_sources')}><ul className="sources-list">{sourceLinks.map(([key,url])=><li key={key}><a href={url} target="_blank" rel="noreferrer">{t(key)} ↗</a></li>)}<li>{t('source_priors')}</li></ul><small>{t('source_date')}</small></Section><Section icon={Info} title={t('assumptions')}><ul className="assumptions">{['population','market','cost'].map(k=><li key={k}>{t(`assumptions_${k}`)}</li>)}</ul><p>{t('interest_assumption')}</p></Section><Section icon={ShieldCheck} title={t('model_title')}><p>{t('model_desc')}</p>{coverage?.metrics&&<Notice>{t('model_metric',{count:n(coverage.metrics.holdout),accuracy:n(coverage.metrics.accuracy*100,1)+'%'})}</Notice>}{report&&<><p>{t('confidence')}: {report.business.confidence===null?t('category'):n((report.business.confidence||0)*100,1)+'%'}</p><h3>{t('retrieved')}</h3><ul>{report.retrieval.map(r=><li key={r.id}>{r.source==='nabard'?<a target="_blank" rel="noreferrer" href={`${r.url}#page=${r.page}`}>{t('source_nabard')} · {t('page')} {n(r.page)}</a>:t(r.source==='nsfdc'?'source_scheme':'source_priors')}</li>)}</ul></>}</Section></div>
     <Section icon={Database} title={t('dataset_title')}><p>{t('dataset_intro')}</p><div className="dataset-grid">{[['villages','2024-09','official'],['districts','2024-09','official'],['sectors','2024-09','synthetic'],['knowledge','2024-09','official'],['schemes','2024-09','official'],['classifier','2024-09','synthetic']].map(([key,snap,kind])=><div className="dataset-card" key={key}><h3><Icon as={Database} size={16}/>{t(`dataset_${key}`)}</h3><small>{t('dataset_date',{date:snap})}</small><span className="badge">{t(`dataset_${kind}`)}</span></div>)}</div><small>{t('dataset_refresh_note')}</small></Section></div>
   </>}<details className="language-roadmap"><summary>{t('more_languages')}</summary><p>{t('language_roadmap')}</p></details>
  </main><NavHelper navigate={key=>{setStage('app');setTab(key)}}/><footer><span><Icon as={Sprout}/>{t('footer')}</span><span>{t(online?'online':'offline')}</span></footer>
 </>;
}

