/* ExpoVault pilot: priority original CAD + source GLBs before generated concepts.
 * Keep unverified and private Drive assets out of automatic public download. */
const q=id=>document.getElementById(id);
const section=q('pilotSection');
const grid=q('pilotGrid');
const search=q('pilotSearch');
const count=q('pilotVisibleCount');
let catalog=[],visible=[],limit=16,filter='booth';
const TYPE_LABEL={full_booth_reference:'Physically built reference',modular_booth:'Original booth kit',designer_archive:'Author 3D source',original_study:'Designer study',architectural_display:'Architectural system',display_system:'Display system',production_component:'Technical component'};
const catGroup=x=>x.category==='full_booth_reference'||x.category==='modular_booth'||x.category==='designer_archive'||x.category==='original_study'?'booth':x.has_native_cad?'components':'other';
function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!=null)node.textContent=String(text);return node}
function safeAssetUrl(value){if(typeof value!=='string')return null;try{const u=new URL(value,location.href);if(u.protocol!=='https:'&&u.origin!==location.origin)return null;if(u.protocol==='https:'&&u.hostname!=='media.sketchfab.com'&&u.origin!==location.origin)return null;return u.href}catch{return null}}
function safeLink(value){try{const u=new URL(value,location.href);return u.protocol==='https:'||u.origin===location.origin?u.href:null}catch{return null}}
function makeLink(text,url,primary=false){const a=el('a',primary?'pilot-primary pilot-a11y':'pilot-a11y',text);a.href=url;a.target=url.startsWith(location.origin)?'_self':'_blank';if(a.target==='_blank')a.rel='noopener noreferrer';return a}
function card(m){
 const article=el('article','pilot-card'),cover=el('div','pilot-cover'),label=el('span','pilot-overline',TYPE_LABEL[m.category]||'Original 3D source');
 const number=el('span','pilot-number',m.uid?'#'+m.uid.slice(0,7).toUpperCase():'CUT FILES');
 const imgURL=safeAssetUrl(m.thumbnail);
 const fallback=el('div','pilot-wire');
 if(imgURL){const img=el('img');img.loading='lazy';img.decoding='async';img.src=imgURL;img.alt=m.title+' 3D model preview';img.onerror=()=>{img.remove();cover.prepend(fallback)};cover.append(img)}else cover.append(fallback);
 cover.append(label,number);
 const content=el('div','pilot-card-content'),title=el('h3','',m.title),by=el('div','pilot-byline','by '+(m.creator||'Original designer')),tags=el('div','pilot-tags');
 tags.append(el('span','pilot-tag cad','Original 3D'));
 if(m.has_native_cad)tags.append(el('span','pilot-tag cad','Native CAD supplied'));
 else tags.append(el('span','pilot-tag','Source ZIP'));
 tags.append(el('span','pilot-tag warning','Engineering QA pending'));
 const formats=el('div','pilot-detail',Array.isArray(m.formats)?m.formats.join('  ·  '):'Creator source package');
 const actions=el('div','pilot-actions');
 if(m.hosted_glb){actions.append(makeLink('◈ Open in 3D Composer','composer.html?design='+encodeURIComponent(m.id),true))}
 else if(m.uid){actions.append(makeLink('◈ Compose from source','composer.html?source='+encodeURIComponent(m.uid),true))}
 const src=safeLink(m.source_file_url);
 if(src)actions.append(makeLink(src.includes('drive.google.com')?'↗ Team Drive source':'↓ Original source pack',src));
 else actions.append(makeLink('↗ Original creator',safeLink(m.source_model_url)||'originals.html'));
 content.append(title,by,tags,formats,actions);article.append(cover,content);return article
}
function activeFilter(item){
 if(filter==='all')return true;
 if(filter==='booth')return catGroup(item)==='booth';
 if(filter==='cad')return item.has_native_cad;
 if(filter==='component')return ['production_component','display_system','architectural_display'].includes(item.category);
 return true;
}
function render(){
 const word=(search?.value||'').trim().toLowerCase();
 visible=catalog.filter(x=>activeFilter(x)&&(!word||[x.title,x.creator,x.uid,x.category,x.formats?.join(' ')].join(' ').toLowerCase().includes(word)));
 visible.sort((a,b)=>b.rank-a.rank||a.title.localeCompare(b.title));
 grid.replaceChildren();for(const x of visible.slice(0,limit))grid.append(card(x));
 count.textContent='Showing '+Math.min(limit,visible.length)+' of '+visible.length+' matching source files';
 q('pilotMore').hidden=visible.length<=limit;
 q('pilotEmpty').hidden=visible.length!==0
}
function bind(){
 if(!section)return;
 search.addEventListener('input',()=>{limit=16;render()});
 section.querySelectorAll('[data-pilot-filter]').forEach(btn=>btn.addEventListener('click',()=>{
  filter=btn.dataset.pilotFilter;limit=16;section.querySelectorAll('[data-pilot-filter]').forEach(x=>x.setAttribute('aria-pressed',x===btn?'true':'false'));render()
 }));
 q('pilotMore').addEventListener('click',()=>{limit+=16;render()});
}
async function init(){
 if(!section)return;bind();
 try{const r=await fetch('catalog/pilot_source_library.json',{cache:'no-store'});if(!r.ok)throw new Error('Catalog HTTP '+r.status);
 const data=await r.json();catalog=Array.isArray(data.assets)?data.assets:[];
 if(catalog.length!==data.showcase_total||data.staged_original_uid_count!==369)throw new Error('Curated manifest is inconsistent');
 const n=el('span','','369 original source IDs · '+data.has_native_cad_count+' with native CAD');
 q('pilotLibraryStats').replaceChildren(n);
 render()
 }catch(err){q('pilotEmpty').hidden=false;q('pilotEmpty').textContent='Source collection unavailable. Existing hosted 3D library remains available.';count.textContent='Source index unavailable';console.warn('Pilot source collection',err)}
}
init();
