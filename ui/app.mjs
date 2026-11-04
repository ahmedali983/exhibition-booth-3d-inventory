import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { OBJExporter } from 'three/addons/exporters/OBJExporter.js';

const $=id=>document.getElementById(id);
const dom=(tag,className,text)=>{const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=text;return el};
const FIRST_LOAD=36,LOAD_MORE=48;
const state={
  all:[],sources:[],visible:[],sourceVisible:[],category:'all',sourceFilter:'all',
  page:'discover',sort:'curated',search:'',sourceSearch:'',pageSize:FIRST_LOAD,
  sourcePageSize:36,current:null,favorites:new Set(),brand:{name:'PAW CLUB',primary:'#ed714b',secondary:'#53d5b3',base:'light',logo:null}
};
let renderer,camera,scene,orbit,modelRoot,baseMaterials,logoMesh,animationId,activeLoad=0,toastTimer,viewerObserver;
try{
 const saved=JSON.parse(localStorage.getItem('expovault-v2-favorites')||'[]');
 if(Array.isArray(saved))state.favorites=new Set(saved);
 const brand=JSON.parse(localStorage.getItem('expovault-v2-brand')||'null');
 if(brand&&typeof brand==='object')state.brand={...state.brand,...brand};
}catch(_){}
function notify(message){const el=$('toast');el.textContent=message;el.classList.add('active');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('active'),3500)}
const safe=(val)=>String(val==null?'':val);
const pathFor= v=>'assets/thumbs/'+v.id+'.webp';
const nice=v=>v.style+' '+v.booth_type;
function saveState(){
 try{localStorage.setItem('expovault-v2-favorites',JSON.stringify([...state.favorites]));localStorage.setItem('expovault-v2-brand',JSON.stringify(state.brand))}catch(_){}
}
function populateFilters(){
 for(const [id,arr] of [['filterWidth',[3,4,5,6,8,10,12]],['filterDepth',[2,3,4,5,6,8]],['filterStyle',['Minimal','Portal','Truss','Feature Wall','Canopy']],['filterFitout',['Reception','Meeting','Retail','Digital','Storage']]]){
  const select=$(id);for(const value of arr){const opt=dom('option','',safe(value)+(typeof value==='number'?' m':''));opt.value=value;select.append(opt)}
  select.addEventListener('change',applyFilters);
 }
}
function order(a){
 const h=x=>{let n=(Number(x.id.split('-').pop())*2654435761)>>>0;n^=n>>>16;n=Math.imul(n,2246822507);return (n^(n>>>13))>>>0};
 switch(state.sort){
  case 'newest':return a.sort((v,w)=>w.id.localeCompare(v.id));
  case 'area':return a.sort((v,w)=>v.area_m2-w.area_m2||v.id.localeCompare(w.id));
  default:return a.sort((v,w)=>h(v)-h(w));
 }
}
function applyFilters(){
 const search=state.search.toLowerCase().trim();
 const width=$('filterWidth').value,depth=$('filterDepth').value,style=$('filterStyle').value,fit=$('filterFitout').value;
 state.visible=order(state.all.filter(v=>
  (state.category==='all'||v.booth_type===state.category||v.style===state.category)
  &&(!width||v.width_m===Number(width))
  &&(!depth||v.depth_m===Number(depth))
  &&(!style||v.style===style)
  &&(!fit||v.fitout===fit)
  &&(!search||(v.id+' '+nice(v)+' '+v.fitout+' '+v.width_m+'x'+v.depth_m+' '+v.area_m2+' sqm').toLowerCase().includes(search))
 ));
 state.pageSize=FIRST_LOAD;
 $('resultCount').textContent=state.visible.length.toLocaleString();
 $('filterBadge').classList.toggle('active',Boolean(width||depth||style||fit));
 renderGallery();
}
function makeCard(v){
 const card=dom('article','design-card');card.setAttribute('role','button');card.setAttribute('tabindex','0');card.setAttribute('aria-label','Open '+nice(v)+' '+v.width_m+' by '+v.depth_m+' metres');
 const image=dom('div','card-image');
 const img=dom('img');img.src=pathFor(v);img.loading='lazy';img.decoding='async';img.alt=nice(v)+' '+v.width_m+' × '+v.depth_m+' m exhibition stand visualization';
 img.onerror=()=>{img.onerror=null;img.src='assets/thumbs/EV-0001.webp'};
 image.append(img);
 const top=dom('div','card-topline'),tag=dom('span','card-tag',v.booth_type.toUpperCase()),heart=dom('button','heart-btn'+(state.favorites.has(v.id)?' saved':''),state.favorites.has(v.id)?'♥':'♡');
 heart.setAttribute('aria-label','Save '+v.id);heart.setAttribute('aria-pressed',state.favorites.has(v.id)?'true':'false');
 heart.onclick=e=>{e.stopPropagation();toggleFavorite(v.id);heart.classList.toggle('saved');heart.textContent=state.favorites.has(v.id)?'♥':'♡';heart.setAttribute('aria-pressed',state.favorites.has(v.id)?'true':'false')};
 top.append(tag,heart);image.append(top,dom('div','card-hover','✧ Open in 3D Studio  ↗'));card.append(image);
 const info=dom('div','card-info'),meta=dom('div','card-meta-top'),h3=dom('h3','',nice(v)),id=dom('small','',v.id);
 meta.append(h3,id);
 const subtitle=dom('p','card-subtitle',v.fitout+' fit-out · '+v.width_m+' × '+v.depth_m+' m · '+v.area_m2+' m²');
 const foot=dom('div','card-foot'),left=dom('span','', '▧ 3D + DXF'),right=dom('em','','EDITABLE');
 foot.append(left,right);info.append(meta,subtitle,foot);card.append(info);
 card.onclick=()=>openStudio(v);
 card.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openStudio(v)}};
 return card;
}
function renderGallery(append=false){
 const grid=$('galleryGrid');if(!append)grid.replaceChildren();
 const start=append?grid.children.length:0;
 const subset=state.visible.slice(start,state.pageSize);
 const frag=document.createDocumentFragment();
 for(const v of subset)frag.append(makeCard(v));
 grid.append(frag);
 $('galleryEmpty').hidden=state.visible.length!==0;
 $('galleryGrid').hidden=state.visible.length===0;
 $('loadMore').hidden=grid.children.length>=state.visible.length;
 $('feedProgress').textContent='Showing '+grid.children.length.toLocaleString()+' of '+state.visible.length.toLocaleString()+' concepts';
}
function toggleFavorite(id){
 state.favorites.has(id)?state.favorites.delete(id):state.favorites.add(id);
 $('savedCount').textContent=state.favorites.size;
 saveState();
 if(state.page==='saved')renderSaved();
 notify(state.favorites.has(id)?'Saved to your moodboard ♡':'Removed from saved board');
}
function renderSaved(){
 const host=$('savedGrid');host.replaceChildren();
 const ids=[...state.favorites],byid=new Map(state.all.map(x=>[x.id,x]));
 for(const id of ids){const item=byid.get(id);if(item)host.append(makeCard(item))}
 $('savedEmpty').hidden=host.children.length>0;
}
function switchPage(name,push=true){
 if(!['discover','sources','saved','brand'].includes(name))name='discover';
 state.page=name;for(const x of ['discover','sources','saved','brand'])$('page'+x[0].toUpperCase()+x.slice(1)).classList.toggle('is-active',x===name);
 document.querySelectorAll('.nav-link').forEach(el=>el.classList.toggle('is-active',el.dataset.page===name));
 $('breadcrumb').textContent=({discover:'Discover',sources:'Real-world models',saved:'Saved boards',brand:'Brand studio'})[name];
 $('searchInput').placeholder=name==='sources'?'Search creator models and sources...':'Search by style, size, layout, or ID...';
 $('searchInput').value=name==='sources'?state.sourceSearch:state.search;
 if(name==='sources')renderSources();if(name==='saved')renderSaved();if(name==='brand')fillBrandUI();
 if(push)history.replaceState(null,'','#'+name);
 window.scrollTo({top:0,behavior:'instant'});
 document.querySelector('.sidebar').classList.remove('mobile-open');
}
function normalizeSource(item){
 const val={...item};
 if(item.site==='Sketchfab'&&item.id&&item.id.startsWith('SKFB-')){
  const uid=item.id.slice(5);val.url='https://sketchfab.com/models/'+uid;
 }
 return val;
}
function applySourceFilters(){
 const query=state.sourceSearch.toLowerCase().trim();
 let sources=state.sources.filter(v=>{
  const match=(v.title+' '+(v.author||'')+' '+v.site+' '+(v.license||'')+' '+(v.format||'')).toLowerCase().includes(query);
  if(!match)return false;
  switch(state.sourceFilter){
   case 'Sketchfab':return v.site==='Sketchfab';
   case '3D Warehouse':return v.site==='3D Warehouse';
   case 'CAD':return /CAD|DXF|DWG|beMatrix|OCTA/i.test(v.title+' '+v.site+' '+v.format);
   case 'paid':return /ArtStation|Fab|paid|marketplace|Standard Use/i.test(v.site+' '+v.license+' '+v.status);
   default:return true;
  }
 });
 state.sourceVisible=sources;state.sourcePageSize=36;renderSources();
}
function makeSourceCard(v){
 const card=dom('article','design-card source-card');
 const image=dom('div','card-image');
 if(v.thumbnail){const img=dom('img');img.src=v.thumbnail;img.loading='lazy';img.decoding='async';img.alt='Original creator model '+v.title;img.referrerPolicy='no-referrer';img.onerror=()=>{img.remove();image.append(dom('div','placeholder-source','◈'))};image.append(img)}
 else image.append(dom('div','placeholder-source',v.site==='GitHub'?'⌘':v.site==='3D Warehouse'?'▣':'◈'));
 const top=dom('div','card-topline');top.append(dom('span','card-tag source-badge',v.site));image.append(top);card.append(image);
 const info=dom('div','card-info');const line=dom('div','card-meta-top'),h=dom('h3','',v.title);line.append(h);
 info.append(line,dom('p','card-subtitle',(v.author?'by '+v.author+' · ':'')+v.format));
 const foot=dom('div','card-foot');foot.append(dom('span','',v.license||'Check licence'),dom('em','','SOURCE ↗'));info.append(foot);card.append(info);
 card.setAttribute('role','link');card.setAttribute('tabindex','0');card.setAttribute('aria-label','Open original '+v.title);
 card.onclick=()=>window.open(v.url,'_blank','noopener,noreferrer');
 card.onkeydown=e=>{if(e.key==='Enter')card.click()};
 return card;
}
function renderSources(append=false){
 const grid=$('sourceGrid');if(!append)grid.replaceChildren();
 const frag=document.createDocumentFragment();
 for(const v of state.sourceVisible.slice(grid.children.length,state.sourcePageSize))frag.append(makeSourceCard(v));
 grid.append(frag);
 $('externalCount').textContent=state.sourceVisible.length.toLocaleString();
 $('sourceStat').textContent=state.sources.length.toLocaleString()+'+';
 $('sourceMore').hidden=grid.children.length>=state.sourceVisible.length;
 $('sourceProgress').textContent='Showing '+grid.children.length.toLocaleString()+' of '+state.sourceVisible.length.toLocaleString()+' original-source leads';
}
function renderSpotlight(){
 const grid=$('sourceSpotlight');if(!grid)return;
 grid.replaceChildren(...state.sources.filter(x=>x.thumbnail&&x.is_downloadable!==false).slice(0,8).map(makeSourceCard));
}
function fillBrandUI(){
 const b=state.brand;$('brandName').value=b.name;$('brandPrimary').value=b.primary;$('brandSecondary').value=b.secondary;$('brandBase').value=b.base;updateBrandPreview();
}
function readBrand(){
 state.brand.name=$('brandName').value.trim()||'YOUR BRAND';state.brand.primary=$('brandPrimary').value;state.brand.secondary=$('brandSecondary').value;state.brand.base=$('brandBase').value;
 saveState();updateBrandPreview();
}
function updateBrandPreview(){
 const b=state.brand;$('brandPrimaryLabel').textContent=b.primary.toUpperCase();$('brandSecondaryLabel').textContent=b.secondary.toUpperCase();
 $('brandPaletteName').textContent=b.name.toUpperCase();
 $('brandBigMark').innerHTML='';
 const content=document.createTextNode(b.name.toUpperCase().split(' ').join('\n'));
 $('brandBigMark').append(content,dom('span','','✳'));
 $('brandBigMark').style.whiteSpace='pre-line';$('brandBigMark').style.fontSize=b.name.length>12?'72px':'clamp(60px,9vw,115px)';
 $('brandPreview').style.background=b.primary;
 $('brandBigMark').style.color=b.base==='dark'?'#141719':'#fff';
}
function preset(name){
 const presets={paw:{name:'PAW CLUB',primary:'#ed714b',secondary:'#53d5b3',base:'light'},tech:{name:'TECH LAB',primary:'#0b737c',secondary:'#76d9c4',base:'dark'},luxe:{name:'NOIR',primary:'#171c25',secondary:'#e8ba7c',base:'dark'}};
 state.brand={...state.brand,...presets[name]};saveState();fillBrandUI();notify('Brand preset ready — open a booth to preview it');
}
function viewButton(view){
 document.querySelectorAll('.view-preset').forEach(el=>el.classList.toggle('active',el.dataset.view===view));
 if(!state.current||!camera||!orbit)return;
 const v=state.current;const reach=Math.max(v.width_m,v.depth_m)*1.7;
 if(view==='front')camera.position.set(0,2.4,reach*1.5);
 else if(view==='top')camera.position.set(0,reach*1.5,.001);
 else camera.position.set(reach*.88,reach*.68,reach);
 orbit.target.set(0,1.5,0);orbit.update();
}
function cancelViewer(){
 activeLoad++;
 if(animationId)cancelAnimationFrame(animationId);animationId=0;
 if(viewerObserver){viewerObserver.disconnect();viewerObserver=null}
 if(renderer){renderer.dispose();renderer.domElement.remove();renderer=null}
 if(orbit){orbit.dispose();orbit=null}
 modelRoot=null;scene=null;camera=null;logoMesh=null;
}
function closeStudio(){
 $('studioModal').hidden=true;$('modalBackdrop').hidden=true;document.body.style.overflow='';cancelViewer();
}
async function openStudio(v){
 if(!v)return;
 state.current=v;$('studioModal').hidden=false;$('modalBackdrop').hidden=false;document.body.style.overflow='hidden';
 $('modalTitle').textContent=nice(v)+' · '+v.width_m+' × '+v.depth_m+' m';
 $('modalSubtitle').textContent=v.fitout+' concept · '+v.area_m2+' m² footprint';
 $('designCode').textContent=v.id;
 const list=[['Footprint',v.width_m+' × '+v.depth_m+' m'],['Exposed sides',v.booth_type],['Style',v.style],['Layout',v.fitout],['Height','3.2 m'],['Area',v.area_m2+' m²']];
 $('designDetails').replaceChildren(...list.map(([key,val])=>{const item=dom('div','design-detail');item.append(dom('span','',key),dom('strong','',val));return item}));
 $('modalBrand').value=state.brand.name;$('modalColor').value=state.brand.primary;$('modalHex').textContent=state.brand.primary.toUpperCase();
 document.querySelectorAll('.base-swatch').forEach(x=>x.classList.toggle('active',x.dataset.base===state.brand.base));
 $('viewerLoading').hidden=false;$('downloadStatus').textContent='Loading actual GLB model...';
 await setupViewer(v);
}
function backdropColours(){
 const isDark=state.brand.base==='dark';
 if(scene)scene.background=new THREE.Color(isDark?'#232b31':'#e1e8e8');
}
async function setupViewer(v){
 const token=++activeLoad;cancelViewer();activeLoad=token;
 const host=$('threeViewport');host.querySelectorAll('canvas').forEach(c=>c.remove());
 scene=new THREE.Scene();backdropColours();
 camera=new THREE.PerspectiveCamera(43,1,.1,200);
 const gl=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
 renderer=gl;gl.setPixelRatio(Math.min(window.devicePixelRatio||1,2));gl.outputColorSpace=THREE.SRGBColorSpace;gl.shadowMap.enabled=true;
 host.prepend(gl.domElement);
 orbit=new OrbitControls(camera,gl.domElement);orbit.enableDamping=true;orbit.maxPolarAngle=Math.PI/2.07;
 scene.add(new THREE.HemisphereLight(0xffffff,0x617580,2.1));
 const lamp=new THREE.DirectionalLight(0xffffff,3.0);lamp.position.set(8,12,9);lamp.castShadow=true;lamp.shadow.mapSize.set(1024,1024);lamp.shadow.bias=-0.0003;lamp.shadow.normalBias=0.05;scene.add(lamp);
 const grid=new THREE.GridHelper(32,32,0xc6d0d1,0xd4dadb);grid.position.y=-.065;scene.add(grid);
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(100,100),new THREE.ShadowMaterial({opacity:.13}));floor.rotation.x=-Math.PI/2;floor.position.y=-.03;floor.receiveShadow=true;scene.add(floor);
 function resize(){if(!renderer||!camera||host.clientHeight===0)return;const w=host.clientWidth,h=host.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();gl.setSize(w,h,false)}
 const obs=new ResizeObserver(resize);viewerObserver=obs;obs.observe(host);
 function animate(){if(!renderer||token!==activeLoad){obs.disconnect();return}animationId=requestAnimationFrame(animate);orbit.update();gl.render(scene,camera)}
 resize();viewButton('perspective');animate();
 try{
  const result=await new GLTFLoader().loadAsync(v.glb);
  if(token!==activeLoad){obs.disconnect();return}
  modelRoot=result.scene;modelRoot.name=v.id+' booth';scene.add(modelRoot);
  modelRoot.traverse(node=>{if(node.isMesh){node.castShadow=true;node.receiveShadow=false;node.material=node.material.clone()}});
  applyMaterials();makeBrandSign();applyBrandSign();viewButton('perspective');
  $('viewerLoading').hidden=true;$('downloadStatus').textContent='GLB mesh loaded · customize and export';
 }catch(err){$('viewerLoading').textContent='Could not load 3D: '+err.message;$('downloadStatus').textContent='Model unavailable';console.error(err)}
}
function applyMaterials(){
 if(!modelRoot)return;
 const white=state.brand.base!=='dark';
 backdropColours();
 modelRoot.traverse(node=>{
  if(!node.isMesh)return;
  const m=node.material;const name=(m.name||'').toLowerCase();
  if(name.includes('palette_0'))m.color.set(white?'#f7f6f0':'#21252b');
  if(name.includes('palette_1'))m.color.set(state.brand.primary);
  if(name.includes('palette_2'))m.color.set(white?'#e6dfd3':'#30353b');
  if(name.includes('palette_4'))m.color.set(state.brand.secondary);
 });
}
function makeBrandSign(){
 if(!modelRoot||!state.current)return;
 const v=state.current;
 logoMesh=new THREE.Mesh(new THREE.PlaneGeometry(Math.min(v.width_m*.79,3.7),.6),new THREE.MeshBasicMaterial({color:0xffffff,side:THREE.DoubleSide}));
 logoMesh.name='Editable brand artwork';
 const z=v.booth_type==='Island'?.33:-v.depth_m/2+(v.style==='Feature Wall'?.78:.30);
 logoMesh.position.set(0,v.booth_type==='Island'?1.75:2.86,z);
 modelRoot.add(logoMesh);
}
async function applyBrandSign(){
 if(!logoMesh)return;
 const cvs=document.createElement('canvas');cvs.width=1024;cvs.height=210;const cx=cvs.getContext('2d');
 cx.fillStyle=state.brand.base==='dark'?'#1c2429':'#ffffff';cx.fillRect(0,0,1024,210);
 cx.fillStyle=state.brand.primary;cx.fillRect(0,0,16,210);cx.fillRect(1008,0,16,210);
 const logoData=state.brand.logo;
 if(logoData){const img=new Image();img.onload=()=>{const scale=Math.min(260/img.width,150/img.height);const w=img.width*scale,h=img.height*scale;cx.drawImage(img,52,30,w,h);drawText(350,650);updateTexture()};img.onerror=()=>{drawText(0,1000);updateTexture()};img.src=logoData}
 else{drawText(0,1000);updateTexture()}
 function drawText(start,width){cx.fillStyle=state.brand.base==='dark'?'#f5f7f4':'#182022';cx.textAlign='center';cx.textBaseline='middle';cx.font='bold 95px Arial,sans-serif';cx.fillText(state.brand.name.toUpperCase().slice(0,23),start+width/2,107,width-60)}
 function updateTexture(){if(!logoMesh)return;const tex=new THREE.CanvasTexture(cvs);tex.colorSpace=THREE.SRGBColorSpace;if(logoMesh.material.map)logoMesh.material.map.dispose();logoMesh.material.map=tex;logoMesh.material.color.set('white');logoMesh.material.needsUpdate=true}
}
function setBase(base){
 state.brand.base=base;saveState();document.querySelectorAll('.base-swatch').forEach(x=>x.classList.toggle('active',x.dataset.base===base));applyMaterials();applyBrandSign();
}
function syncModalBrand(){
 state.brand.primary=$('modalColor').value;state.brand.name=$('modalBrand').value.trim()||'YOUR BRAND';
 $('modalHex').textContent=state.brand.primary.toUpperCase();saveState();applyMaterials();applyBrandSign();
}
function saveBlob(name,bytes,type){
 const b=bytes instanceof Blob?bytes:new Blob([bytes],{type:type||'application/octet-stream'});
 const url=URL.createObjectURL(b);const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
function exportGLB(){
 return new Promise((resolve,reject)=>{
  if(!modelRoot)return reject(new Error('3D geometry has not loaded'));
  const exporter=new GLTFExporter();
  exporter.parse(modelRoot,data=>resolve(data),reject,{binary:true,onlyVisible:true,maxTextureSize:1024});
 });
}
function exportOBJ(){
 if(!modelRoot)throw Error('3D geometry has not loaded');
 return new OBJExporter().parse(modelRoot);
}
async function fetchPlan(){
 const response=await fetch(state.current.dxf);if(!response.ok)throw Error('2D DXF not available');return await response.text();
}
function escapeXml(str){return safe(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;')}
function calculatePanels(v){
 const sides=[{side:'back',span_m:v.width_m,enabled:v.booth_type!=='Island'}];
 if(v.booth_type==='Inline'||v.booth_type==='Corner')sides.push({side:'left',span_m:v.depth_m,enabled:true});
 if(v.booth_type==='Inline')sides.push({side:'right',span_m:v.depth_m,enabled:true});
 return sides.filter(x=>x.enabled).flatMap(side=>{
  const qty=Math.ceil(side.span_m/1);
  return Array.from({length:qty},(_,i)=>({side:side.side,index:i+1,nominal_w_mm:Math.round(1000*Math.min(1,side.span_m-i)),nominal_h_mm:3200,
   cut_w_mm:Math.round(1000*Math.min(1,side.span_m-i))+20,cut_h_mm:3220,artwork_w_mm:Math.round(1000*Math.min(1,side.span_m-i))+40,artwork_h_mm:3240}));
 });
}
function printSvg(panel,v){
 const artW=panel.artwork_w_mm,artH=panel.artwork_h_mm,pad=10,cutW=panel.cut_w_mm,cutH=panel.cut_h_mm;
 const name=escapeXml(state.brand.name),side=escapeXml(panel.side);
 return '<svg xmlns="http://www.w3.org/2000/svg" width="'+artW+'mm" height="'+artH+'mm" viewBox="0 0 '+artW+' '+artH+'">'+
 '<title>'+escapeXml(v.id)+' · '+side+' panel '+panel.index+' · artwork guide only</title>'+
 '<desc>PRELIMINARY ARTWORK PLACEMENT TEMPLATE. Confirm actual frame visible size, bleed and printer requirements. RGB colours are NOT CMYK print-ready.</desc>'+
 '<rect width="100%" height="100%" fill="'+(state.brand.base==='dark'?'#1f2528':'#ffffff')+'"/>'+
 '<rect x="'+pad+'" y="'+pad+'" width="'+cutW+'" height="'+cutH+'" fill="none" stroke="#ff2e2e" stroke-width="2" stroke-dasharray="20 12"/>'+
 '<rect x="30" y="30" width="'+(artW-60)+'" height="'+(artH-60)+'" fill="none" stroke="#0090c2" stroke-width="2" stroke-dasharray="9 8"/>'+
 '<rect x="0" y="0" width="'+artW+'" height="90" fill="'+state.brand.primary+'"/>'+
 '<text x="'+artW/2+'" y="'+Math.min(artH*.4,1050)+'" font-family="Arial" font-size="'+Math.min(135,artW/8)+'" text-anchor="middle" fill="'+(state.brand.base==='dark'?'#ffffff':'#242b2b')+'" font-weight="bold">'+name+'</text>'+
 '<text x="'+artW/2+'" y="'+(artH-70)+'" font-family="Arial" font-size="31" text-anchor="middle" fill="'+(state.brand.base==='dark'?'#ffffff':'#333333')+'">'+escapeXml(v.id+' '+side.toUpperCase()+' PANEL '+panel.index)+'</text>'+
 '<text x="'+artW/2+'" y="'+(artH-30)+'" font-family="Arial" font-size="20" text-anchor="middle" fill="#e03d3d">CONCEPT GUIDE — NOT PRINT-READY</text>'+
 '</svg>';
}
function bomFor(v,panels){
 const rows=[
 ['ITEM','DESCRIPTION','QUANTITY','UNIT','DIMENSION','STATUS'],
 ['001','Floor platform / conceptual footprint',1,'set',v.width_m+' x '+v.depth_m+' m','Concept estimate'],
 ['002','Wall panels',panels.length,'panels','individual sizes in panel_schedule.csv','Geometry only'],
 ['003','Wall support / frame profiles',panels.length*2,'approx pcs','3.2 m vertical','Supplier selection required'],
 ['004','Corner connectors',v.booth_type==='Inline'?8:v.booth_type==='Corner'?4:0,'approx pcs','system dependent','Unverified'],
 ];
 if(['Portal','Canopy'].includes(v.style))rows.push(['005','Front portal structure',3,'segments','to design','ENGINEER APPROVAL REQUIRED']);
 if(v.style==='Truss')rows.push(['006','Truss superstructure',1,'system','to design','RIGGING ENGINEER REQUIRED']);
 if(v.style==='Feature Wall')rows.push(['007','Feature wall / shelving',1,'assembly','to design','Unverified']);
 if(v.fitout==='Reception')rows.push(['008','Reception desk',1,'piece','approx 1.7 x 0.66 m','Concept']);
 if(v.fitout==='Meeting')rows.push(['009','Meeting table & seating',1,'set','to design','Concept']);
 if(v.fitout==='Digital')rows.push(['010','Digital screen',1,'item','up to 3.28 x 1.43 m mock','Electrical plan required']);
 if(v.fitout==='Retail')rows.push(['011','Display plinths',3,'pieces','approx 0.8 x 0.68 m','Concept']);
 return rows.map(row=>row.map(x=>'"'+safe(x).replace(/"/g,'""')+'"').join(',')).join('\r\n')+'\r\n';
}
function panelCsv(panels){return [['SIDE','PANEL','NOMINAL_WIDTH_MM','NOMINAL_HEIGHT_MM','ASSUMED_CUT_W_MM','ASSUMED_CUT_H_MM','ART_W_MM','ART_H_MM','STATUS'],...panels.map(p=>[p.side,p.index,p.nominal_w_mm,p.nominal_h_mm,p.cut_w_mm,p.cut_h_mm,p.artwork_w_mm,p.artwork_h_mm,'PRELIMINARY ONLY'])].map(row=>row.join(',')).join('\r\n')+'\r\n'}
function notes(v){
 return '# EXPOVAULT / '+v.id+' — CONCEPT PRODUCTION HANDOFF\n\n'+
 '## Model\n'+nice(v)+' · '+v.width_m+' × '+v.depth_m+' metres · '+v.fitout+'\n\n'+
 '## File contents\n- model/booth.glb: true GLB 2.0 triangulated 3D geometry with selected palette and brand sign\n'+
 '- model/booth.obj: same 3D concept as editable mesh, although OBJ has limited material/texture portability\n'+
 '- drawings/floorplan.dxf: 2D footprint, dimensions and conceptual partitions\n'+
 '- panels/*.svg: one scalable vector artwork placement guide per panel (not calibrated for any specific printer)\n'+
 '- panel_schedule.csv: estimated nominal, cut and artwork dimensions\n'+
 '- bom_estimate.csv: conceptual material list, not supplier purchase order\n'+
 '- specification.json: filters and chosen brand colours\n\n'+
 '## Never send directly to fabrication\nThis package is NOT a final production specification, cut sheet, assembly instruction or structural approval.\n'+
 'All profile lengths, wall thickness, artwork bleeds, print colour, finishing, truss, loads, joints, access, electric power, fire codes and manufacturer tooling MUST be checked by a qualified booth contractor.\n'+
 'For manufacturer-backed production, see source links for beMatrix beCAD, OCTANORM OCTAcad and suppliers in the Source Gallery.\n\n'+
 'All 3D procedural concepts in this pack are ExpoVault original geometry. No external creator assets are included.\n';
}
async function productionZip(){
 if(!state.current||!modelRoot){notify('Open a loaded 3D model first');return}
 const button=$('downloadProduction');button.disabled=true;button.textContent='Preparing pack…';$('downloadStatus').textContent='Building GLB, OBJ, DXF and SVG sheets';
 try{
  if(!window.JSZip)throw Error('The ZIP library could not load; check your internet connection.');
  const v=state.current,zip=new window.JSZip(),panels=calculatePanels(v);
  const [glb,dxf]=await Promise.all([exportGLB(),fetchPlan()]);
  zip.file('model/booth.glb',glb);zip.file('model/booth.obj',exportOBJ());zip.file('drawings/floorplan.dxf',dxf);
  for(const p of panels)zip.file('panels/'+p.side+'-'+String(p.index).padStart(2,'0')+'.svg',printSvg(p,v));
  zip.file('panel_schedule.csv',panelCsv(panels));zip.file('bom_estimate.csv',bomFor(v,panels));
  zip.file('specification.json',JSON.stringify({...v,brand:state.brand,source:'ExpoVault procedural geometry',approval:'NOT APPROVED FOR FABRICATION'},null,2));
  zip.file('README_CONCEPT_HANDOFF.md',notes(v));
  const archive=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:6}});
  saveBlob(v.id+'-'+state.brand.name.toLowerCase().replace(/\W+/g,'-')+'-concept-production.zip',archive);
  $('downloadStatus').textContent='Pack exported · supplier verification required';notify('Your 3D + DXF + SVG production-concept pack is ready');
 }catch(err){$('downloadStatus').textContent='Could not create the ZIP';notify(err.message);console.error(err)}
 finally{button.disabled=false;button.textContent='↓ Download concept production ZIP'}
}
function hookEvents(){
 document.querySelectorAll('[data-page]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();switchPage(el.dataset.page)}));
 document.querySelectorAll('[data-open-id]').forEach(el=>el.onclick=()=>openStudio(state.all.find(v=>v.id===el.dataset.openId)));
 $('mobileMenu').onclick=()=>document.querySelector('.sidebar').classList.toggle('mobile-open');
 $('searchInput').addEventListener('input',e=>{if(state.page==='sources'){state.sourceSearch=e.target.value;applySourceFilters()}else{state.search=e.target.value;if(state.page!=='discover')switchPage('discover');applyFilters()}});
 document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('searchInput').focus()}if(e.key==='Escape'){if(!$('studioModal').hidden)closeStudio();else document.querySelector('.sidebar').classList.remove('mobile-open')}});
 $('exploreBtn').onclick=()=>$('collection').scrollIntoView({behavior:'smooth',block:'start'});
 for(const btn of document.querySelectorAll('.category'))btn.onclick=()=>{state.category=btn.dataset.category;document.querySelectorAll('.category').forEach(x=>x.classList.toggle('active',x===btn));applyFilters()};
 const sortButtons=[['sortTrending','curated'],['sortNewest','newest'],['sortArea','area']];
 for(const [id,sort] of sortButtons)$(id).onclick=()=>{state.sort=sort;sortButtons.forEach(([k])=>$(k).classList.toggle('active',k===id));applyFilters()};
 $('filtersToggle').onclick=()=>$('filtersDrawer').hidden=!$('filtersDrawer').hidden;
 for(const reset of ['resetFilters','emptyReset'])$(reset).onclick=()=>{state.category='all';for(const id of ['filterWidth','filterDepth','filterStyle','filterFitout'])$(id).value='';state.search='';$('searchInput').value='';document.querySelectorAll('.category').forEach(x=>x.classList.toggle('active',x.dataset.category==='all'));applyFilters()};
 $('loadMore').onclick=()=>{state.pageSize+=LOAD_MORE;renderGallery(true)};
 $('sourceMore').onclick=()=>{state.sourcePageSize+=48;renderSources(true)};
 document.querySelectorAll('.source-tab').forEach(btn=>btn.onclick=()=>{state.sourceFilter=btn.dataset.sourceFilter;document.querySelectorAll('.source-tab').forEach(x=>x.classList.toggle('active',x===btn));applySourceFilters()});
 $('sourcesSearch').oninput=e=>{state.sourceSearch=e.target.value;applySourceFilters()};
 for(const id of ['brandName','brandPrimary','brandSecondary','brandBase'])$(id).addEventListener('input',readBrand);
 $('brandLogo').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;
  if(file.size>1024*1024){notify('Please use a logo smaller than 1 MB');return}
  state.brand.logo=await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(file)});
  saveState();notify('Brand logo loaded — open a 3D model to preview');
 };
 document.querySelectorAll('[data-preset]').forEach(el=>el.onclick=()=>preset(el.dataset.preset));
 $('brandApply').onclick=()=>{readBrand();switchPage('discover');notify('Brand kit saved — open any model to apply it')};
 $('closeModal').onclick=closeStudio;$('modalBackdrop').onclick=closeStudio;
 $('modalColor').oninput=syncModalBrand;$('modalBrand').onchange=syncModalBrand;
 document.querySelectorAll('.base-swatch').forEach(el=>el.onclick=()=>setBase(el.dataset.base));
 document.querySelectorAll('.view-preset').forEach(el=>el.onclick=()=>viewButton(el.dataset.view));
 $('downloadGLB').onclick=async()=>{try{const binary=await exportGLB();saveBlob(state.current.id+'-branded.glb',binary);notify('Branded GLB exported')}catch(err){notify(err.message)}};
 $('downloadOBJ').onclick=()=>{try{saveBlob(state.current.id+'.obj',exportOBJ(),'text/plain');notify('OBJ geometry exported')}catch(err){notify(err.message)}};
 $('downloadDXF').onclick=async()=>{try{saveBlob(state.current.id+'.dxf',await fetchPlan(),'application/dxf');notify('DXF concept floor plan exported')}catch(err){notify(err.message)}};
 $('downloadProduction').onclick=productionZip;
 window.addEventListener('hashchange',()=>{const slug=location.hash.replace('#','');if(['discover','sources','saved','brand'].includes(slug)&&state.page!==slug)switchPage(slug,false)});
}
async function initialize(){
 populateFilters();hookEvents();$('savedCount').textContent=state.favorites.size;fillBrandUI();
 try{
  const response=await fetch('catalog/generated_manifest.json');
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();
  state.all=data.items||[];applyFilters();
 }catch(err){console.error(err);$('resultCount').textContent='Unavailable';notify('Could not load catalogue: '+err.message)}
 try{
  const [a,b,c]=await Promise.all([fetch('catalog/sources.json'),fetch('catalog/sketchfab_index.json'),fetch('catalog/creator_discovery.json')]);
  const manual=a.ok?await a.json():[],automated=b.ok?(await b.json()).items||[]:[],extra=c.ok?(await c.json()).items||[]:[];
  const seen=new Set();for(const row of [...manual,...automated,...extra]){const v=normalizeSource(row);const key=v.site==='Sketchfab'&&v.id&&v.id.startsWith('SKFB-')?v.id:v.url;if(seen.has(key))continue;seen.add(key);state.sources.push(v)}
  state.sources.sort((a,b)=>Number(b.view_count||0)-Number(a.view_count||0));
  applySourceFilters();renderSpotlight();
 }catch(err){console.warn('Sources not loaded',err);notify('External sources temporarily unavailable')}
 const route=location.hash.replace('#','');
 switchPage(['discover','sources','saved','brand'].includes(route)?route:'discover',false);
}
initialize();
