import {useState} from 'react';
import {Download, Bookmark, Printer} from 'lucide-react';

export type SiteResult={name:string;latitude:number;longitude:number;height_m:number;sun_hours:number;earth_hours:number;overlap_hours:number;overlap_hours_plus_2deg:number};
export type PlanSnapshot={start:string;end:string;step_minutes:number;sun_clearance_deg:number;earth_clearance_deg:number;model_version:string;dataset_sha256:string;dataset_kind:string;sites:SiteResult[]};
const utc=(s:string)=>s.replace('T',' ').replace('Z',' UTC');
function download(value:unknown){
 const blob=new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'});
 const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='lunaris-site-comparison.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export default function Explore({plan}:{plan:PlanSnapshot}){
 const [baseline,setBaseline]=useState<PlanSnapshot|null>(null);
 const sameSite=(a:SiteResult,b:SiteResult)=>a.latitude===b.latitude && a.longitude===b.longitude && a.height_m===b.height_m;
 return <section className="explore-card" aria-labelledby="explore-title">
  <div className="explore-head"><div><div className="nav-label">TRADE STUDY / DECISION SUPPORT</div><h2 id="explore-title">Compare the alternatives<span>.</span></h2></div><button onClick={()=>setBaseline(plan)}><Bookmark size={14}/> PIN CURRENT AS BASELINE</button></div>
  <p>Pin a run, change the date or assumptions, and compare again. Only identical coordinates and observer heights are paired. Different durations, thresholds, sampling, or data sources are not like-for-like; no automatic site ranking is implied.</p>
  {baseline?<><div className="baseline-line"><strong>BASELINE</strong> {utc(baseline.start)} → {utc(baseline.end)} · {baseline.step_minutes}-minute bins · Sun &gt; {baseline.sun_clearance_deg}° / Earth &gt; {baseline.earth_clearance_deg}° <button onClick={()=>setBaseline(null)}>CLEAR</button></div>
   <div className="baseline-line"><strong>CURRENT</strong> {utc(plan.start)} → {utc(plan.end)} · {plan.step_minutes}-minute bins · Sun &gt; {plan.sun_clearance_deg}° / Earth &gt; {plan.earth_clearance_deg}°</div>
   <div className="trade-table"><table><thead><tr><th>Current site</th><th>Baseline overlap</th><th>Current overlap</th><th>Change</th></tr></thead><tbody>{plan.sites.map((site,i)=>{const matches=baseline.sites.filter(b=>sameSite(site,b));const match=matches.length===1?matches[0]:null;const delta=match?site.overlap_hours-match.overlap_hours:0;return <tr key={i}><th>{site.name} <small>{site.latitude}°, {site.longitude}° · {site.height_m} m</small></th><td>{match?`${match.overlap_hours} h`:'No unique coordinate match'}</td><td>{site.overlap_hours} h</td><td>{match?`${delta>=0?'+':''}${delta.toFixed(2)} h`:'—'}</td></tr>})}</tbody></table></div>
  </>:<div className="baseline-empty">No baseline pinned yet. Pin the current run to compare another date, location, or assumption.</div>}
  <div className="explore-actions"><button onClick={()=>download({schema:'lunaris-site-comparison-v1',exported_at_utc:new Date().toISOString(),notice:'Exploratory screening only; not flight qualified. No terrain, antenna or operational constraints.',current:plan,baseline})}><Download size={14}/> EXPORT JSON</button><button onClick={()=>window.print()}><Printer size={14}/> PRINT / SAVE PDF</button></div>
  <p className="explore-foot">JSON records the displayed results, selected assumptions, UTC intervals, model version and dataset hash. Pinned baseline is kept in this browser session only. Print uses your browser's PDF option.</p>
 </section>
}
