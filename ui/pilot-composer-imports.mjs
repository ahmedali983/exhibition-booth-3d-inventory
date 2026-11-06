/* ExpoVault — internal source archive -> editable Three.js scene.
 * No transfer of user-selected 3D bytes to a server; original Drive permissions apply.
 */
export function initializeTeamSources(api,records){
 const {state,dom:$,JSZip,loadBase,addItem,switchTab,renderItems,toast}=api;
 state.teamAssets=Array.isArray(records)?records.slice().sort((a,b)=>(b.rank||0)-(a.rank||0)):[];
 const partKinds=new Set(['production_component','display_system','architectural_display']);
 const show=id=>$(id);
 const sourceOf=record=>{const value=record?.source_file_url||record?.source_model_url||'';
  try{const u=new URL(value,location.href);if(u.protocol==='https:'||u.origin===location.origin)return u.href}catch{}
  return null};
 function makeRow(rec){
  const wrap=document.createElement('div');wrap.className='team-source-row';
  const description=document.createElement('div'),heading=document.createElement('strong'),note=document.createElement('small');
  heading.textContent=rec.title||rec.id;
  note.textContent=(rec.formats||[]).join(' · ')+' · '+(rec.has_native_cad?'Native CAD supplied':'3D source available')+' · engineer review required';
  description.append(heading,note);wrap.append(description);
  const url=sourceOf(rec);
  if(url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';
   a.textContent=rec.source_file_url?'Open package ↗':'Creator page ↗';wrap.append(a)}
  return wrap;
 }
 function render(kind){
  const target=kind==='part'?'partSourceList':'teamSourceList';
  const field=kind==='part'?'partSourceSearch':'teamSourceSearch';
  const host=show(target);if(!host)return;
  const query=(show(field)?.value||'').trim().toLowerCase();
  const matches=state.teamAssets.filter(r=>(kind==='part'?partKinds.has(r.category):!partKinds.has(r.category))&&
    (!query||[r.title,r.creator,r.uid,r.formats?.join(' '),r.category].join(' ').toLowerCase().includes(query)));
  host.replaceChildren();
  if(!matches.length){const p=document.createElement('div');p.className='team-source-empty';p.textContent='No matching source. Try another designer, size or ID.';host.append(p);return}
  for(const item of matches.slice(0,12))host.append(makeRow(item));
  if(matches.length>12){const p=document.createElement('div');p.className='team-source-empty';p.textContent='Showing 12 of '+matches.length+'. Search to narrow the list.';host.append(p)}
 }
 async function bytesFromSource(file){
  if(!file||file.size>250_000_000)throw Error('The maximum source archive size is 250 MB');
  if(!/\.(glb|zip)$/i.test(file.name))throw Error('Select an original .glb or source .zip file');
  let data;
  if(/\.zip$/i.test(file.name)){
   if(!JSZip)throw Error('ZIP reader is not available');
   const zip=await JSZip.loadAsync(file,{checkCRC32:true});
   const entries=Object.values(zip.files).filter(x=>!x.dir&&/\.glb$/i.test(x.name));
   if(!entries.length)throw Error('No GLB inside ZIP. Native CAD-only archives must be converted by an engineer first.');
   entries.sort((a,b)=>a.name.length-b.name.length);
   const entry=entries[0];
   if((entry._data?.uncompressedSize||0)>160_000_000)throw Error('GLB exceeds the safe 160 MB viewer limit');
   data=await entry.async('arraybuffer');
  }else data=await file.arrayBuffer();
  if(!(data instanceof ArrayBuffer)||data.byteLength<20||data.byteLength>160_000_000)throw Error('Invalid or oversized GLB');
  const head=new DataView(data);
  if(head.getUint32(0,true)!==0x46546c67||head.getUint32(4,true)!==2||head.getUint32(8,true)!==data.byteLength)
   throw Error('Not a valid GLB v2 3D scene');
  return data;
 }
 async function importFile(file,asItem){
  if(!file)return;
  const status=show(asItem?'importPartStatus':'importSourceStatus');
  status.textContent='Checking '+file.name+'…';
  try{
   const bytes=await bytesFromSource(file);
   const uid=file.name.match(/[a-f0-9]{32}/i)?.[0]?.toLowerCase()||null;
   const found=state.teamAssets.find(x=>x.uid===uid)||null;
   const title=(found?.title||file.name.replace(/\.(zip|glb)$/i,'')).slice(0,100);
   if(asItem){
    const asset={id:'TEAM-ITEM-'+Date.now(),name:title,pack:'Team imported sources',pack_slug:'team-source-import',
     description:'Locally imported source geometry',kind:'3D source',license:found?.license_status||'User supplied',
     source_url:found?.source_model_url||null,thumbnail:found?.thumbnail||'assets/thumbs/EV-0001.webp',
     localBytes:bytes,is_local_import:true};
    state.assets.unshift(asset);
    state.filterPack='all';show('itemPack').value='all';
    renderItems();const placed=await addItem(asset);
    if(!placed)throw Error('3D geometry could not be placed');
    switchTab('items');status.textContent='Added '+title+'. Use Position & Edit to recolour the selected material.';
   }else{
    const base={id:'TEAM-'+(uid||Date.now()),name:title,creator:found?.creator||'Team source import',
     source_url:found?.source_model_url||null,license:found?.license_status||'Team-supplied original',
     is_creator_base:true,localBytes:bytes,native_cad_bundle:found?.source_file_url||null,
     glb:null,thumbnail:found?.thumbnail||'assets/thumbs/EV-0001.webp',
     booth_type:'Team original',style:'Source import',fitout:'Editable GLB',
     width_m:6,depth_m:6,area_m2:36};
    state.sourceBases.unshift(base);state.bases.unshift(base);
    const option=document.createElement('option');option.value=base.id;
    option.textContent=title+' — local source';show('originalDesign').prepend(option);show('originalDesign').value=base.id;
    await loadBase(base,{preserve:false});
    if(state.base!==base)throw Error('GLB failed to open');
    switchTab('brand');status.textContent='Loaded '+title+' — real 3D materials ready for recolouring.';
   }
  }catch(e){status.textContent='Import failed: '+e.message;toast(e.message);console.error('ExpoVault source import',e)}
 }
 show('teamSourceSearch')?.addEventListener('input',()=>render('booth'));
 show('partSourceSearch')?.addEventListener('input',()=>render('part'));
 for(const [field,asItem] of [['sourceFileImport',false],['partFileImport',true]]){
  show(field)?.addEventListener('change',async e=>{
   const file=e.target.files?.[0];e.target.value='';
   await importFile(file,asItem);
  });
 }
 render('booth');render('part');
 const param=new URLSearchParams(location.search).get('source')||'';
 const match=state.teamAssets.find(x=>x.uid===param);
 if(match){
  const part=partKinds.has(match.category);
  const field=show(part?'partSourceSearch':'teamSourceSearch');
  field.value=match.uid;render(part?'part':'booth');
  show(part?'importPartStatus':'importSourceStatus').textContent='Selected '+match.title+'. Open its source package from the list, download it from team Drive, and import the ZIP/GLB above.';
  if(part)switchTab('items');
 }
}
