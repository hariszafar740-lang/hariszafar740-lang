import {useEffect,useState} from 'react';

type Props={mode:'phase'|'bins';value:number;max:number;step:number;onChange:(n:number)=>void;timeLabel?:string;disabled?:boolean};
export default function Replay({mode,value,max,step,onChange,timeLabel,disabled=false}:Props){
 const [playing,setPlaying]=useState(false);
 const [speed,setSpeed]=useState(1);
 useEffect(()=>{if(disabled||value>=max)setPlaying(false)},[disabled,value,max]);
 useEffect(()=>{if(!playing||disabled)return;const timer=window.setTimeout(()=>onChange(Math.min(max,Math.round((value+step)*100)/100)),1000/speed);return()=>window.clearTimeout(timer)},[playing,disabled,value,max,step,speed,onChange]);
 const title=mode==='phase'?'Lunar phase playback':'Sky geometry playback';
 return <section className="replay" aria-label={title}>
  <div className="replay-head"><div><span className="replay-kicker">SIMULATION / {mode==='phase'?'01':'02'}</span><h2>{title}</h2></div><span className="replay-status" role="status">{disabled?'INPUTS CHANGED':playing?'PLAYING':value>=max?'COMPLETE':'PAUSED'}</span></div>
  <p>{mode==='phase'?'Step through the model lunar phase. Each step requests a fresh backend simulation; phase is not a calendar date.':'Replay the last comparison: exact start followed by calculated midpoint bins. This is not a route or forecast.'}</p>
  <label className="replay-slider"><span>{mode==='phase'?`PHASE ${value.toFixed(1)} / 29.5 DAYS`:`${timeLabel} · ${value===0?'EXACT START':'BIN MIDPOINT'}`}</span><input aria-label={mode==='phase'?'Playback lunar phase':'Comparison playback position'} type="range" min="0" max={max} step={step} value={value} disabled={disabled} onChange={e=>{setPlaying(false);onChange(Number(e.target.value))}}/></label>
  <div className="replay-controls"><button type="button" disabled={disabled} onClick={()=>{if(value>=max)onChange(0);setPlaying(v=>!v)}}>{playing?'Pause':'Play'}</button><button type="button" disabled={disabled||playing||value<=0} onClick={()=>onChange(Math.max(0,Math.round((value-step)*100)/100))}>Step backward</button><button type="button" disabled={disabled||playing||value>=max} onClick={()=>onChange(Math.min(max,Math.round((value+step)*100)/100))}>Step forward</button><button type="button" disabled={disabled} onClick={()=>{setPlaying(false);onChange(0)}}>Reset time</button><label>Speed <select aria-label={`${title} speed`} value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value="0.5">0.5×</option><option value="1">1×</option><option value="2">2×</option></select></label></div>
  {disabled&&<p>Run the comparison to replay the current inputs.</p>}
 </section>
}
