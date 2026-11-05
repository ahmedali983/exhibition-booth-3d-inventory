import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
const JSZip=window.JSZip;

const $=id=>document.getElementById(id);
const UI={
  width:'widthSelect',depth:'depthSelect',exposure:'exposureSelect',style:'styleSelect',fitout:'fitoutSelect'
};
const state={
  bases:[],sourceBases:[],assets:[],base:null,baseObject:null,baseBox:null,baseFloor:0,baseLoad:0,
  placed:[],selectedId:null,nextId:1,filterText:'',filterPack:'all',
  logoUrl:null,brand:'YOUR BRAND',primary:'#0d614e',accent:'#ebc486',panel:'#f3f7f4',
  exporting:false,dirty:false,ready:false
};
let scene,cam,renderer,controls,exportRoot,lights,grid,raycaster,mouse,observer,animationId;
let highlight=null,dragging=false,dragOffset=new THREE.Vector3(),dragPlane=new THREE.Plane(new THREE.Vector3(0,1),0),toastTimer;
let baseOriginalMaterials=[],logoBoard=null,logoTexture=null;
const loader=new GLTFLoader();
const downloader=new GLTFExporter();
const formats={width:[3,4,5,6,8,10,12],depth:[2,3,4,5,6,8],exposure:['Inline','Corner','Peninsula','Island'],style:['Minimal','Portal','Truss','Feature Wall','Canopy'],fitout:['Reception','Meeting','Retail','Digital','Storage']};
function toast(message){const box=$('toast');box.textContent=message;box.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>box.classList.remove('visible'),3200)}
function setStatus(message){$('sceneStatus').textContent=message;$('viewportState').textContent=message}
function setDirty(){state.dirty=true;$('saveState').textContent='● Unsaved changes'}
function clearDirty(){state.dirty=false;$('saveState').textContent='✓ Saved project'}
function validAsset(asset){return asset?.license==='CC0-1.0'&&/^assets\/open-3d\/CC0-\d+\.glb$/.test(asset.glb)}
function downloadBlob(filename,value,type='application/octet-stream'){
 const blob=value instanceof Blob?value:new Blob([value],{type});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();
 setTimeout(()=>URL.revokeObjectURL(url),10000);
}
function safeName(text){return String(text||'booth').replace(/[^a-z0-9_-]/gi,'-').slice(0,60)}
function getSelected(){return state.placed.find(x=>x.instanceId===state.selectedId)||null}
function baseChoice(){const f={
  width_m:+$(UI.width).value,depth_m:+$(UI.depth).value,
  booth_type:$(UI.exposure).value,style:$(UI.style).value,fitout:$(UI.fitout).value
 };
 return state.bases.find(b=>b.width_m===f.width_m&&b.depth_m===f.depth_m&&b.booth_type===f.booth_type&&b.style===f.style&&b.fitout===f.fitout);
}
function baseUrl(base,ext='glb'){if(base?.is_creator_base)return ext==='glb'?base.glb:null;return 'assets/generated/'+base.width_m+'x'+base.depth_m+'/'+base.id+'.'+ext}
function updateBasePreview(){
 const b=baseChoice();if(!b)return;
 $('baseName').textContent=b.style+' · '+b.booth_type;
 $('baseId').textContent=b.id+' / '+b.width_m+' × '+b.depth_m+' m';
 $('basePreview').src='assets/thumbs/'+b.id+'.webp';
}
function createViewer(){
 scene=new THREE.Scene();
 scene.background=new THREE.Color('#ddece3');
 cam=new THREE.PerspectiveCamera(40,1,.01,1000);
 renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
 renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;
 renderer.toneMappingExposure=1.45;
 const viewport=$('viewport');viewport.prepend(renderer.domElement);
 controls=new OrbitControls(cam,renderer.domElement);
 controls.enableDamping=true;controls.dampingFactor=.06;
 controls.maxPolarAngle=Math.PI*.48;
 controls.minDistance=.8;controls.maxDistance=80;
 const hemi=new THREE.HemisphereLight(0xffffff,0x879c87,2.3);
 const key=new THREE.DirectionalLight(0xffffff,3.1);key.position.set(-4,11,8);
 const rim=new THREE.DirectionalLight(0xc8e9ff,1.5);rim.position.set(7,5,-5);
 scene.add(hemi,key,rim);
 lights=[hemi,key,rim];
 grid=new THREE.GridHelper(16,32,0xa2bbab,0xc9d9ca);scene.add(grid);
 exportRoot=new THREE.Group();exportRoot.name='ExpoVault Complete Booth Design';scene.add(exportRoot);
 raycaster=new THREE.Raycaster();mouse=new THREE.Vector2();
 function resize(){const w=viewport.clientWidth,h=viewport.clientHeight;if(!w||!h)return;
  cam.aspect=w/h;cam.updateProjectionMatrix();renderer.setSize(w,h,false)}
 observer=new ResizeObserver(resize);observer.observe(viewport);resize();
 renderer.domElement.addEventListener('pointerdown',pointerDown);
 window.addEventListener('pointermove',pointerMove);
 window.addEventListener('pointerup',pointerUp);
 window.addEventListener('keydown',e=>{
  if(e.key==='Delete'&&document.activeElement?.tagName!=='INPUT')removeSelected();
  if(e.key==='Escape')selectItem(null);
 });
 function frame(){animationId=requestAnimationFrame(frame);if(document.hidden)return;controls.update();renderer.render(scene,cam)}
 frame();
}
function collectMaterials(root){
 const result=[];
 root.traverse(node=>{
  if(!node.isMesh||!node.material)return;
  const mats=Array.isArray(node.material)?node.material:[node.material];
  const cloned=mats.map(m=>m.clone());
  node.material=Array.isArray(node.material)?cloned:cloned[0];
  cloned.forEach(mat=>result.push({node,material:mat,original:mat.clone()}));
 });
 return result;
}
function recolorBase(){
 if(!state.baseObject)return;
 for(let i=0;i<baseOriginalMaterials.length;i++){
  const m=baseOriginalMaterials[i].material;
  const meshName=(baseOriginalMaterials[i].node.name+' '+m.name).toLowerCase();
  if(!m.color)continue;
  const orig=baseOriginalMaterials[i].original.color;
  if(state.base?.is_creator_base && m.map)continue;
  if(/floor|carpet|ground|baseplate/.test(meshName))m.color.copy(orig);
  else if(/panel|back|wall|wallboard|roof|screen/.test(meshName))m.color.set(state.panel);
  else if(/trim|metal|pole|column|rail|frame|truss/.test(meshName))m.color.set(state.accent);
  else if(i%5===0)m.color.set(state.accent);
  else if(i%4===0)m.color.set(state.panel);
  else m.color.set(state.primary);
  m.needsUpdate=true;
 }
}
function removeObject(node){
 if(!node)return;
 node.removeFromParent();
 node.traverse(child=>{
  if(child.geometry)child.geometry.dispose();
  const materials=Array.isArray(child.material)?child.material:child.material?[child.material]:[];
  for(const mat of materials){if(mat.map&&mat.map!==logoTexture)mat.map.dispose();mat.dispose()}
 });
}
function resetCamera(){
 if(!state.baseBox)return;
 const center=state.baseBox.getCenter(new THREE.Vector3());
 const size=state.baseBox.getSize(new THREE.Vector3());
 const reach=Math.max(size.x,size.y,size.z,2);
 const dist=Math.max(reach*1.9,5);
 cam.position.set(center.x+dist*.68,center.y+dist*.55,center.z+dist*1.06);
 controls.target.copy(center);controls.update();
 cam.near=.01;cam.far=dist*100;cam.updateProjectionMatrix();
}
async function loadBase(b,{preserve=true,quiet=false}={}){
 if(!b)return;
 const token=++state.baseLoad;
 if(!quiet){setStatus('Loading '+b.id+' geometry…');$('loadingScene').hidden=false}
 try{
  const res=await fetch(baseUrl(b),{cache:'force-cache'});
  if(!res.ok)throw Error('Base GLB unavailable: HTTP '+res.status);
  const gltf=await loader.parseAsync(await res.arrayBuffer(),'');
  if(token!==state.baseLoad)return;
  const prev=state.baseObject;
  if(prev)removeObject(prev);
  baseOriginalMaterials.forEach(x=>x.original.dispose());
  state.baseObject=gltf.scene;
  state.baseObject.name='Base '+b.id;
  if(b.is_creator_base){
   // Preserve original mesh topology, with a uniformly scaled editing scene.
   const before=new THREE.Box3().setFromObject(state.baseObject);
   const dims=before.getSize(new THREE.Vector3());
   if(before.isEmpty()||!Number.isFinite(dims.x)||dims.x<=0)throw Error('Original GLB has no valid geometry');
   const maxHorizontal=Math.max(dims.x,dims.z,.001);
   const uniformScale=Math.max(.00001,Math.min(10000,6/maxHorizontal));
   state.baseObject.scale.setScalar(uniformScale);
   const scaled=new THREE.Box3().setFromObject(state.baseObject);
   const center=scaled.getCenter(new THREE.Vector3());
   state.baseObject.position.set(-center.x,-scaled.min.y,-center.z);
   const size=new THREE.Box3().setFromObject(state.baseObject).getSize(new THREE.Vector3());
   b.width_m=Number(size.x.toFixed(2));b.depth_m=Number(size.z.toFixed(2));
   b.area_m2=Number((size.x*size.z).toFixed(2));
  }
  exportRoot.add(state.baseObject);
  baseOriginalMaterials=collectMaterials(state.baseObject);
  state.base=b;
  state.baseBox=new THREE.Box3().setFromObject(state.baseObject);
  state.baseFloor=state.baseBox.min.y;
  grid.position.y=state.baseFloor-.025;
  const maxSize=Math.max(b.width_m,b.depth_m);
  grid.scale.setScalar(Math.max(1,maxSize/16));
  if(!b.is_creator_base)recolorBase();await updateBrandBoard();
  resetCamera();
  if(!preserve)for(const item of [...state.placed])removeItem(item);
  $('loadingScene').hidden=true;
  $('currentBoothTitle').textContent=b.is_creator_base?b.name:b.style+' '+b.booth_type+' · '+b.width_m+' × '+b.depth_m+' m';
  $('dimensions').textContent=b.is_creator_base?'ORIGINAL CC BY GLB · normalized preview, not measured CAD': 'BASE: '+b.width_m+' × '+b.depth_m+' m · '+b.area_m2+' m²';
  $('boothArea').textContent=b.area_m2+' m²';
  setStatus('Booth structure ready · '+b.id);
  $('partsCount').textContent=String(state.placed.length);
  if(b.is_creator_base){
   $('basePreview').src=b.thumbnail||'assets/thumbs/EV-0001.webp';
   $('baseName').textContent=b.name;
   $('baseId').textContent='by '+b.creator+' · CC BY 4.0';
  }else updateBasePreview();
  $('exportDxf').disabled=!!b.is_creator_base;
  $('exportDxf').title=b.is_creator_base?'Creator original only includes GLB, no authentic DXF':'Download preliminary generated DXF';
  setDirty();state.ready=true;
  if(!quiet)toast('3D booth structure loaded');
 }catch(error){$('loadingScene').hidden=false;$('loadingScene').querySelector('p').textContent=error.message;setStatus('Could not load base geometry');toast(error.message);console.error(error)}
}
async function updateBrandBoard(){
 if(!state.baseBox)return;
 if(logoBoard){removeObject(logoBoard);logoBoard=null}
 const size=state.baseBox.getSize(new THREE.Vector3());
 const width=Math.min(size.x*.69,2.8),height=Math.min(.64,size.y*.24);
 const canvas=document.createElement('canvas');canvas.width=1536;canvas.height=384;
 const ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
 ctx.fillStyle='#ffffff';ctx.fillRect(0,0,canvas.width,canvas.height);
 if(state.logoUrl){
  try{
   const img=new Image();img.src=state.logoUrl;
   await img.decode();
   const ratio=Math.min(1250/img.naturalWidth,290/img.naturalHeight);
   const w=img.naturalWidth*ratio,h=img.naturalHeight*ratio;
   ctx.drawImage(img,(canvas.width-w)/2,(canvas.height-h)/2,w,h);
  }catch(error){console.warn('Logo could not be painted',error)}
 }else{
  ctx.fillStyle=state.primary;ctx.font='bold 132px Arial,sans-serif';ctx.textAlign='center';
  const max=state.brand.trim().slice(0,32)||'YOUR BRAND';
  ctx.fillText(max,768,242,1400);
 }
 logoTexture=new THREE.CanvasTexture(canvas);logoTexture.colorSpace=THREE.SRGBColorSpace;logoTexture.needsUpdate=true;
 const group=new THREE.Group();group.name='Brand sign';
 const plaque=new THREE.Mesh(new THREE.BoxGeometry(width+.12,height+.09,.03),new THREE.MeshStandardMaterial({color:state.accent,metalness:.08,roughness:.65}));
 plaque.position.z=-.016;group.add(plaque);
 const artwork=new THREE.Mesh(new THREE.PlaneGeometry(width,height),new THREE.MeshStandardMaterial({map:logoTexture,roughness:.7,metalness:0,side:THREE.DoubleSide}));
 artwork.position.z=.01;group.add(artwork);
 const bbox=state.baseBox;
 group.position.set((bbox.min.x+bbox.max.x)/2,Math.max(bbox.min.y+1.3,bbox.max.y-.47),bbox.min.z+Math.min(.42,size.z*.17));
 logoBoard=group;exportRoot.add(logoBoard);
}
function updateBrand(){
 state.brand=$('brandName').value.trim().slice(0,32)||'YOUR BRAND';
 state.primary=$('primaryColor').value;state.accent=$('accentColor').value;state.panel=$('panelColor').value;
 recolorBase();updateBrandBoard();setDirty();toast('Brand palette applied to the booth');
}
function getRay(ev){
 const r=renderer.domElement.getBoundingClientRect();
 mouse.x=((ev.clientX-r.left)/r.width)*2-1;
 mouse.y=-((ev.clientY-r.top)/r.height)*2+1;
 raycaster.setFromCamera(mouse,cam);
 return raycaster;
}
function pointerDown(ev){
 if(!state.ready)return;
 const hits=getRay(ev).intersectObjects(state.placed.map(x=>x.pivot),true);
 if(hits.length){
  let object=hits[0].object;
  while(object&&!object.userData.instanceId)object=object.parent;
  if(object?.userData.instanceId)selectItem(object.userData.instanceId);
 }
 if(ev.shiftKey&&getSelected()){
  const p=new THREE.Vector3();
  dragPlane.constant=-state.baseFloor;
  if(getRay(ev).ray.intersectPlane(dragPlane,p)){
   dragging=true;
   const item=getSelected();
   dragOffset.set(item.pivot.position.x-p.x,0,item.pivot.position.z-p.z);
   controls.enabled=false;
  }
 }
}
function pointerMove(ev){
 if(!dragging||!getSelected())return;
 const out=new THREE.Vector3();
 if(getRay(ev).ray.intersectPlane(dragPlane,out)){
  const item=getSelected();
  item.pivot.position.x=clampPosition(out.x+dragOffset.x,'x');
  item.pivot.position.z=clampPosition(out.z+dragOffset.z,'z');
  syncTransforms();setDirty();
 }
}
function pointerUp(){dragging=false;if(controls)controls.enabled=true}
function clampPosition(value,axis){
 if(!state.base)return value;
 const bound=(axis==='x'?state.base.width_m:state.base.depth_m)/2;
 return Math.max(-bound+.15,Math.min(bound-.15,value));
}
function selectItem(id){
 state.selectedId=id;const selected=getSelected();
 $('selectedName').textContent=selected?selected.asset.name:'Select a placed item to edit';
 $('selectionTag').hidden=!selected;
 $('selectedName').style.color=selected?'#2c6a44':'#8ba38f';
 for(const id of ['itemX','itemZ','itemRot','itemScale','removeItem','selectedMaterial','selectedItemColor','applyItemColor','moveLeft','moveRight','moveFront','moveBack'])$(id).disabled=!selected;
 if(highlight){scene.remove(highlight);highlight.geometry.dispose();highlight.material.dispose();highlight=null}
 if(selected){
  highlight=new THREE.BoxHelper(selected.pivot,0x1e9b70);
  scene.add(highlight);
  syncTransforms();
  const list=$('selectedMaterial');list.replaceChildren();
  selected.materials.forEach((info,index)=>{
   const o=document.createElement('option');o.value=String(index);o.textContent=(info.material.name||info.node.name||'Material')+' '+(index+1);list.append(o);
  });
 }else{
  $('selectedMaterial').replaceChildren();
 }
}
function syncTransforms(){
 const item=getSelected();if(!item)return;
 $('itemX').value=item.pivot.position.x.toFixed(2);
 $('itemZ').value=item.pivot.position.z.toFixed(2);
 $('itemRot').value=String(Math.round(THREE.MathUtils.radToDeg(item.pivot.rotation.y)));
 $('itemScale').value=item.pivot.scale.x.toFixed(2);
 if(highlight)highlight.update();
}
function removeItem(item){
 item.pivot.removeFromParent();
 removeObject(item.pivot);
 state.placed=state.placed.filter(p=>p!==item);
 $('partsCount').textContent=String(state.placed.length);
 if(state.selectedId===item.instanceId)selectItem(null);
 setDirty();
}
function removeSelected(){const item=getSelected();if(item){removeItem(item);toast('Removed '+item.asset.name)}}
async function addItem(asset,{record=null}={}){
 if(!state.base){toast('Choose a booth structure first');switchTab('base');return}
 if(!validAsset(asset))return toast('Only verified hosted CC0 geometry may be added');
 const id=record?.instanceId||'part-'+state.nextId++;
 if(state.placed.some(p=>p.instanceId===id))return;
 setStatus('Loading item '+asset.name+'…');
 try{
  const response=await fetch(asset.glb,{cache:'force-cache'});
  if(!response.ok)throw Error('Item GLB returned '+response.status);
  const parsed=await loader.parseAsync(await response.arrayBuffer(),'');
  const pivot=new THREE.Group();pivot.userData.instanceId=id;pivot.name='Placed: '+asset.name;
  const source=parsed.scene;
  const bounds=new THREE.Box3().setFromObject(source);
  if(bounds.isEmpty())throw Error('Model is missing geometry');
  const center=bounds.getCenter(new THREE.Vector3());
  source.position.set(-center.x,-bounds.min.y,-center.z);
  pivot.add(source);
  const max=Math.max(...bounds.getSize(new THREE.Vector3()).toArray(),.01);
  const suggested=Math.max(.15,Math.min(2,1.3/max));
  pivot.position.set(record?.x||0,state.baseFloor,record?.z||0);
  pivot.rotation.y=record?.r||0;
  pivot.scale.setScalar(record?.s||suggested);
  exportRoot.add(pivot);
  const materials=collectMaterials(source);
  const item={instanceId:id,asset,pivot,materials};
  state.placed.push(item);
  if(record?.colors){
   materials.forEach((ref,i)=>{
    const value=record.colors[i];if(value&&ref.material.color)ref.material.color.set(value);
   });
  }
  selectItem(id);$('partsCount').textContent=String(state.placed.length);
  setStatus(asset.name+' added · edit position or Shift+drag in 3D');
  toast('Added '+asset.name+' to the 3D booth');
  setDirty();return item;
 }catch(error){setStatus('Could not add '+asset.name);toast(error.message);console.error(error)}
}
function paintItem(){
 const item=getSelected();if(!item)return;
 const index=Number($('selectedMaterial').value),m=item.materials[index]?.material;
 if(!m?.color){toast('Selected material has no editable base colour');return}
 m.color.set($('selectedItemColor').value);m.needsUpdate=true;
 setDirty();toast('Selected 3D material recoloured');
}
function changeTransform(){
 const item=getSelected();if(!item)return;
 const x=Number($('itemX').value),z=Number($('itemZ').value),r=Number($('itemRot').value),s=Number($('itemScale').value);
 if(![x,z,r,s].every(Number.isFinite)){toast('Use valid numeric values');return}
 item.pivot.position.x=clampPosition(x,'x');
 item.pivot.position.z=clampPosition(z,'z');
 item.pivot.rotation.y=THREE.MathUtils.degToRad(r);
 item.pivot.scale.setScalar(Math.max(.05,Math.min(6,s)));
 if(highlight)highlight.update();setDirty();
}
function buildProject(){
 return {
  schema:'expovault-composer-v1',generated_at:new Date().toISOString(),
  base_id:state.base.id,
  brand:{name:state.brand,primary:state.primary,accent:state.accent,panel:state.panel,logo_data_url:state.logoUrl},
  items:state.placed.map(item=>({
   instanceId:item.instanceId,asset_id:item.asset.id,
   x:item.pivot.position.x,z:item.pivot.position.z,
   r:item.pivot.rotation.y,s:item.pivot.scale.x,
   colors:item.materials.map(m=>m.material.color?'#'+m.material.color.getHexString():null)
  })),
  notes:'Geometric concept only. Not certified for real manufacturing.'
 };
}
function projectFilename(){return 'expovault-'+(state.base?.id||'booth')+'-'+safeName(state.brand)}
function saveProject(){
 if(!state.base){toast('Choose a base structure first');return}
 downloadBlob(projectFilename()+'.json',JSON.stringify(buildProject(),null,2),'application/json;charset=utf-8');
 clearDirty();toast('Editable project JSON downloaded');
}
async function restoreProject(payload){
 if(payload?.schema!=='expovault-composer-v1'||!Array.isArray(payload.items)||payload.items.length>120)throw Error('This is not a valid ExpoVault Composer project');
 const b=state.bases.find(v=>v.id===payload.base_id);if(!b)throw Error('Booth ID not found in our local inventory');
 for(const [key,value] of Object.entries({width:b.width_m,depth:b.depth_m,exposure:b.booth_type,style:b.style,fitout:b.fitout}))$(UI[key]).value=String(value);
 const brand=payload.brand||{};
 $('brandName').value=brand.name||'YOUR BRAND';
 for(const [key,k] of [['primaryColor','primary'],['accentColor','accent'],['panelColor','panel']])$(key).value=/^#[0-9a-f]{6}$/i.test(brand[k]||'')?brand[k]:$(key).value;
 state.brand=$('brandName').value;state.primary=$('primaryColor').value;state.accent=$('accentColor').value;state.panel=$('panelColor').value;
 state.logoUrl=typeof brand.logo_data_url==='string'&&brand.logo_data_url.startsWith('data:image/')&&brand.logo_data_url.length<3e6?brand.logo_data_url:null;
 for(const item of [...state.placed])removeItem(item);
 await loadBase(b,{preserve:false,quiet:true});
 const lookup=new Map(state.assets.map(a=>[a.id,a]));
 for(const item of payload.items){const asset=lookup.get(item.asset_id);if(asset)await addItem(asset,{record:item})}
 selectItem(null);switchTab('items');clearDirty();
 toast('Project restored with '+state.placed.length+' placed items');
}
function findItemMatches(){
 const q=state.filterText.toLowerCase();
 return state.assets.filter(a=>(state.filterPack==='all'||a.pack_slug===state.filterPack)&&(!q||(a.name+' '+a.pack+' '+a.description+' '+a.kind).toLowerCase().includes(q)));
}
function renderItems(){
 const list=findItemMatches();
 $('itemResults').textContent=list.length+' items';
 const host=$('itemBrowser');host.replaceChildren();
 const frag=document.createDocumentFragment();
 for(const asset of list.slice(0,72)){
  const box=document.createElement('div');box.className='item-tile';
  const image=document.createElement('img');image.src=asset.thumbnail;image.loading='lazy';image.decoding='async';image.alt=asset.name;
  const detail=document.createElement('div'),name=document.createElement('h4');name.textContent=asset.name;
  const category=document.createElement('p');category.textContent=asset.pack;
  const button=document.createElement('button');button.textContent='+ Add to booth';button.onclick=()=>addItem(asset);
  detail.append(name,category,button);box.append(image,detail);frag.append(box);
 }
 host.append(frag);
 if(!list.length)host.append(document.createTextNode('No items match. Try another search.'));
}
function switchTab(tab){
 document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('selected',b.dataset.tab===tab));
 for(const id of ['base','items','brand','export'])$('tab-'+id).classList.toggle('selected',id===tab);
 document.querySelectorAll('.steps span').forEach((e,i)=>e.classList.toggle('current',['base','items','brand','export'][i]===tab));
}
async function generateGlb(){
 if(!state.baseObject)throw Error('Load a booth structure first');
 return await new Promise((resolve,reject)=>downloader.parse(
  exportRoot,
  out=>out instanceof ArrayBuffer?resolve(out):reject(Error('GLB binary not returned')),
  reject,{binary:true,onlyVisible:true,maxTextureSize:2048}
 ));
}
async function downloadGLB(){
 if(state.exporting)return;
 state.exporting=true;$('exportGlb').disabled=true;$('exportGlbPanel').disabled=true;
 setStatus('Preparing fully assembled 3D GLB…');
 try{const data=await generateGlb();downloadBlob(projectFilename()+'.glb',data,'model/gltf-binary');setStatus('GLB export complete');toast('Full booth GLB downloaded · '+Math.round(data.byteLength/1024)+' KB')}
 catch(error){toast('GLB export failed: '+error.message);console.error(error)}
 finally{state.exporting=false;$('exportGlb').disabled=false;$('exportGlbPanel').disabled=false}
}
async function downloadDXF(){
 if(!state.base)return toast('Select a booth first');
 if(state.base.is_creator_base)return toast('Original creator GLB contains no authentic DXF or original drawing; please use a generated booth for 2D concept plans.');
 const response=await fetch(baseUrl(state.base,'dxf'));
 if(!response.ok)return toast('DXF is not available');
 downloadBlob(state.base.id+'-concept.dxf',await response.blob(),'application/dxf');
 toast('Preliminary DXF downloaded');
}
function BOM(){
 const parts=state.placed.map(i=>({
  label:i.asset.name,asset_id:i.asset.id,license:i.asset.license,source:i.asset.source_url,
  glb:i.asset.glb,instance_id:i.instanceId,
  x_m:i.pivot.position.x,z_m:i.pivot.position.z,
  rotation_deg:THREE.MathUtils.radToDeg(i.pivot.rotation.y),scale:i.pivot.scale.x
 }));
 return {base:{id:state.base.id,width_m:state.base.width_m,depth_m:state.base.depth_m,area_m2:state.base.area_m2,
   schematic:baseUrl(state.base,'dxf'),source_url:state.base.source_url||null,creator:state.base.creator||null,license:state.base.license||null,production_status:'CONCEPT_NOT_MANUFACTURING_APPROVED'},
  brand:state.brand,parts,count:parts.length,
  note:'This is a design composition, not a BOM with verified commercial part codes or engineering tolerances.'};
}
async function downloadZIP(){
 if(state.exporting)return;
 state.exporting=true;$('exportZip').disabled=true;setStatus('Packaging full concept files…');
 try{
  const glb=await generateGlb();
  const dxf=state.base.is_creator_base?null:await fetch(baseUrl(state.base,'dxf')).then(r=>{if(!r.ok)throw Error('DXF missing');return r.arrayBuffer()});
  const zip=new JSZip();
  zip.file('3D/'+projectFilename()+'.glb',glb);
  if(dxf)zip.file('PLAN/'+state.base.id+'-concept.dxf',dxf);
  zip.file('PROJECT/'+projectFilename()+'.json',JSON.stringify(buildProject(),null,2));
  zip.file('PARTS/placed-items.json',JSON.stringify(BOM(),null,2));
  zip.file('README.txt',[
   'EXPOVAULT — CONCEPT HANDOFF PACK','',
   'The 3D GLB contains the selected base booth, hosted CC0 items and custom brand artwork.',
   dxf?'The DXF shows the generated base floor plan, NOT final installation drawings.':'Original creator model has no authentic source DXF; none is included.',
   'The placed-items list documents the original sources and colours.',
   'No Sketchfab view-only mesh was downloaded, copied or extracted.','',
   'IMPORTANT: NOT FABRICATION READY.',
   'Engineer and fabricator verification is required for tolerances, frame systems, cut sheets,',
   'joinery, accessibility, safety, print bleeds, electrical layouts and structural stability.'
  ].join('\n'));
  if(state.base.is_creator_base)zip.file('CREATOR_CREDITS.txt',[
   'Original model: '+state.base.name,'Original creator: '+state.base.creator,
   'Source: '+state.base.source_url,
   'Licence: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/',
   'Changes: uniformly scaled for composition, brand materials/sign or placed items may have been added.',
   'Credit original creator and link licence in downstream derivative works.',
   'This is not an original native SketchUp/FBX/DWG or fabrication-ready drawing.'
  ].join('\n'));
  const result=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:5}});
  downloadBlob(projectFilename()+'-CONCEPT-PACK.zip',result,'application/zip');
  setStatus('Concept ZIP exported');toast('Complete 3D concept pack downloaded');
 }catch(error){toast('ZIP export failed: '+error.message);console.error(error)}
 finally{state.exporting=false;$('exportZip').disabled=false}
}
function wire(){
 for(const [key,values] of Object.entries(formats)){
  const select=$(UI[key]);
  for(const v of values){const opt=document.createElement('option');opt.value=String(v);opt.textContent=String(v)+(key==='width'||key==='depth'?' m':'');select.append(opt)}
  select.addEventListener('change',updateBasePreview);
 }
 $('widthSelect').value='6';$('depthSelect').value='3';
 $('exposureSelect').value='Inline';$('styleSelect').value='Portal';$('fitoutSelect').value='Reception';
 document.querySelectorAll('.tab').forEach(button=>button.onclick=()=>switchTab(button.dataset.tab));
 $('applyBase').onclick=async()=>{await loadBase(baseChoice());switchTab('items')};
 $('applyOriginal').onclick=async()=>{
  const b=state.sourceBases.find(x=>x.id===$('originalDesign').value);
  if(!b){toast('Choose an original hosted designer booth first');return}
  await loadBase(b,{preserve:false});switchTab('brand');
 };
 $('itemSearch').oninput=e=>{state.filterText=e.target.value;renderItems()};
 $('itemPack').onchange=e=>{state.filterPack=e.target.value;renderItems()};
 for(const [picker,hex] of [['primaryColor','primaryHex'],['accentColor','accentHex'],['panelColor','panelHex']]){
  $(picker).oninput=e=>$(hex).textContent=e.target.value.toUpperCase();
 }
 $('applyBrand').onclick=updateBrand;
 $('logoFile').onchange=async e=>{
  const file=e.target.files?.[0];if(!file)return;
  if(file.size>2_000_000){toast('Maximum logo size is 2 MB');return}
  state.logoUrl=await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.readAsDataURL(file)});
  await updateBrandBoard();setDirty();toast('Logo added to booth model');
 };
 for(const control of ['itemX','itemZ','itemRot','itemScale'])$(control).onchange=changeTransform;
 for(const [id,dx,dz] of [['moveLeft',-.1,0],['moveRight',.1,0],['moveBack',0,-.1],['moveFront',0,.1]]){
  $(id).onclick=()=>{const item=getSelected();if(!item)return;item.pivot.position.x=clampPosition(item.pivot.position.x+dx,'x');
   item.pivot.position.z=clampPosition(item.pivot.position.z+dz,'z');syncTransforms();setDirty()};
 }
 $('removeItem').onclick=removeSelected;
 $('applyItemColor').onclick=paintItem;
 $('resetCamera').onclick=resetCamera;
 $('snapFloor').onclick=()=>{const item=getSelected();if(item){item.pivot.position.y=state.baseFloor;toast('Snapped to booth floor')}};
 $('saveProject').onclick=saveProject;$('saveProjectPanel').onclick=saveProject;
 $('exportGlb').onclick=downloadGLB;$('exportGlbPanel').onclick=downloadGLB;
 $('exportDxf').onclick=downloadDXF;$('exportZip').onclick=downloadZIP;
 $('importProject').onchange=async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{if(file.size>4e6)throw Error('Project file too large');const project=JSON.parse(await file.text());await restoreProject(project)}catch(err){toast('Import failed: '+err.message)}
  e.target.value='';
 };
 window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue=''}});
}
async function init(){
 wire();createViewer();
 try{
  const [manif,open,creatorData]=await Promise.all([
   fetch('catalog/generated_manifest.json').then(r=>r.json()),
   fetch('catalog/open_3d_cc0.json').then(r=>r.json()),
   fetch('catalog/authorized_booths.json').then(r=>r.json())
  ]);
  state.sourceBases=(creatorData.assets||[]).filter(a=>a.is_full_booth&&a.license==='CC-BY-4.0'&&/^assets\/authorized-booths\/SKFB-[0-9a-f]{32}\.glb$/.test(a.glb)).map(a=>({
   id:a.id,name:a.name,creator:a.creator,source_url:a.source_url,license:a.license,
   is_creator_base:true,glb:a.glb,thumbnail:a.thumbnail,booth_type:'Designer original',
   style:'Artist-made',fitout:'Original',width_m:6,depth_m:6,area_m2:36
  }));
  state.bases=[...(manif.items||[]),...state.sourceBases];
  const select=$('originalDesign');
  for(const b of state.sourceBases){const opt=document.createElement('option');opt.value=b.id;opt.textContent=b.name+' — '+b.creator;select.append(opt)}
  state.assets=(open.assets||[]).filter(validAsset);
  $('assetCount').textContent=String(state.assets.length);
  const packs=new Map();
  for(const asset of state.assets)packs.set(asset.pack_slug,asset.pack);
  for(const [key,name] of packs){
   const opt=document.createElement('option');opt.value=key;opt.textContent=name;
   $('itemPack').append(opt);
  }
  renderItems();const preset=state.bases.find(x=>x.id===new URLSearchParams(location.search).get('design'));
  if(preset&&!preset.is_creator_base){for(const [field,value] of Object.entries({width:preset.width_m,depth:preset.depth_m,exposure:preset.booth_type,style:preset.style,fitout:preset.fitout}))$(UI[field]).value=String(value)}
  if(preset?.is_creator_base)$('originalDesign').value=preset.id;
  updateBasePreview();
  await loadBase(preset?.is_creator_base?preset:baseChoice(),{quiet:false});
  const chosenTab=new URLSearchParams(location.search).get('tab');
  if(['brand','items','export','base'].includes(chosenTab))switchTab(chosenTab);
 }catch(error){
  setStatus('Could not load the catalogues');$('loadingScene').querySelector('p').textContent=error.message;
  toast('Cannot load studio inventory: '+error.message);console.error(error);
 }
}
init();
