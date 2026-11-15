/// <reference types="vite/client" />
import {useEffect, useRef, useState} from 'react';
import moonTextureUrl from './assets/lroc_color_2k.jpg';
import {zoomCamera} from './globe-navigation.mjs';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';

type Props={phase:number; latitude:number; longitude:number; dust:number; onSelect:(lat:number,lon:number)=>void};
const rad=Math.PI/180;
function point(lat:number, lon:number, r:number){return new THREE.Vector3(r*Math.cos(lat*rad)*Math.cos(lon*rad),r*Math.sin(lat*rad),r*Math.cos(lat*rad)*Math.sin(lon*rad));}
function texture(){
 const canvas=document.createElement('canvas'); canvas.width=1024; canvas.height=512; const ctx=canvas.getContext('2d')!;
 let seed=8392; const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
 ctx.fillStyle='#aaa9a5';ctx.fillRect(0,0,1024,512);
 // Layered semi-transparent mottling and impact basins: illustrative, not a lunar map.
 for(let i=0;i<3600;i++){const x=rand()*1024,y=rand()*512,r=rand()*27+2;ctx.fillStyle=rand()>.5?'rgba(42,43,45,.055)':'rgba(250,245,230,.035)';ctx.beginPath();ctx.ellipse(x,y,r,r*(.35+rand()*.65),0,0,Math.PI*2);ctx.fill()}
 for(let i=0;i<500;i++){const x=rand()*1024,y=rand()*512,r=rand()*9+1;ctx.strokeStyle='rgba(232,229,219,.20)';ctx.lineWidth=Math.max(.5,r*.18);ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();ctx.fillStyle='rgba(27,30,32,.15)';ctx.beginPath();ctx.arc(x-r*.12,y-r*.1,r*.74,0,Math.PI*2);ctx.fill()}
 const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
}
export default function Globe({phase,latitude,longitude,dust,onSelect}:Props){
 const [textureStatus,setTextureStatus]=useState<'loading'|'nasa'|'fallback'>('loading');
 const [webglAvailable,setWebglAvailable]=useState(true);
 const host=useRef<HTMLDivElement>(null); const onSelectRef=useRef(onSelect); onSelectRef.current=onSelect;
 const refs=useRef<{sun:THREE.DirectionalLight;pin:THREE.Group;particles:THREE.Points;camera:THREE.PerspectiveCamera;controls:OrbitControls}|null>(null);
 useEffect(()=>{if(!host.current)return;const el=host.current;
 let active=true;
 const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(36,1,.1,100);camera.position.set(4.3,2.2,5.8);
 let renderer:THREE.WebGLRenderer;try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true})}catch{setWebglAvailable(false);return}
 renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.outputColorSpace=THREE.SRGBColorSpace;el.appendChild(renderer.domElement);
 const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=3.5;controls.maxDistance=11;controls.autoRotate=false;
 const geo=new THREE.SphereGeometry(2,96,64);const map=texture();const material=new THREE.MeshStandardMaterial({map,roughness:1});const moon=new THREE.Mesh(geo,material);scene.add(moon);
 new THREE.TextureLoader().load(moonTextureUrl,loaded=>{
  if(!active){loaded.dispose();return}
  loaded.colorSpace=THREE.SRGBColorSpace;
  loaded.wrapS=THREE.RepeatWrapping;
  loaded.repeat.x=-1;
  loaded.offset.x=1;
  material.map?.dispose();
  material.map=loaded;
  material.needsUpdate=true;
  setTextureStatus('nasa');
 },undefined,()=>{if(active)setTextureStatus('fallback')});
 scene.add(new THREE.AmbientLight(0x9aabbc,.72));const sun=new THREE.DirectionalLight(0xfff7e8,2.6);scene.add(sun);
 const glow=new THREE.Mesh(new THREE.SphereGeometry(2.07,64,48),new THREE.MeshBasicMaterial({color:0x61c8ef,transparent:true,opacity:.035,side:THREE.BackSide}));scene.add(glow);
 const rings=new THREE.Group();for(const radius of [2.28,2.5,2.7]){const points=[];for(let i=0;i<=128;i++){const a=i/128*Math.PI*2;points.push(new THREE.Vector3(radius*Math.cos(a),0,radius*Math.sin(a)))}const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:0x62c8e3,transparent:true,opacity:.055}));line.rotation.x=.26;line.rotation.z=-.15;rings.add(line)}scene.add(rings);
 const particleGeo=new THREE.BufferGeometry();const positions=[];let seed=42;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};for(let i=0;i<450;i++){const a=rand()*Math.PI*2;const v=rand()*2-1;const r=2.08+rand()*.42;positions.push(r*Math.sqrt(1-v*v)*Math.cos(a),r*v,r*Math.sqrt(1-v*v)*Math.sin(a))}particleGeo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));const particles=new THREE.Points(particleGeo,new THREE.PointsMaterial({color:0x79dcf6,size:.012,transparent:true,opacity:.35}));scene.add(particles);
 const pin=new THREE.Group();const circle=new THREE.Mesh(new THREE.SphereGeometry(.055,16,16),new THREE.MeshBasicMaterial({color:0x72e8ff}));pin.add(circle);const halo=new THREE.Mesh(new THREE.RingGeometry(.09,.105,32),new THREE.MeshBasicMaterial({color:0x8deaff,side:THREE.DoubleSide,transparent:true,opacity:.85}));pin.add(halo);scene.add(pin);refs.current={sun,pin,particles,camera,controls};
 let down={x:0,y:0};renderer.domElement.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY}});const click=(e:PointerEvent)=>{if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)return;const rect=renderer.domElement.getBoundingClientRect();const mouse=new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-((e.clientY-rect.top)/rect.height)*2+1);const ray=new THREE.Raycaster();ray.setFromCamera(mouse,camera);const hit=ray.intersectObject(moon)[0];if(hit){const p=hit.point.normalize();onSelectRef.current(Math.round(Math.asin(p.y)/rad*10)/10,Math.round(Math.atan2(p.z,p.x)/rad*10)/10)}};renderer.domElement.addEventListener('pointerup',click);
 const resize=()=>{const w=el.clientWidth,h=el.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)};const ro=new ResizeObserver(resize);ro.observe(el);resize();let frame=0;const render=()=>{frame=requestAnimationFrame(render);controls.update();renderer.render(scene,camera)};render();
 return()=>{active=false;cancelAnimationFrame(frame);ro.disconnect();renderer.domElement.removeEventListener('pointerup',click);controls.dispose();geo.dispose();material.map?.dispose();material.dispose();particleGeo.dispose();scene.traverse(o=>{if(o instanceof THREE.Mesh || o instanceof THREE.Line || o instanceof THREE.Points){o.geometry.dispose();const m=o.material; if(Array.isArray(m))m.forEach(x=>x.dispose());else m.dispose()}});renderer.dispose();el.removeChild(renderer.domElement);refs.current=null};
 },[]);
 useEffect(()=>{const r=refs.current;if(!r)return;r.sun.position.copy(point(0,phase/29.53*360,10));r.pin.position.copy(point(latitude,longitude,2.025));r.pin.lookAt(point(latitude,longitude,4));(r.particles.material as THREE.PointsMaterial).opacity=Math.min(.25,.08+dust*5)},[phase,latitude,longitude,dust]);
 const zoom=(factor:number)=>{const r=refs.current;if(r)zoomCamera(r.camera,r.controls,factor)};
 const resetView=()=>{refs.current?.controls.reset()};
 return <div className="globe-canvas" ref={host} aria-label="Interactive 3D lunar globe. Drag to rotate, scroll to zoom, click to select a site.">{webglAvailable?<div className="globe-controls" role="group" aria-label="Globe view controls"><button type="button" aria-label="Zoom in on globe" onClick={()=>zoom(.8)}>+</button><button type="button" aria-label="Zoom out on globe" onClick={()=>zoom(1.25)}>−</button><button type="button" aria-label="Reset globe view" onClick={resetView}>RESET VIEW</button></div>:<p className="webgl-unavailable" role="status">3D view unavailable. Enter latitude and longitude in the site inspector to continue.</p>}{webglAvailable&&<span className="globe-texture-status" role="status">{textureStatus==='loading'?'Loading surface image…':textureStatus==='nasa'?'NASA SVS LROC-derived imagery · visual only':'Illustrative fallback · NASA imagery unavailable'}</span>}</div>;
}
