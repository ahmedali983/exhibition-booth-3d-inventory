const $=id=>document.getElementById(id);
const create=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=String(text);return el};
const STATE={models:[],concepts:[],technical:[],section:'models',search:{models:'',concepts:'',technical:''},kind:'all',availability:'any',licence:'any',sort:'relevant',modelsFiltered:[],conceptsFiltered:[],modelsShow:28,conceptsShow:28,active:null,position:0,fromSaved:false,saved:new Set()};
const PROFILE='https://sketchfab.com/';
let noticeTimer=0;
try{const entries=JSON.parse(localStorage.getItem('expovault-v3-saved')||'[]');if(Array.isArray(entries))STATE.saved=new Set(entries)}catch(_){}
function toast(message){const box=$('toast');box.textContent=message;box.classList.add('visible');clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>box.classList.remove('visible'),3200)}
function persistSaved(){try{localStorage.setItem('expovault-v3-saved',JSON.stringify([...STATE.saved]));}catch(_){}$('sideSaved').textContent=STATE.saved.size}
function number(x){return(Number(x||0)).toLocaleString('en-US')}
function validHttp(url,allowed=[]){
 try{const p=new URL(url);if(p.protocol!=='https:')return null;if(allowed.length&&!allowed.some(d=>p.hostname===d||p.hostname.endsWith('.'+d)))return null;return p.href}catch(_){return null}
}
function uidFor(v){const m=/^SKFB-([0-9A-Za-z]{20,40})$/.exec(v?.id||'');return m?m[1]:null}
function category(v){
 const t=(v.title||'').toLowerCase();
 if(/\b(exhibition booth|exhibition stand|exhibition stall|expo booth|expo stand|trade.?show booth|tradeshow stand|trade fair stand|stand design|booth design|exhibit booth|exhib.?stand|exhibition design|event booth)\b/.test(t))return'booth';
 if(/\b(pavilion|exhibition hall|expo hall|gallery|showroom|museum exhibit|exhibition room|convention hall)\b/.test(t))return'pavilion';
 if(/\b(display|showcase|kiosk|counter|truss|retail stand|exhibition furniture|octanorm)\b/.test(t))return'display';
 if(/\b(event|stage|festival|fairground|trade fair|exhibition|expo|exhibit|stand)\b/.test(t))return'event';
 return'other';
}
function score(v){
 const t=(v.title||'').toLowerCase();
 let score={booth:120,pavilion:65,display:50,event:35,other:0}[v.category];
 if(/exhibition (booth|stand|stall)/.test(t))score+=30;
 if(/trade.?show (booth|stand)|modular|island booth|shell scheme/.test(t))score+=18;
 if(/3d|booth|exhibition|expo/.test(t))score+=6;
 if(/restaurant|dj booth|anime expo|toy|character|game/.test(t))score-=45;
 if(v.is_downloadable)score+=7;
 score+=Math.min(17,Math.log10(1+(v.view_count||0))*3);
 return score;
}
function sectionTitle(s){return({models:'3D designs',concepts:'Booth studio',technical:'Production toolkit',saved:'My collection'})[s]}
function setSection(name,{changeHash=true,scroll=true}={}){
 if(!['models','concepts','technical','saved'].includes(name))name='models';
 STATE.section=name;
 for(const s of ['models','concepts','technical','saved'])$('section-'+s).classList.toggle('active',s===name);
 document.querySelectorAll('[data-section]').forEach(btn=>btn.classList.toggle('selected',btn.dataset.section===name&&btn.classList.contains('side-link')));
 $('breadcrumb').textContent=sectionTitle(name);
 $('query').placeholder=name==='models'?'Search exhibition stands or creators...':name==='concepts'?'Search by size, structure or ID...':name==='technical'?'Search DWG, CAD or 3D sources...':'Search your saved assets...';
 $('query').value=STATE.search[name]||'';
 if(name==='saved')renderSaved();
 if(name==='technical')renderTechnical();
 if(changeHash)history.replaceState(null,'','#'+name);
 $('side').classList.remove('mobile-show');
 if(scroll)window.scrollTo({top:0,behavior:'instant'});
}
function resetModelFilters(){
 STATE.search.models='';STATE.kind='all';STATE.availability='any';STATE.licence='any';STATE.sort='relevant';
 $('query').value='';$('availability').value='any';$('modelLicence').value='any';$('modelSort').value='relevant';
 document.querySelectorAll('.chip').forEach(b=>b.classList.toggle('active',b.dataset.kind==='all'));
 runModelFilters();
}
function runModelFilters(){
 const q=STATE.search.models.toLowerCase().trim();
 let items=STATE.models.filter(v=>
   (STATE.kind==='all'||v.category===STATE.kind)
   &&(STATE.availability==='any'||(STATE.availability==='download'?v.is_downloadable:!v.is_downloadable))
   &&(STATE.licence==='any'||(STATE.licence==='cc'&&/CC|Creative Commons/i.test(v.license))||(STATE.licence==='noncommercial'&&/NonCommercial|NC\b/i.test(v.license))||(STATE.licence==='unspecified'&&!/CC|Creative Commons/i.test(v.license)))
   &&(!q||(v.title+' '+v.author+' '+v.license+' '+v.category).toLowerCase().includes(q))
 );
 switch(STATE.sort){
  case 'views':items.sort((a,b)=>(b.view_count||0)-(a.view_count||0));break;
  case 'new':items.sort((a,b)=>String(b.published_at||'').localeCompare(String(a.published_at||'')));break;
  case 'az':items.sort((a,b)=>a.title.localeCompare(b.title));break;
  default:items.sort((a,b)=>b.relevance-a.relevance);break;
 }
 STATE.modelsFiltered=items;STATE.modelsShow=28;renderModels();
 $('modelCount').textContent=number(items.length);
 $('filterDot').classList.toggle('active',STATE.availability!=='any'||STATE.licence!=='any');
}
function favoriteButton(v){
 const saved=STATE.saved.has(v.id);
 const heart=create('button','save-button'+(saved?' saved':''),saved?'♥':'♡');
 heart.setAttribute('aria-label',saved?'Remove from saved':'Save model');
 heart.setAttribute('aria-pressed',String(saved));heart.title=saved?'Remove from collection':'Add to collection';
 heart.onclick=e=>{e.stopPropagation();toggleSave(v.id);heart.textContent=STATE.saved.has(v.id)?'♥':'♡';heart.classList.toggle('saved',STATE.saved.has(v.id));heart.setAttribute('aria-pressed',String(STATE.saved.has(v.id)))};
 return heart;
}
function openDownloadCenter(v){
 if(!v?.is_downloadable)return toast('Creator does not offer the original model for download.');
 window.dispatchEvent(new CustomEvent('expovault:download-open',{detail:{
  uid:uidFor(v),id:v.id,title:v.title,author:v.author||'Original creator',
  license:v.license||'Unspecified',source:'https://sketchfab.com/models/'+uidFor(v)
 }}));
}
function toggleSave(id){
 if(STATE.saved.has(id))STATE.saved.delete(id);else STATE.saved.add(id);
 persistSaved();toast(STATE.saved.has(id)?'Added to your design collection':'Removed from your collection');
 if(STATE.section==='saved')renderSaved();
}
function thumbnail(src,alt){
 const img=create('img');img.alt=alt;img.loading='lazy';img.decoding='async';img.referrerPolicy='strict-origin-when-cross-origin';img.src=src;
 img.onerror=()=>{const parent=img.parentElement;if(parent)parent.insertBefore(create('div','model-thumb-fallback','◇'),img);img.remove()};
 return img;
}
function makeOriginalCard(v){
 const card=create('article','model-card');card.tabIndex=0;card.setAttribute('role','button');card.setAttribute('aria-label','Open embedded 3D preview of '+v.title);
 const visual=create('div','model-thumb');const fallback=create('div','model-thumb-fallback','◇');
 const imgSrc=validHttp(v.thumbnail,['sketchfab.com','cloudfront.net']);
 if(imgSrc)visual.append(thumbnail(imgSrc,v.title));else visual.append(fallback);
 const top=create('div','thumb-top'),downloadable=v.is_downloadable;
 top.append(create('span','mini-label'+(downloadable?' download':''),downloadable?'3D + DOWNLOAD':'LIVE 3D'),favoriteButton(v));visual.append(top,create('div','thumb-overlay','◈ Explore interactive 3D ↗'));
 const body=create('div','card-text');body.append(create('h3','',v.title),create('div','card-author','by '+(v.author||'Original creator')));
 const bottom=create('div','card-bottom');bottom.append(create('span','',number(v.view_count)+' views'),create('b',v.category==='other'?'muted-badge':'',v.category==='booth'?'EXHIBITION':v.category==='pavilion'?'PAVILION':v.category==='display'?'DISPLAY':v.category==='event'?'EVENT':'RELATED'));
 body.append(bottom);
 if(v.is_downloadable){
  const control=create('button','inline-download','↓ Download 3D');
  control.setAttribute('aria-label','Download authorized 3D files for '+v.title);
  control.onclick=e=>{e.stopPropagation();openDownloadCenter(v)};
  body.append(control);
 }
 card.append(visual,body);
 card.onclick=()=>openOriginal(v);
 card.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openOriginal(v)}};
 return card;
}
function renderModels(append=false){
 const host=$('modelGrid');if(!append)host.replaceChildren();
 const frag=document.createDocumentFragment();
 for(const item of STATE.modelsFiltered.slice(host.children.length,STATE.modelsShow))frag.append(makeOriginalCard(item));
 host.append(frag);
 $('modelEmpty').hidden=STATE.modelsFiltered.length!==0;
 $('moreModels').hidden=host.children.length>=STATE.modelsFiltered.length;
 $('modelProgress').textContent='Showing '+number(host.children.length)+' of '+number(STATE.modelsFiltered.length)+' original source records';
}
function makeConceptCard(v){
 const card=create('article','model-card concept-card');card.tabIndex=0;card.setAttribute('role','button');card.setAttribute('aria-label','Open editable concept '+v.id);
 const visual=create('div','model-thumb');visual.append(thumbnail('assets/thumbs/'+v.id+'.webp',v.style+' '+v.booth_type));
 const head=create('div','thumb-top');head.append(create('span','mini-label',v.width_m+' × '+v.depth_m+' M'),favoriteButton(v));
 visual.append(head,create('div','thumb-overlay','✧ Open branded 3D studio ↗'));
 const body=create('div','card-text');body.append(create('h3','',v.style+' '+v.booth_type),create('div','card-author',v.fitout+' · '+v.area_m2+' m² · '+v.id));
 const bottom=create('div','card-bottom');bottom.append(create('span','','GLB + DXF'),create('b','','CUSTOMIZABLE'));body.append(bottom);
 const direct=create('div','concept-downloads');
 for(const [format,ext] of [['Download GLB','glb'],['Download DXF','dxf']]){
  const a=create('a','',format);a.href='assets/generated/'+v.width_m+'x'+v.depth_m+'/'+v.id+'.'+ext;
  a.download=v.id+'.'+ext;
  a.onclick=e=>e.stopPropagation();
  direct.append(a);
 }
 body.append(direct);card.append(visual,body);
 const open=()=>{window.location.href='studio.html?design='+encodeURIComponent(v.id)};
 card.onclick=open;card.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}};
 return card;
}
function runConceptFilters(){
 const w=$('conceptWidth').value,d=$('conceptDepth').value,s=$('conceptStyle').value,t=$('conceptType').value,q=STATE.search.concepts.toLowerCase().trim();
 STATE.conceptsFiltered=STATE.concepts.filter(v=>(!w||v.width_m===+w)&&(!d||v.depth_m===+d)&&(!s||v.style===s)&&(!t||v.booth_type===t)&&(!q||(v.id+' '+v.style+' '+v.booth_type+' '+v.fitout+' '+v.width_m+'x'+v.depth_m).toLowerCase().includes(q)));
 STATE.conceptsShow=28;renderConcepts();
 $('conceptCount').textContent=number(STATE.conceptsFiltered.length);
}
function renderConcepts(append=false){
 const host=$('conceptGrid');if(!append)host.replaceChildren();const frag=document.createDocumentFragment();
 for(const v of STATE.conceptsFiltered.slice(host.children.length,STATE.conceptsShow))frag.append(makeConceptCard(v));
 host.append(frag);$('moreConcepts').hidden=host.children.length>=STATE.conceptsFiltered.length;
 $('conceptProgress').textContent='Showing '+number(host.children.length)+' of '+number(STATE.conceptsFiltered.length)+' editable 3D files';
}
function renderTechnical(){
 const term=($('technicalQuery').value||STATE.search.technical||'').toLowerCase().trim();const items=STATE.technical.filter(x=>!term||(x.title+' '+x.notes+' '+x.format+' '+x.site).toLowerCase().includes(term));
 const host=$('referenceGrid');host.replaceChildren();$('technicalCount').textContent=number(items.length);
 for(const v of items){
  const link=create('a','reference-card');link.href=validHttp(v.url)||'#';link.target='_blank';link.rel='noopener noreferrer';
  link.append(create('div','reference-label',v.site.toUpperCase()),create('h3','',v.title),create('p','',v.notes||'Original external production reference'));
  const foot=create('div','reference-foot');foot.append(create('span','',v.format||v.license||'Original source'),create('strong','','Open source ↗'));link.append(foot);host.append(link);
 }
}
function renderSaved(){
 const host=$('savedGrid');host.replaceChildren();const modelMap=new Map(STATE.models.map(x=>[x.id,x])),conceptMap=new Map(STATE.concepts.map(x=>[x.id,x]));
 for(const id of STATE.saved){const v=modelMap.get(id)||conceptMap.get(id);if(!v)continue;host.append(id.startsWith('SKFB-')?makeOriginalCard(v):makeConceptCard(v))}
 $('savedEmpty').hidden=host.children.length>0;
}
function activeList(){
 const list=STATE.fromSaved?STATE.models.filter(x=>STATE.saved.has(x.id)):STATE.modelsFiltered;
 return list.length?list:STATE.models;
}
function openOriginal(v,{hash=true,fromSaved=false}={}){
 if(!v||!uidFor(v))return toast('This original source is not available for embedding');
 STATE.active=v;STATE.fromSaved=fromSaved||STATE.section==='saved';
 const list=activeList();STATE.position=list.findIndex(x=>x.id===v.id);if(STATE.position<0)STATE.position=0;
 $('viewer').hidden=false;$('viewerOverlay').hidden=false;document.body.style.overflow='hidden';
 $('viewerTitle').textContent=v.title;$('viewerAuthor').textContent=v.author||'Original creator';
 $('viewerAuthor').href=validHttp(v.author_url,['sketchfab.com'])||PROFILE+encodeURIComponent(v.author||'');
 $('detailDownload').textContent=v.is_downloadable?'With creator permission':'Preview only';
 $('downloadExternal').disabled=!v.is_downloadable;
 $('downloadExternal').textContent=v.is_downloadable?'↓ Download licensed 3D':'View-only model · no file';
 $('downloadAvailability').textContent=v.is_downloadable?'Eligible for sign-in':'No public download';
 $('downloadExternalHint').textContent=v.is_downloadable?'Use the official embedded sign-in to request this model’s glTF ZIP and textures. Current access is checked at download time.':'This model’s original mesh is not offered for public download. Create a separate editable concept in Booth Studio.';
 $('detailKind').textContent=v.category.toUpperCase();
 $('detailLicense').textContent=v.license||'Not specified';
 $('detailViews').textContent=number(v.view_count)+' views';
 $('originalLink').href=PROFILE+'models/'+uidFor(v);
 const image=$('detailCover');image.replaceChildren();const src=validHttp(v.thumbnail,['sketchfab.com','cloudfront.net']);if(src)image.append(thumbnail(src,v.title));
 $('viewerSave').textContent=(STATE.saved.has(v.id)?'♥ Saved':'♡ Save');
 $('modelPosition').textContent=number(STATE.position+1)+' / '+number(list.length);
 $('modelPrev').disabled=STATE.position<=0;$('modelNext').disabled=STATE.position>=list.length-1;
 const iframe=$('sketchfabFrame');$('iframeLoader').hidden=false;
 // Official Sketchfab embedding: the source platform remains the 3D host.
 iframe.onload=()=>{$('iframeLoader').hidden=true};
 iframe.src='https://sketchfab.com/models/'+uidFor(v)+'/embed?autostart=1&preload=1&ui_controls=1&ui_infos=1&ui_watermark=1&ui_hint=2';
 window.dispatchEvent(new CustomEvent('expovault:model-open',{detail:{uid:uidFor(v),title:v.title}}));
 if(hash)history.replaceState(null,'','#model='+uidFor(v));
}
function closeViewer({restoreHash=true}={}){
 $('viewer').hidden=true;$('viewerOverlay').hidden=true;document.body.style.overflow='';
 window.dispatchEvent(new CustomEvent('expovault:model-close'));
 const iframe=$('sketchfabFrame');iframe.src='about:blank';iframe.onload=null;
 STATE.active=null;
 if(restoreHash)history.replaceState(null,'','#'+STATE.section);
}
function moveModel(dir){
 const list=activeList(),pos=list.findIndex(x=>x.id===STATE.active?.id);const next=list[pos+dir];
 if(next)openOriginal(next,{fromSaved:STATE.fromSaved});
}
function bindControls(){
 document.querySelectorAll('[data-section]').forEach(item=>item.addEventListener('click',e=>{e.preventDefault();if(STATE.active)closeViewer({restoreHash:false});setSection(item.dataset.section)}));
 $('mobileMenu').onclick=()=>$('side').classList.toggle('mobile-show');
 $('jumpCollection').onclick=()=>$('collectionAnchor').scrollIntoView({behavior:'smooth'});
 $('query').oninput=e=>{
  if(STATE.section==='models'){STATE.search.models=e.target.value;runModelFilters()}
  else if(STATE.section==='concepts'){STATE.search.concepts=e.target.value;runConceptFilters()}
  else if(STATE.section==='technical'){STATE.search.technical=e.target.value;$('technicalQuery').value=e.target.value;renderTechnical()}
  else if(STATE.section==='saved'){const q=e.target.value.toLowerCase();for(const card of $('savedGrid').children)card.style.display=card.textContent.toLowerCase().includes(q)?'':'none'}
 };
 for(const button of document.querySelectorAll('.chip'))button.onclick=()=>{STATE.kind=button.dataset.kind;document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('active',c===button));runModelFilters()};
 $('toggleFilters').onclick=()=>$('filterDrawer').hidden=!$('filterDrawer').hidden;
 $('availability').onchange=e=>{STATE.availability=e.target.value;runModelFilters()};
 $('modelLicence').onchange=e=>{STATE.licence=e.target.value;runModelFilters()};
 $('modelSort').onchange=e=>{STATE.sort=e.target.value;runModelFilters()};
 $('clearFilters').onclick=resetModelFilters;$('resetEmpty').onclick=resetModelFilters;
 $('moreModels').onclick=()=>{STATE.modelsShow+=32;renderModels(true)};
 $('moreConcepts').onclick=()=>{STATE.conceptsShow+=32;renderConcepts(true)};
 for(const [id,data] of [['conceptWidth',[3,4,5,6,8,10,12]],['conceptDepth',[2,3,4,5,6,8]],['conceptStyle',['Minimal','Portal','Truss','Feature Wall','Canopy']],['conceptType',['Inline','Corner','Peninsula','Island']]]){
  const el=$(id);for(const val of data){const o=create('option','',val+(typeof val==='number'?' m':''));o.value=val;el.append(o)}
  el.onchange=runConceptFilters;
 }
 $('technicalQuery').oninput=e=>{STATE.search.technical=e.target.value;$('query').value=e.target.value;renderTechnical()};
 $('viewerClose').onclick=()=>closeViewer();$('viewerOverlay').onclick=()=>closeViewer();
 $('viewerSave').onclick=()=>{if(STATE.active){toggleSave(STATE.active.id);$('viewerSave').textContent=STATE.saved.has(STATE.active.id)?'♥ Saved':'♡ Save'}};
 $('viewerShare').onclick=async()=>{const u=new URL(location.href);u.hash='model='+uidFor(STATE.active);try{await navigator.clipboard.writeText(u.href);toast('Shareable model link copied')}catch(_){toast('Share this link: '+u.href)}};
 $('modelPrev').onclick=()=>moveModel(-1);$('modelNext').onclick=()=>moveModel(1);
 $('findConcept').onclick=()=>{closeViewer({restoreHash:false});setSection('concepts')};
 $('downloadExternal').onclick=()=>{if(STATE.active?.is_downloadable)openDownloadCenter(STATE.active)};
 document.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('query').focus()}
  if(e.key==='Escape'){if(STATE.active)closeViewer();else $('side').classList.remove('mobile-show')}
  if(STATE.active&&e.target.tagName!=='INPUT'){if(e.key==='ArrowRight')moveModel(1);if(e.key==='ArrowLeft')moveModel(-1)}
 });
 window.addEventListener('hashchange',()=>navigateFromHash());
}
function navigateFromHash(){
 const hash=location.hash.slice(1);
 if(hash.startsWith('model=')){
  const id=hash.slice(6).toLowerCase();const model=STATE.models.find(v=>uidFor(v)?.toLowerCase()===id);
  if(model){if(STATE.section!=='models')setSection('models',{changeHash:false});if(STATE.active?.id!==model.id)openOriginal(model,{hash:false})}
  return;
 }
 if(STATE.active)closeViewer({restoreHash:false});
 if(['models','concepts','technical','saved'].includes(hash)&&STATE.section!==hash)setSection(hash,{changeHash:false});
}
async function fetchJSON(url){
 const response=await fetch(url,{cache:'force-cache'});if(!response.ok)throw Error(url+' '+response.status);return response.json();
}
async function init(){
 bindControls();
 let fileResults;
 try{fileResults=await Promise.all([fetchJSON('catalog/sketchfab_index.json'),fetchJSON('catalog/creator_discovery.json'),fetchJSON('catalog/concept_cards.json'),fetchJSON('catalog/sources.json'),fetchJSON('catalog/oembed_thumbnails.json')])}
 catch(error){console.error(error);$('modelGrid').textContent='Catalogue load failed — refresh this page to retry';toast('Catalogue could not load');return}
 const [original,discovery,concepts,sources,highRes]=fileResults;
 const seen=new Set();
 for(const v of [...(original.items||[]),...(discovery.items||[])]){
  if(!uidFor(v)||seen.has(v.id))continue;seen.add(v.id);
  const item={...v,title:String(v.title||'Untitled model').trim(),author:String(v.author||'Original creator'),is_downloadable:!!v.is_downloadable};
  item.category=category(item);item.relevance=score(item);
  STATE.models.push(item);
 }
 STATE.concepts=(concepts.items||[]).map(c=>({id:c[0],width_m:c[1],depth_m:c[2],booth_type:c[3],style:c[4],fitout:c[5],area_m2:c[6]}));STATE.technical=sources||[];
 const thumbnails=highRes.thumbnails||{};for(const item of STATE.models){const value=thumbnails[item.id];if(value&&validHttp(value.thumbnail,['sketchfab.com','cloudfront.net']))item.thumbnail=value.thumbnail}
 STATE.models.sort((a,b)=>b.relevance-a.relevance);
 $('metricModels').textContent=number(STATE.models.length);
 $('sideSources').textContent=number(STATE.models.length);
 persistSaved();runModelFilters();runConceptFilters();renderTechnical();
 // Surface genuine source content in hero, without copying or rehosting protected meshes.
 const featured=STATE.models.filter(x=>x.category==='booth'&&validHttp(x.thumbnail,['sketchfab.com','cloudfront.net']));
 if(featured.length>1){$('heroImageOne').src=featured[3]?.thumbnail||featured[0].thumbnail;$('heroImageTwo').src=featured[10]?.thumbnail||featured[1].thumbnail}
 const hash=location.hash.slice(1);
 if(['models','concepts','technical','saved'].includes(hash))setSection(hash,{changeHash:false,scroll:false});
 else setSection('models',{changeHash:false,scroll:false});
 if(hash.startsWith('model='))navigateFromHash();
}
init();
