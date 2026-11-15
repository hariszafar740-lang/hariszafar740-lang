import {useState} from 'react';
import {Download, Bookmark, Printer} from 'lucide-react';
import {describeChanges} from './comparison.mjs';
import {buildExport} from './export-report.mjs';

export type SiteResult={name:string;latitude:number;longitude:number;height_m:number;sun_hours:number;earth_hours:number;overlap_hours:number;overlap_hours_plus_2deg:number};
export type PlanSnapshot={start:string;end:string;step_minutes:number;sun_clearance_deg:number;earth_clearance_deg:number;model_version:string;dataset_sha256:string;dataset_kind:string;sites:SiteResult[]};
const utc=(s:string)=>s.replace('T',' ').replace('Z',' UTC');
function download(value:unknown){
 const blob=new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'});
 const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='lunaris-site-comparison.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export default function Explore({plan}:{plan:PlanSnapshot}){
 const [baseline,setBaseline]=useState<PlanSnapshot|null>(null);
 const changes=baseline?describeChanges(baseline,plan):null;
 return <section className="explore-card" aria-labelledby="explore-title">
  <div className="explore-head"><div><div className="nav-label">TRADE STUDY / DECISION SUPPORT</div><h2 id="explore-title">Compare the alternatives<span>.</span></h2></div><button onClick={()=>setBaseline(plan)}><Bookmark size={14}/> PIN CURRENT AS BASELINE</button></div>
  <p>Pin a run, change the date or assumptions, and compare again. Only identical coordinates and observer heights are paired. Different durations, thresholds, sampling, or data sources are not like-for-like; no automatic site ranking is implied.</p>
  {baseline?<><div className="baseline-line"><strong>BASELINE</strong> {utc(baseline.start)} → {utc(baseline.end)} · {baseline.step_minutes}-minute bins · Sun &gt; {baseline.sun_clearance_deg}° / Earth &gt; {baseline.earth_clearance_deg}° <button onClick={()=>setBaseline(null)}>CLEAR</button></div>
   <div className="baseline-line"><strong>CURRENT</strong> {utc(plan.start)} → {utc(plan.end)} · {plan.step_minutes}-minute bins · Sun &gt; {plan.sun_clearance_deg}° / Earth &gt; {plan.earth_clearance_deg}°</div>
   {changes&&<div className="changes-panel" aria-labelledby="changes-title"><h3 id="changes-title">What changed?</h3><p>Changes describe the inputs and midpoint-bin results; they do not establish which change caused an outcome.</p>{changes.inputs.length?<ul>{changes.inputs.map((item,i)=><li key={i}>{item}</li>)}</ul>:<p>No scenario settings or data source changed.</p>}<p>Hours depend on the duration, bin size and clearances shown above. Geometric screening only; no terrain or antenna constraints.</p></div>}
   <div className="trade-table"><table><caption>Changes in midpoint-bin hours compared with the pinned baseline</caption><thead><tr><th scope="col">Current site</th><th scope="col">Sun change</th><th scope="col">Earth change</th><th scope="col">Overlap change</th></tr></thead><tbody>{changes?.sites.map((site,i)=><tr key={i}><th scope="row">{site.name} <small>{site.latitude}°, {site.longitude}° · {site.height_m} m</small></th>{site.matched?<><td>{site.sun}</td><td>{site.earth}</td><td>{site.overlap}</td></>:<td colSpan={3}>No unique coordinate match</td>}</tr>)}</tbody></table></div>
  </>:<div className="baseline-empty">No baseline pinned yet. Pin the current run to compare another date, location, or assumption.</div>}
  <div className="explore-actions"><button onClick={()=>download(buildExport(plan,baseline))}><Download size={14}/> EXPORT JSON</button><button onClick={()=>window.print()}><Printer size={14}/> PRINT / SAVE PDF</button></div>
  <p className="explore-foot">JSON exports the last successful comparison, not unsubmitted edits. It includes the full result, assumptions, dataset hash, limitations and a change summary if a baseline is pinned. Terrain is separate and has its own export. The code revision is not recorded automatically. Print uses your browser's PDF option.</p>
 </section>
}
