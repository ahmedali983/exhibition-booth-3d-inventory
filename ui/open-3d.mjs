import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';

const $=id=>document.getElementById(id);
const el=(tag,className,text)=>{
 const node=document.createElement(tag);
 if(className)node.className=className;
 if(text!==undefined)node.textContent=String(text);
 return node;
};
const state={assets:[],visible:[],packs:[],filter:'all',query:'',sort:'featured',count:32,active:null,activeIndex:-1,originalMaterials:[],scene:null,camera:null,renderer:null,controls:null,object:null,resetView:null,observer:null,frame:0,loadId:0};
let toastTimer=0;
const fmt=num=>Number(num||0).toLocaleString('en-US');
const size=bytes=>bytes>=1048576?(bytes/1048576).toFixed(2)+' MB':(bytes/1024).toFixed(0)+' KB';
const validPath=str=>typeof str==='string'&&(/^assets\/open-3d\/CC0-\d+\.(glb|webp)$/.test(str)||/^assets\/authorized-booths\/[A-Za-z][A-Za-z0-9_-]{2,64}\.(glb|webp)$/.test(str));
function notice(message){$('toast').textContent=message;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),3200)}
function downloadBlob(fileName,result,type='model/gltf-binary'){
 const blob=result instanceof Blob?result:new Blob([result],{type});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download=fileName;document.body.append(link);link.click();link.remove();
 setTimeout(()=>URL.revokeObjectURL(url),8000);
}
async function loadLibrary(){
 const [original,approved]=await Promise.all([
  fetch('catalog/open_3d_cc0.json').then(r=>{if(!r.ok)throw Error('3D asset catalogue unavailable (HTTP '+r.status+')');return r.json()}),
  fetch('catalog/authorized_booths.json').then(r=>r.ok?r.json():{assets:[]})
 ]);
 const licensed=(approved.assets||[]).filter(v=>v?.glb&&validPath(v.glb)).map(v=>({
  ...v,
  name:v.name||v.title,
  pack:v.is_full_booth?'Creator-licensed booth designs':'Creator-licensed 3D items',
  pack_slug:v.is_full_booth?'licensed-booths':'licensed-items',
  thumbnail:validPath(v.thumbnail)?v.thumbnail:null,
  source_creator:v.creator||'Original creator',
  triangles:Number(v.triangles||0),
  file_size:Number(v.file_size||0)
 }));
 const groups=[...(original.packs||[])];
 for(const [slug,title] of [['licensed-booths','Creator-licensed booths'],['licensed-items','Creator-licensed items']]){
  const count=licensed.filter(v=>v.pack_slug===slug).length;
  if(count)groups.unshift({slug,title,available:count});
 }
 return {assets:[...licensed,...(original.assets||[])],packs:groups,licensedCount:licensed.length};
}
function card(asset){
 const item=el('article','open-card');
 const picture=el('div','open-card-image');
 if(asset.thumbnail){
  const image=el('img');image.src=asset.thumbnail;image.alt=asset.name+' — 3D model preview';image.loading='lazy';image.decoding='async';
  image.onerror=()=>{image.remove();picture.style.background='#e1eae3';picture.append(el('div','model-thumb-fallback','◈'))};
  picture.append(image);
 }else{
  picture.append(el('div','model-thumb-fallback','◈'));
 }
 picture.append(el('span','label',asset.is_full_booth?'◈ FULL BOOTH':'◈ REAL GLB'));
 const look=el('button','','✳ Inspect 3D and recolour');look.onclick=()=>open(asset);
 picture.onclick=e=>{if(e.target!==look)open(asset)};
 picture.append(look);
 const body=el('div','open-card-body');
 body.append(el('div','open-card-kicker',asset.pack),el('h3','',asset.name),el('p','',asset.description||asset.kind));
 const facts=el('div','open-card-facts');
 facts.append(el('span','','GLB · '+size(asset.file_size)),el('span','',asset.license==='CC0-1.0'?'CC0':asset.license==='CC-BY-4.0'?'CC BY':'Licensed'));
 const actions=el('div','open-card-actions');
 const direct=asset.license==='CC-BY-4.0'?el('button','','↓ GLB + licence ZIP'):el('a','','↓ Download 3D');
 if(asset.license==='CC-BY-4.0')direct.onclick=()=>downloadLicensedPackage(asset,direct);
 else {direct.href=asset.glb;direct.download=asset.id+'.glb';direct.setAttribute('aria-label','Download original GLB for '+asset.name)}
 const customise=el('button','','✳ Recolour');customise.onclick=()=>open(asset);
 actions.append(direct,customise);body.append(facts,actions);item.append(picture,body);
 return item;
}
async function downloadLicensedPackage(asset,button){
 const old=button.textContent;button.disabled=true;button.textContent='Preparing…';
 try{
  if(!window.JSZip)throw Error('ZIP exporter is not available');
  const response=await fetch(asset.glb);
  if(!response.ok)throw Error('Original 3D GLB missing: HTTP '+response.status);
  const data=await response.arrayBuffer(),view=new DataView(data);
  if(data.byteLength<20||view.getUint32(0,true)!==0x46546c67||view.getUint32(8,true)!==data.byteLength)throw Error('Invalid GLB binary');
  const zip=new window.JSZip();
  zip.file('3D/'+asset.id+'.glb',data);
  zip.file('CREDITS.txt',[
   'Original designer: '+asset.creator,
   'Model title: '+asset.name,
   'Model source: '+asset.source_url,
   'Licence: Creative Commons Attribution 4.0',
   'https://creativecommons.org/licenses/by/4.0/',
   'Changes: none to archived source model in this package',
   'For any modified version, credit the author, link the licence, and state changes.',
   'The model is not an approved manufacturing/shop drawing.'
  ].join('\n'));
  zip.file('SOURCE.json',JSON.stringify({id:asset.id,uid:asset.uid,name:asset.name,creator:asset.creator,source:asset.source_url,license:asset.license,license_url:asset.license_url},null,2));
  const blob=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:4}});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=asset.id+'-ORIGINAL-3D.zip';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),10000);
  notice('Original Sketchfab model GLB downloaded from ExpoVault with CC BY credits');
 }catch(error){notice('3D download failed: '+error.message);console.error(error)}
 finally{button.disabled=false;button.textContent=old}
}
function sortedAssets(){
 const q=state.query.trim().toLowerCase();
 let list=state.assets.filter(a=>(state.filter==='all'||a.pack_slug===state.filter)&&
  (!q||[a.name,a.pack,a.description,a.kind,a.id].some(s=>String(s||'').toLowerCase().includes(q))));
 switch(state.sort){
  case 'name':list.sort((a,b)=>a.name.localeCompare(b.name));break;
  case 'size':list.sort((a,b)=>a.file_size-b.file_size);break;
  case 'triangles':list.sort((a,b)=>b.triangles-a.triangles);break;
  default:list.sort((a,b)=>Number(!!b.is_full_booth)-Number(!!a.is_full_booth)||((/gallery|retail|indoor-market/.test(a.pack_slug)?0:1)-(/gallery|retail|indoor-market/.test(b.pack_slug)?0:1))||a.name.localeCompare(b.name));
 }
 return list;
}
function runFilters(){
 state.visible=sortedAssets();state.count=32;render();
}
function render(more=false){
 const grid=$('assetGrid');if(!more)grid.replaceChildren();
 const fragment=document.createDocumentFragment();
 for(const asset of state.visible.slice(grid.children.length,state.count))fragment.append(card(asset));
 grid.append(fragment);
 $('emptyAssets').hidden=state.visible.length>0;
 $('visibleCount').textContent=fmt(state.visible.length);
 $('resultsLabel').textContent=fmt(state.visible.length)+' files';
 $('showMoreAssets').hidden=grid.children.length>=state.visible.length;
 $('assetProgress').textContent='Showing '+fmt(grid.children.length)+' of '+fmt(state.visible.length)+' self-hosted GLB files';
}
function filters(){
 const host=$('packFilters');
 for(const item of state.packs){
  const b=el('button','pack-tab',item.title+' · '+item.count);
  b.dataset.pack=item.slug;
  host.append(b);
 }
 host.querySelectorAll('[data-pack]').forEach(b=>b.onclick=()=>{
  state.filter=b.dataset.pack;
  history.replaceState(null,'',location.pathname+'?pack='+encodeURIComponent(state.filter));
  host.querySelectorAll('[data-pack]').forEach(c=>c.classList.toggle('selected',c===b));
  runFilters();
 });
}
function resizeViewer(){
 if(!state.renderer||!state.camera)return;
 const host=$('openCanvas'),w=host.clientWidth,h=host.clientHeight;
 if(w<1||h<1)return;
 state.camera.aspect=w/h;state.camera.updateProjectionMatrix();state.renderer.setSize(w,h,false);
}
function setupViewer(){
 if(state.renderer)return;
 const canvasHost=$('openCanvas');
 state.scene=new THREE.Scene();
 state.scene.background=new THREE.Color('#d9e8dc');
 state.camera=new THREE.PerspectiveCamera(42,1,.01,20000);
 const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 state.renderer=renderer;
 canvasHost.prepend(renderer.domElement);
 state.controls=new OrbitControls(state.camera,renderer.domElement);
 state.controls.enableDamping=true;
 state.controls.maxPolarAngle=Math.PI-.015;
 state.scene.add(new THREE.HemisphereLight('#ffffff','#6f9881',2.3));
 const l=new THREE.DirectionalLight('#ffffff',3.2);l.position.set(9,13,7);state.scene.add(l);
 const fill=new THREE.DirectionalLight('#c4e8ff',1.4);fill.position.set(-7,3,-9);state.scene.add(fill);
 state.observer=new ResizeObserver(resizeViewer);state.observer.observe(canvasHost);
 resizeViewer();
 function animate(){
  state.frame=requestAnimationFrame(animate);
  if(!state.renderer||document.hidden||$('openViewer').hidden)return;
  state.controls.update();state.renderer.render(state.scene,state.camera);
 }
 animate();
}
function disposeObject(root){
 if(!root)return;
 root.traverse(n=>{
  if(n.geometry)n.geometry.dispose();
  const mats=Array.isArray(n.material)?n.material:n.material?[n.material]:[];
  for(const m of mats){if(m.map)m.map.dispose();m.dispose()}
 });
}
function clearObject(){
 if(state.object){state.scene.remove(state.object);disposeObject(state.object)}
 state.object=null;state.originalMaterials=[];state.resetView=null;
 $('editableMaterial').replaceChildren();
 $('exportCustomized').disabled=true;
}
function fitModel(root){
 const bb=new THREE.Box3().setFromObject(root);
 if(bb.isEmpty())throw Error('This model has no visible geometry');
 const d=bb.getSize(new THREE.Vector3()),center=bb.getCenter(new THREE.Vector3());
 const max=Math.max(d.x,d.y,d.z,.001),rad=Math.max(max*2.2,(max*.62)/Math.tan(THREE.MathUtils.degToRad(state.camera.fov)*.5)*1.4);
 const offset=new THREE.Vector3(.8,.48,1).normalize().multiplyScalar(rad);
 state.camera.position.copy(center).add(offset);
 state.camera.near=Math.max(.0001,rad/10000);
 state.camera.far=rad*100;
 state.camera.updateProjectionMatrix();
 state.controls.target.copy(center);
 state.controls.minDistance=max*.05;
 state.controls.maxDistance=max*20;
 state.controls.update();
 state.resetView={cam:state.camera.position.clone(),target:center.clone()};
 $('meshDetail').textContent='Bounding box · '+[d.x,d.y,d.z].map(x=>x.toFixed(2)).join(' × ')+' model units';
}
function materials(root){
 const entries=[];
 root.traverse(n=>{
  if(!n.isMesh||!n.material)return;
  const list=Array.isArray(n.material)?n.material:[n.material];
  const clones=list.map(m=>m.clone());
  n.material=Array.isArray(n.material)?clones:clones[0];
  for(const m of clones){
   if(entries.length<200)entries.push({mesh:n,material:m,original:m.clone(),label:(n.name||'Mesh')+' · '+(m.name||'Material')});
  }
 });
 state.originalMaterials=entries;
 const sel=$('editableMaterial');sel.replaceChildren();
 for(const [i,m] of entries.entries()){
  const opt=el('option','',m.label);opt.value=i;sel.append(opt);
 }
 $('applyAssetColor').disabled=entries.length===0;$('resetAssetColor').disabled=entries.length===0;
}
async function open(asset){
 state.active=asset;
 state.activeIndex=state.visible.findIndex(v=>v.id===asset.id);
 $('openOverlay').hidden=false;$('openViewer').hidden=false;
 document.body.style.overflow='hidden';
 $('openTitle').textContent=asset.name;$('inspectorTitle').textContent=asset.name;
 $('inspectorDescription').textContent=asset.description||'Editable 3D scene component';
 $('inspectorSize').textContent=size(asset.file_size);
 $('inspectorTris').textContent=fmt(asset.triangles);
 $('originName').textContent=asset.source_creator||asset.pack;
 $('originName').href=asset.source_url&&asset.source_url.startsWith('https://')?asset.source_url:'#';
 $('inspectorLicense').textContent=asset.license==='CC0-1.0'?'CC0 1.0':asset.license==='CC-BY-4.0'?'CC BY 4.0':'Creator-approved';
 $('licenseStatus').textContent=asset.license==='CC0-1.0'?'CC0: no attribution required':asset.license==='CC-BY-4.0'?'CC BY: credit creator and source with any reuse':'Usage limited to the creator’s specific written permission';
 $('downloadRealGLB').href=asset.glb;
 $('downloadRealGLB').download=asset.id+'.glb';
 $('downloadRealGLB').textContent=asset.license==='CC-BY-4.0'?'↓ Download original 3D + licence ZIP':'↓ Download original GLB';
 $('downloadRealGLB').onclick=asset.license==='CC-BY-4.0'?e=>{e.preventDefault();downloadLicensedPackage(asset,$('downloadRealGLB'))}:null;
 $('nextAsset').disabled=state.activeIndex>=state.visible.length-1;
 $('loading3d').hidden=false;$('loading3d').textContent='Loading the original 3D geometry…';
 setupViewer();clearObject();
 const id=++state.loadId;
 try{
  const response=await fetch(asset.glb,{cache:'force-cache'});
  if(!response.ok)throw Error('GLB unavailable: HTTP '+response.status);
  const data=await response.arrayBuffer();
  const model=await new GLTFLoader().parseAsync(data,'');
  if(id!==state.loadId)return;
  const object=model.scene;
  if(!object)throw Error('3D scene is empty');
  state.object=object;state.scene.add(object);
  fitModel(object);materials(object);
  $('loading3d').hidden=true;$('exportCustomized').disabled=false;
 }catch(e){
  if(id!==state.loadId)return;
  $('loading3d').textContent='Preview unavailable: '+e.message;
  notice('Preview could not load. You can still download the original GLB.');
 }
}
function close(){
 ++state.loadId;
 $('openOverlay').hidden=true;$('openViewer').hidden=true;
 document.body.style.overflow='';
 clearObject();state.active=null;
}
function paint(){
 const slot=state.originalMaterials[Number($('editableMaterial').value)];
 if(!slot){notice('Select a material first');return}
 if(!slot.material.color){notice('Selected material cannot be recoloured');return}
 slot.material.color.set($('editableColor').value);
 slot.material.needsUpdate=true;
 notice('Colour applied to preview · export a new GLB to save it');
}
function resetMaterial(){
 const slot=state.originalMaterials[Number($('editableMaterial').value)];
 if(!slot)return;
 slot.material.copy(slot.original);
 slot.material.needsUpdate=true;
 notice('Original material restored');
}
function downloadBranded(){
 if(!state.object||!state.active)return;
 const button=$('exportCustomized');
 button.disabled=true;button.textContent='Exporting…';
 new GLTFExporter().parse(
  state.object,
  data=>{downloadBlob(state.active.id+'-custom-colours.glb',data);button.disabled=false;button.textContent='↓ Download coloured GLB';notice('Customized GLB is saved to downloads')},
  error=>{button.disabled=false;button.textContent='↓ Download coloured GLB';notice('3D export failed: '+error.message)},
  {binary:true,onlyVisible:true,maxTextureSize:1024}
 );
}
function wire(){
 $('scrollArchive').onclick=()=>$('assetCollection').scrollIntoView({behavior:'smooth'});
 $('searchAssets').oninput=e=>{state.query=e.target.value;runFilters()};
 $('sortAssets').onchange=e=>{state.sort=e.target.value;runFilters()};
 $('clearAssetSearch').onclick=()=>{
  state.query='';state.filter='all';$('searchAssets').value='';
  $('packFilters').querySelectorAll('.pack-tab').forEach(b=>b.classList.toggle('selected',b.dataset.pack==='all'));runFilters();
 };
 $('showMoreAssets').onclick=()=>{state.count+=40;render(true)};
 $('closeAsset').onclick=close;$('openOverlay').onclick=close;
 $('nextAsset').onclick=()=>{const next=state.visible[state.activeIndex+1];if(next)open(next)};
 $('resetView').onclick=()=>{
  if(!state.resetView)return;
  state.camera.position.copy(state.resetView.cam);state.controls.target.copy(state.resetView.target);state.controls.update();
 };
 $('editableColor').oninput=e=>$('editableHex').textContent=e.target.value.toUpperCase();
 $('applyAssetColor').onclick=paint;$('resetAssetColor').onclick=resetMaterial;
 $('exportCustomized').onclick=downloadBranded;
 document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&!$('openViewer').hidden)close();
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('searchAssets').focus()}
 });
}
async function init(){
 wire();
 try{
  const data=await loadLibrary();
  state.assets=(data.assets||[]).filter(a=>['CC0-1.0','CC-BY-4.0','RIGHTS-HOLDER-PERMISSION'].includes(a.license)&&validPath(a.glb)&&(!a.thumbnail||validPath(a.thumbnail)));
  const countByPack=new Map();
  for(const asset of state.assets)countByPack.set(asset.pack_slug,(countByPack.get(asset.pack_slug)||0)+1);
  state.packs=(data.packs||[]).filter(p=>countByPack.has(p.slug)).map(p=>({...p,count:countByPack.get(p.slug)}));
  $('totalAssets').textContent=fmt(state.assets.length);
  $('totalPacks').textContent=fmt(state.packs.length);
  $('sideAssetCount').textContent=fmt(state.assets.length);
 $('libraryLicenses').textContent=data.licensedCount?'Open + approved':'CC0';
  filters();
  const params=new URLSearchParams(location.search);
  const initialPack=params.get('pack');
  if(initialPack&&state.packs.some(p=>p.slug===initialPack))state.filter=initialPack;
  const chosen=$('packFilters').querySelector('[data-pack="'+state.filter+'"]');
  if(chosen)$('packFilters').querySelectorAll('[data-pack]').forEach(b=>b.classList.toggle('selected',b===chosen));
  runFilters();
  const chosenAsset=params.get('asset');
  if(chosenAsset){
   const matching=state.assets.find(a=>a.id===chosenAsset);
   if(matching){if(state.filter!=='all'&&matching.pack_slug!==state.filter){state.filter=matching.pack_slug;runFilters()}open(matching)}
  }
 }catch(error){$('assetGrid').textContent='Catalogue failed to load: '+error.message;notice(error.message)}
}
init();
