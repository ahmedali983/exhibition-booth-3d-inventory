/* ExpoVault Studio: spotlight high-quality source-authored booth models.
 * Official Sketchfab embeds; avoid viewer ripping, misleading CAD certification,
 * placeholders, and incorrectly counting components as complete booths.
 */
const el=id=>document.getElementById(id);
const wrap=el('pilotSection'), grid=el('pilotGrid'), search=el('pilotSearch');
let items=[],filtered=[],filter='booth';
const filterMatch=x=>filter==='all'||(filter==='booth'&&(x.category==='featured'||x.category==='production'))||
 (filter==='cad'&&(x.cad_cutting_files_verified||x.editable_creator_source_format==='FBX'))||
 (filter==='component'&&x.category==='concept');
const tags={featured:'Designer original · exhibition booth',concept:'Designer concept · inspiration',production:'Built reference · cutting files'};
const trusted=url=>{try{const u=new URL(url,location.href);return (u.protocol==='https:'||u.origin===location.origin)?u.href:null}catch{return null}};
function create(tag,cls,txt){const o=document.createElement(tag);if(cls)o.className=cls;if(txt!==undefined)o.textContent=txt;return o}
function link(text,url){const a=create('a','pilot-a11y',text);a.href=trusted(url)||'#';a.target='_blank';a.rel='noopener noreferrer';return a}
function dialog3D(m){
 if(!m.uid){window.location.href='composer.html?design='+encodeURIComponent(m.id);return}
 const dlg=document.createElement('dialog');dlg.className='pilot-3d-dialog';dlg.setAttribute('aria-label',m.title+' — interactive 3D');
 const top=create('div','pilot-dialog-top');
 const details=create('div','');details.append(create('strong','',m.title),create('small','',m.creator+' · 3D hosted by Sketchfab'));
 const fallback=link('Open directly on Sketchfab ↗',m.source_model_url);fallback.classList.add('pilot-direct-link');details.append(fallback);
 const close=create('button','pilot-dialog-close','✕ Close');close.type='button';close.setAttribute('aria-label','Close 3D viewer');
 top.append(details,close);
 const viewer=create('div','pilot-dialog-viewer');
 const iframe=document.createElement('iframe');iframe.title='Sketchfab interactive 3D preview for '+m.title;
 iframe.src='https://sketchfab.com/models/'+encodeURIComponent(m.uid)+'/embed?autostart=1&ui_hint=0';
 iframe.loading='eager';iframe.allow='autoplay; fullscreen; xr-spatial-tracking';iframe.allowFullscreen=true;
 iframe.referrerPolicy='strict-origin-when-cross-origin';viewer.append(iframe);
 const footer=create('div','pilot-dialog-footer');
 footer.append(create('span','',m.cad_cutting_files_verified?'Original cutting-file sets included':'3D source provided; fabrication drawings not certified'));
 footer.append(link('↗ View original on Sketchfab',m.source_model_url));
 const source=trusted(m.original_3d_drive);if(source)footer.append(link('↗ Creator source / team Drive',source));
 dlg.append(top,viewer,footer);document.body.append(dlg);
 close.addEventListener('click',()=>dlg.close());
 dlg.addEventListener('click',evt=>{if(evt.target===dlg)dlg.close()});
 dlg.addEventListener('close',()=>{iframe.src='about:blank';dlg.remove()},{once:true});
 dlg.showModal();close.focus();
}
function card(m,i){
 const article=create('article','pilot-card pilot-curated-card');
 const cover=create('button','pilot-cover pilot-cover-button');cover.type='button';cover.setAttribute('aria-label','Open real 3D preview: '+m.title);
 const img=create('img');img.alt='Original 3D model preview: '+m.title;img.src=trusted(m.preview)||'';
 img.loading=i<12?'eager':'lazy';img.decoding='async';if(i<6)img.fetchPriority='high';
 img.onerror=()=>{img.hidden=true;cover.classList.add('pilot-no-preview');cover.append(create('span','pilot-no-preview-message','Preview unavailable · click to open 3D'))};
 const status=create('span','pilot-overline',tags[m.category]||'Original 3D');
 cover.append(img,status);cover.addEventListener('click',()=>dialog3D(m));
 const body=create('div','pilot-card-content');
 body.append(create('h3','',m.title),create('div','pilot-byline','Designer: '+m.creator));
 const chips=create('div','pilot-tags');
 chips.append(create('span','pilot-tag cad','Original 3D verified'));
 if(m.cad_cutting_files_verified)chips.append(create('span','pilot-tag cad','Cutting-file reference'));
 else if(m.editable_creator_source_format==='FBX')chips.append(create('span','pilot-tag','Editable FBX included'));
 else chips.append(create('span','pilot-tag','Creator 3D source'));
 chips.append(create('span','pilot-tag warning','Engineer approval pending'));
 body.append(chips,create('p','pilot-detail',m.description||'3D scene supplied by its creator'));
 const actions=create('div','pilot-actions');
 const open=create('button','pilot-primary pilot-a11y','◈ View real 3D');open.type='button';open.addEventListener('click',()=>dialog3D(m));
 actions.append(open);
 if(m.uid)actions.append(link('↗ Open on Sketchfab',m.source_model_url));
 if(m.original_3d_drive)actions.append(link(m.can_download_from_team_drive?'↗ Team source files':'↗ Original design files',m.original_3d_drive));
 body.append(actions,create('div','pilot-rights','Source attribution preserved · 3D visual screening is not fabrication certification'));
 article.append(cover,body);return article;
}
function render(){
 const word=(search.value||'').trim().toLowerCase();
 filtered=items.filter(x=>filterMatch(x)&&(!word||[x.title,x.creator,x.description,x.uid,x.editable_creator_source_format].join(' ').toLowerCase().includes(word)));
 filtered.sort((a,b)=>b.rank-a.rank);
 grid.replaceChildren(...filtered.map(card));
 el('pilotVisibleCount').textContent='Showing '+filtered.length+' selected original 3D models';
 el('pilotMore').hidden=true;el('pilotEmpty').hidden=filtered.length>0;
}
function setButtons(){wrap.querySelectorAll('[data-pilot-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pilotFilter===filter)))}
function init(){
 if(!wrap)return;
 search.addEventListener('input',render);
 wrap.querySelectorAll('[data-pilot-filter]').forEach(b=>b.addEventListener('click',()=>{
  filter=b.dataset.pilotFilter;setButtons();render();
 }));
 const toggle=el('archiveToggle');
 toggle?.addEventListener('click',()=>{const archive=el('rawArchiveWrap');const opening=archive.hidden;archive.hidden=!opening;
  toggle.setAttribute('aria-expanded',String(opening));
  toggle.textContent=opening?'Hide unreviewed archive ↑':'Open unreviewed archive ↓';
  if(opening)archive.scrollIntoView({behavior:'smooth',block:'start'});
 });
 fetch('catalog/studio_quality_shortlist.json',{cache:'no-store'})
 .then(r=>{if(!r.ok)throw Error('Curated 3D source manifest missing');return r.json()})
 .then(data=>{if(!Array.isArray(data.items)||data.full_booth_featured_count<5)throw Error('Invalid shortlist');
  items=data.items;
  el('pilotLibraryStats').textContent=String(data.full_booth_featured_count)+' curated booths · '+String(data.documented_physical_reference_count)+' built reference · '+String(data.additional_concepts)+' concepts';
  render();
 }).catch(err=>{grid.replaceChildren();el('pilotEmpty').hidden=false;el('pilotEmpty').textContent='Real 3D model previews temporarily unavailable. Visit the archived designer source library.';console.error(err)});
}
init();
