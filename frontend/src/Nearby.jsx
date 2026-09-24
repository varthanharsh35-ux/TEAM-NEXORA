import {useState,useEffect,lazy,Suspense} from 'react';
import {useTranslation} from 'react-i18next';
import {api,persist,restore} from './api';
const LocationMap=lazy(()=>import('./LocationMap'));
export default function Nearby({report,mode='competitor',scheme}){
 const cacheKey=`${report.input.lat}:${report.input.lon}:${report.business.category}`;
 const {t,i18n}=useTranslation(),[data,setData]=useState(()=>restore('gs-map-data',{})[cacheKey]||null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[verified,setVerified]=useState(false);
 function remember(r){setData(r);const old=restore('gs-map-data',{});persist('gs-map-data',Object.fromEntries([[cacheKey,r],...Object.entries(old).filter(([k])=>k!==cacheKey)].slice(0,4)))}
 const input=report.input,located=input.lat!=null&&input.lon!=null;
 useEffect(()=>{let active=true;if(located)api(`/map/cached?lat=${input.lat}&lon=${input.lon}&category=${report.business.category}`).then(r=>{if(active&&r)remember(r)}).catch(()=>{});return()=>{active=false}},[report.id]);
 const rows=(data?.points||[]).filter(p=>mode==='bank'?p.kind!=='competitor':p.kind==='competitor').filter(p=>!verified||p.schemes.includes(scheme));
 async function load(){setBusy(true);setError('');try{remember(await api(`/map/nearby?lat=${input.lat}&lon=${input.lon}&category=${report.business.category}`))}catch(e){setError(e.message==='map_wait'?'map_wait':'map_failed')}finally{setBusy(false)}}
 return <section className="panel nearby"><h2>{t(mode==='bank'?'nearby_banks':'nearby_businesses')}</h2><p>{t(mode==='bank'?'bank_map_note':'competitor_map_note')}</p>{located?<><button onClick={load} disabled={busy}>{t(busy?'loading':'load_places')}</button>{mode==='bank'&&<label className="checkbox"><input type="checkbox" checked={verified} onChange={e=>setVerified(e.target.checked)}/>{t('verified_providers')}</label>}<Suspense fallback={<p>{t('map_loading')}</p>}><LocationMap readOnly value={input} points={rows}/></Suspense>{error&&<p role="status">{t(error)}</p>}{data&&<><p>{t('map_checked')}: {new Intl.DateTimeFormat(`${i18n.language}-IN`,{dateStyle:'medium'}).format(new Date(data.checked+'T12:00:00'))} · {t(data.cached?'cached_places':'live_places')}</p>{rows.length===0&&<p>{t(verified?'no_verified_providers':'no_mapped_places')}</p>}<ul className="place-list">{rows.map(p=><li key={p.id}><a href={`https://www.openstreetmap.org/${p.id}`} target="_blank" rel="noreferrer">{p.names?.[i18n.language]||p.name||t(p.kind)}</a><span> · {t(p.kind)}{mode==='bank'&&` · ${t(p.schemes.includes(scheme)?'verified_provider':'provider_unconfirmed')}`}</span></li>)}</ul></>}</>:<p>{t('pin_required')}</p>}</section>
}
