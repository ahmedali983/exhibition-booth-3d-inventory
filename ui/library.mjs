import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OBJLoader} from 'three/addons/loaders/OBJLoader.js';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
import {OBJExporter} from 'three/addons/exporters/OBJExporter.js';

const $=id=>document.getElementById(id);
const DB='expovault-local-models',STORE='assets',MAX_BYTES=150*1024*1024;
let current=null,root=null,scene=null,camera=null,renderer=null,controls=null,grid=null,entries=[],box=null,resetPose=null,openToken=0,toastTimeout=null,dbPromise=null;
let resizeObserver=null;
const fileExt=name=>name.toLowerCase().split('.').pop();
const pretty=(bytes)=>bytes>=1024**2?(bytes/(1024**2)).toFixed(1)+' MB':bytes>=1024?(bytes/1024).toFixed(0)+' KB':bytes+' B';
const fileSafe=name=>name.replace(/[^a-zA-Z0-9_-]+/g,'_').slice(0,80);
function toast(t){const el=$('toast');el.textContent=t;el.classList.add('visible');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>el.classList.remove('visible'),4200)}
function db(){
 if(dbPromise)return dbPromise;
 dbPromise=new Promise((resolve,reject)=>{
  if(!('indexedDB' in window))return reject(new Error('This browser does not support local IndexedDB storage'));
  const req=indexedDB.open(DB,1);
  req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains(STORE))req.result.createObjectStore(STORE,{keyPath:'id'})};
  req.onsuccess=()=>resolve(req.result);
  req.onerror=()=>reject(req.error||new Error('Local storage unavailable'));
 });
 return dbPromise;
}
async function transact(method,mode='readonly',value){
 const database=await db();
 return new Promise((resolve,reject)=>{
  const tx=database.transaction(STORE,mode),store=tx.objectStore(STORE);
  const req=method==='getAll'?store.getAll():method==='get'?store.get(value):method==='put'?store.put(value):store.delete(value);
  req.onsuccess=()=>resolve(req.result);
  req.onerror=()=>reject(req.error||new Error('Local storage operation failed'));
 });
}
function enable(name,yes){$(name).disabled=!yes}
function download(name,data,mime='application/octet-stream'){
 const blob=data instanceof Blob?data:new Blob([data],{type:mime});const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),8000);
}
function viewer(){
 if(renderer)return;
 const host=$('viewport');
 scene=new THREE.Scene();
 scene.background=new THREE.Color('#dfe9e2');
 camera=new THREE.PerspectiveCamera(45,1,0.01,1e6);
 renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.setClearColor(0xdfe9e2);
 const canvas=renderer.domElement;
 canvas.setAttribute('aria-label','Interactive 3D preview of your local model');
 host.prepend(canvas);
 controls=new OrbitControls(camera,canvas);
 controls.enableDamping=true;
 controls.dampingFactor=.055;
 controls.maxPolarAngle=Math.PI-.01;
 const hemisphere=new THREE.HemisphereLight(0xffffff,0x577b68,2.5);
 scene.add(hemisphere);
 const key=new THREE.DirectionalLight(0xffffff,3.1);key.position.set(5,10,8);scene.add(key);
 const fill=new THREE.DirectionalLight(0xb2d2ff,1.1);fill.position.set(-6,3,-8);scene.add(fill);
 grid=new THREE.GridHelper(10,20,0xadc8b6,0xcbd9d0);scene.add(grid);
 const resize=()=>{
  const w=host.clientWidth,h=host.clientHeight;
  if(w<=0||h<=0)return;
  camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
 };
 resizeObserver=new ResizeObserver(resize);resizeObserver.observe(host);resize();
 function frame(){requestAnimationFrame(frame);if(document.hidden||!renderer)return;controls.update();renderer.render(scene,camera)}
 frame();
}
function disposeObject(object){
 object.traverse(n=>{
  if(n.geometry)n.geometry.dispose();
  if(n.material){const list=Array.isArray(n.material)?n.material:[n.material];for(const m of list){if(m.map)m.map.dispose();m.dispose()}}
 });
}
function clear(){
 if(root){scene.remove(root);disposeObject(root);root=null}
 entries=[];box=null;resetPose=null;
 $('materials').replaceChildren();
 $('viewportEmpty').hidden=false;
 for(const n of ['resetCamera','frameModel','applyColor','resetColors','saveLocal','exportGLB','exportOBJ','downloadOriginal','materials'])enable(n,false);
}
function focusObject(object){
 const bb=new THREE.Box3().setFromObject(object);
 if(bb.isEmpty()||!Number.isFinite(bb.min.x)||!Number.isFinite(bb.max.x))throw new Error('The file has no measurable 3D geometry');
 box=bb;
 const center=bb.getCenter(new THREE.Vector3()),size=bb.getSize(new THREE.Vector3());
 const max=Math.max(size.x,size.y,size.z,0.005);
 const vFov=camera.fov*Math.PI/180;
 const fit=(max*.6)/Math.tan(vFov/2),dist=Math.max(max*2.1,fit*1.5);
 camera.near=Math.max(.001,dist/10000);camera.far=Math.max(100,dist*500);camera.updateProjectionMatrix();
 const offset=new THREE.Vector3(.45,.32,.91).normalize().multiplyScalar(dist);
 camera.position.copy(center).add(offset);
 controls.target.copy(center);controls.minDistance=Math.max(max*.02,0.001);controls.maxDistance=Math.max(max*20,dist*5);controls.update();
 grid.position.y=bb.min.y-Math.max(.0001,max*.008);
 grid.scale.setScalar(max/10);
 resetPose={position:camera.position.clone(),target:center.clone()};
 updateDimensions();
}
function updateDimensions(){
 if(!box)return;
 const d=box.getSize(new THREE.Vector3());
 const unit=$('units').value;
 const label=unit==='unspecified'?'model units (not verified)':unit+' (assumed)';
 $('dimensions').textContent='Bounding size: '+[d.x,d.y,d.z].map(v=>Number(v).toFixed(3)).join(' × ')+' '+label+' · X × Y × Z';
}
function getMaterials(object){
 entries=[];
 object.traverse((node)=>{
  if(!node.isMesh||!node.material)return;
  const values=Array.isArray(node.material)?node.material:[node.material];
  const clones=values.map(x=>x.clone());
  node.material=Array.isArray(node.material)?clones:clones[0];
  for(const [index,material] of clones.entries()){
   if(entries.length>=500)break;
   entries.push({node,index,material,original:material.clone(),label:(node.name||'Mesh')+' / '+(material.name||'Material '+(index+1))});
  }
 });
 const select=$('materials');
 select.replaceChildren();
 for(let i=0;i<entries.length;i++){const opt=document.createElement('option');opt.value=i;opt.textContent=entries[i].label;select.append(opt)}
 if(!entries.length){const opt=document.createElement('option');opt.textContent='No editable materials found';select.append(opt)}
 enable('materials',entries.length>0);enable('applyColor',entries.length>0);enable('resetColors',entries.length>0);
}
function geometryInfo(object){
 let mesh=0,triangles=0;
 object.traverse(n=>{
  if(!n.isMesh||!n.geometry)return;
  mesh++;
  const geom=n.geometry;
  triangles+=Math.floor((geom.index?.count||geom.attributes.position?.count||0)/3);
 });
 if(mesh===0)throw new Error('There are no mesh objects in this file');
 return {mesh,triangles};
}
async function parseModel(bytes,ext){
 if(ext==='glb'){
  return new Promise((resolve,reject)=>new GLTFLoader().parse(bytes,'',g=>resolve(g.scene),reject));
 }
 if(ext==='obj'){
  const str=new TextDecoder('utf-8',{fatal:false}).decode(bytes);
  return new OBJLoader().parse(str);
 }
 if(ext==='stl'){
  const geometry=new STLLoader().parse(bytes);
  const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({name:'STL default',color:'#c5d5ca',roughness:.8,metalness:.05}));
  const group=new THREE.Group();group.name='Imported STL';group.add(mesh);return group;
 }
 if(ext==='fbx'){
  return new FBXLoader().parse(bytes,'');
 }
 throw new Error('Unsupported file format: '+ext);
}
async function openFile(file,existingId=null){
 if(!file)return;
 const ext=fileExt(file.name);
 if(!['glb','obj','stl','fbx'].includes(ext)){toast('Use a GLB, OBJ, FBX or STL model');return}
 if(file.size>MAX_BYTES){toast('Maximum file size is 150 MB for this browser studio');return}
 if(file.size===0){toast('This file appears to be empty');return}
 const token=++openToken;
 $('viewerMessage').textContent='Reading '+file.name+'…';
 viewer();clear();
 try{
  const bytes=await file.arrayBuffer();
  if(token!==openToken)return;
  const object=await parseModel(bytes,ext);
  if(token!==openToken)return;
  if(!object)throw Error('No 3D scene could be loaded');
  const info=geometryInfo(object);
  root=object;scene.add(root);
  focusObject(root);getMaterials(root);
  current={id:existingId||crypto.randomUUID(),name:file.name,size:file.size,ext,bytes,meshes:info.mesh,triangles:info.triangles};
  $('assetTitle').textContent=file.name;
  $('assetSubline').textContent='Local 3D mesh · '+(existingId?'Opened from your browser library':'Opened directly from your device');
  $('assetFormat').textContent=ext.toUpperCase();
  $('meshCount').textContent=info.mesh.toLocaleString();
  $('triangles').textContent=info.triangles.toLocaleString();
  $('fileSize').textContent=pretty(file.size);
  $('viewportEmpty').hidden=true;
  $('viewerMessage').textContent='Loaded '+file.name+' · orbit and inspect';
  $('colourStatus').textContent=entries.length+' editable material slots found. Apply your colour and export a new 3D model.';
  for(const n of ['resetCamera','frameModel','saveLocal','exportGLB','exportOBJ','downloadOriginal'])enable(n,true);
  renderer.render(scene,camera);
  toast('3D model loaded successfully');
 }catch(error){
  current=null;clear();$('viewerMessage').textContent='Could not load this 3D model';
  $('viewportEmpty').querySelector('p').textContent='The file may be unsupported, incomplete or depend on external textures. Try a self-contained GLB file.';
  toast('Could not open 3D file: '+error.message);console.error(error);
 }
}
function recolor(){
 const entry=entries[Number($('materials').value)];
 if(!entry)return;
 if(!entry.material.color){$('colourStatus').textContent='This material cannot be recoloured with a standard RGB colour';return}
 entry.material.color.set($('color').value);
 if($('solidColor').checked&&'map' in entry.material)entry.material.map=null;
 entry.material.needsUpdate=true;
 $('colourStatus').textContent='Brand colour applied in this viewer. Save a new GLB to keep the change. Original file is unaffected.';
}
function resetMaterial(){
 const entry=entries[Number($('materials').value)];
 if(!entry)return;
 entry.material.copy(entry.original);
 entry.material.needsUpdate=true;
 $('colourStatus').textContent='Selected material restored to its original settings.';
}
function sceneThumbnail(){
 try{
  renderer.render(scene,camera);
  return renderer.domElement.toDataURL('image/webp',.64);
 }catch(_){return null}
}
async function saveCurrent(){
 if(!current)return;
 const btn=$('saveLocal');btn.disabled=true;btn.textContent='Saving in this browser…';
 try{
  const record={id:current.id,name:current.name,ext:current.ext,size:current.size,bytes:current.bytes,thumbnail:sceneThumbnail(),saved_at:Date.now(),meshes:current.meshes,triangles:current.triangles};
  await transact('put','readwrite',record);
  toast('Original model saved inside this browser');
  await renderLocalLibrary();
 }catch(error){toast('Could not save locally: '+error.message)}
 finally{btn.disabled=false;btn.textContent='⬡  Save original to my browser library'}
}
async function renderLocalLibrary(){
 const host=$('localGrid');host.replaceChildren();
 try{
  const records=await transact('getAll');
  records.sort((a,b)=>b.saved_at-a.saved_at);
  $('libraryCount').textContent=records.length+' asset'+(records.length===1?'':'s');
  $('localEmpty').hidden=records.length>0;
  for(const rec of records){
   const card=document.createElement('article');card.className='local-card';
   if(rec.thumbnail){
    const img=document.createElement('img');img.alt=rec.name;img.src=rec.thumbnail;card.append(img);
   }else{
    const art=document.createElement('div');art.className='local-card-image-fallback';art.textContent='⬡';card.append(art);
   }
   const body=document.createElement('div');body.className='local-card-body';
   const h=document.createElement('h3');h.textContent=rec.name;
   const subtitle=document.createElement('p');subtitle.textContent=rec.ext.toUpperCase()+' · '+pretty(rec.size)+' · '+(rec.meshes||0)+' mesh objects';
   const actions=document.createElement('div');actions.className='local-card-buttons';
   const open=document.createElement('button');open.textContent='Open 3D';
   open.onclick=async()=>{const record=await transact('get','readonly',rec.id);if(record){const file=new File([record.bytes],record.name);await openFile(file,record.id);window.scrollTo({top:0,behavior:'smooth'})}};
   const original=document.createElement('button');original.textContent='Original';original.title='Download the original file you added';
   original.onclick=async()=>{const record=await transact('get','readonly',rec.id);if(record)download(record.name,record.bytes)};
   const remove=document.createElement('button');remove.textContent='✕';remove.title='Remove only from this browser library';
   remove.onclick=async()=>{
    if(!window.confirm('Remove '+rec.name+' from this browser library? Keep a backup of your original file.'))return;
    await transact('delete','readwrite',rec.id);await renderLocalLibrary();toast('Removed local stored copy');
   };
   actions.append(open,original,remove);body.append(h,subtitle,actions);card.append(body);host.append(card);
  }
 }catch(error){$('localEmpty').hidden=false;$('localEmpty').textContent='Browser storage unavailable: '+error.message}
}
async function exportBranded(){
 if(!current||!root)return;
 const btn=$('exportGLB');btn.disabled=true;btn.textContent='Exporting…';
 try{
  const buf=await new Promise((resolve,reject)=>new GLTFExporter().parse(root,resolve,reject,{binary:true,onlyVisible:true,maxTextureSize:2048}));
  download(fileSafe(current.name.replace(/\.[^.]+$/,''))+'-branded.glb',buf);
  toast('Exported a new editable GLB; original remains unchanged');
 }catch(error){toast('GLB export failed: '+error.message)}
 finally{btn.textContent='↓ Export GLB';btn.disabled=false}
}
function exportObj(){
 if(!root||!current)return;
 try{
  const mesh=new OBJExporter().parse(root);
  download(fileSafe(current.name.replace(/\.[^.]+$/,''))+'-mesh.obj',mesh,'text/plain');
  toast('OBJ geometry exported; materials may need manual recreation');
 }catch(error){toast('OBJ export failed: '+error.message)}
}
function setup(){
 const zone=$('dropZone'),input=$('assetFile');
 zone.onclick=()=>input.click();
 zone.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();input.click()}};
 input.onchange=async()=>{if(input.files[0])await openFile(input.files[0]);input.value=''};
 zone.ondragenter=e=>{e.preventDefault();zone.classList.add('dragging')};
 zone.ondragover=e=>{e.preventDefault();zone.classList.add('dragging')};
 zone.ondragleave=()=>zone.classList.remove('dragging');
 zone.ondrop=async e=>{e.preventDefault();zone.classList.remove('dragging');if(e.dataTransfer.files[0])await openFile(e.dataTransfer.files[0])};
 document.addEventListener('dragover',e=>e.preventDefault());
 document.addEventListener('drop',e=>e.preventDefault());
 $('units').onchange=updateDimensions;
 $('color').oninput=e=>$('colorLabel').textContent=e.target.value.toUpperCase();
 $('applyColor').onclick=recolor;$('resetColors').onclick=resetMaterial;
 $('resetCamera').onclick=()=>{
  if(!resetPose||!controls)return;camera.position.copy(resetPose.position);controls.target.copy(resetPose.target);controls.update();
 };
 $('frameModel').onclick=()=>{if(root)focusObject(root)};
 $('saveLocal').onclick=saveCurrent;
 $('downloadOriginal').onclick=()=>{if(current)download(current.name,current.bytes)};
 $('exportGLB').onclick=exportBranded;$('exportOBJ').onclick=exportObj;
 renderLocalLibrary();
}
setup();
