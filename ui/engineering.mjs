const root=document.getElementById('engineeringCollection');
if(root){
  const holder=root.querySelector('#engCards');
  const search=root.querySelector('#engQuery');
  const counter=root.querySelector('#engCount');
  const more=root.querySelector('#engMore');
  const tabs=[...root.querySelectorAll('[data-eng-filter]')];
  let records=[],kind='all',show=12;
  const base=new URL('.',document.baseURI);
  const localFile=p=>new URL(p,base).href;
  const esc=val=>String(val??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const typeName={featured_booth_candidate:'Featured source · Native CAD',modular_kit:'Modular 3D booth kit',original_glb:'Designer original',production_component:'Production 3D component',unreviewed_original:'Staged original source'};
  let visible=[];
  function choose(kindValue){
    kind=kindValue;
    tabs.forEach(t=>{const active=t.dataset.engFilter===kind;t.classList.toggle('active',active);t.setAttribute('aria-pressed',String(active))});
    show=12;display();
  }
  function display(){
    const q=(search.value||'').trim().toLowerCase();
    visible=records.filter(x=>(kind==='all'||(kind==='booth'&&x.quality==='featured_booth_candidate')||(kind==='modular'&&x.quality==='modular_kit')||(kind==='original'&&x.quality==='original_glb')||(kind==='component'&&x.quality==='production_component'))
      &&(!q||[x.title,x.uid,x.creator,x.group,...x.formats].join(' ').toLowerCase().includes(q)));
    const fragment=document.createDocumentFragment();
    for(const item of visible.slice(0,show)){
      const card=document.createElement('article');card.className='eng-card';
      const media=document.createElement('div');media.className='eng-art';
      if(item.thumbnail){
        const img=document.createElement('img');img.loading='lazy';img.decoding='async';img.alt='Original 3D view of '+item.title;
        img.src=localFile(item.thumbnail);img.onerror=()=>{img.remove();media.classList.add('eng-art-empty');media.textContent='⬡';};
        media.append(img);
      }else{media.classList.add('eng-art-empty');media.textContent='⬡'}
      const label=document.createElement('span');label.className='eng-photo-badge';
      label.textContent=item.quality==='featured_booth_candidate'?'CURATED DESIGN':item.formats.includes('DWG')?'NATIVE CAD SOURCE':'ORIGINAL 3D';
      media.append(label);
      const body=document.createElement('div');body.className='eng-card-body';
      const meta=document.createElement('div');meta.className='eng-card-meta';
      meta.textContent=(typeName[item.quality]||'Source model')+(item.wave?' · W'+item.wave:'');
      const h=document.createElement('h3');h.textContent=item.title;
      const subt=document.createElement('p');subt.textContent=item.creator+' · '+item.formats.join(' + ');
      const status=document.createElement('div');status.className='eng-status';
      const complete=item.quality==='featured_booth_candidate';
      status.textContent=complete?'Full booth candidate · engineering review pending':
        item.quality==='modular_kit'?'Editable modular layout · engineering review pending':
        item.quality==='production_component'?'Booth component · not a complete booth':'Source authenticity staged · 3D visual QA pending';
      const foot=document.createElement('div');foot.className='eng-card-foot';
      const open=document.createElement('a');open.className='eng-card-primary';
      if(item.web_glb){open.href=localFile('composer.html?design='+encodeURIComponent(item.id)+'&tab=brand');open.textContent='Edit in Composer';}
      else {open.href=localFile('composer.html?source='+encodeURIComponent(item.uid)+'&tab=items');open.textContent='Open in Composer';}
      const dl=document.createElement('a');dl.className='eng-card-secondary';dl.href=item.drive_url;
      dl.target='_blank';dl.rel='noopener noreferrer';dl.textContent='Source files';
      const copy=document.createElement('button');copy.type='button';copy.className='eng-copy';copy.textContent='Copy ID';copy.title=item.uid;
      copy.onclick=async()=>{try{await navigator.clipboard.writeText(item.uid);copy.textContent='Copied ✓';setTimeout(()=>copy.textContent='Copy ID',1500)}catch(_){copy.textContent=item.uid.slice(0,8)}};
      foot.append(open,dl,copy);body.append(meta,h,subt,status,foot);card.append(media,body);fragment.append(card);
    }
    holder.replaceChildren(fragment);
    counter.textContent=visible.length.toLocaleString('en-US')+' source models';
    more.hidden=visible.length<=show;
  }
  tabs.forEach(t=>t.addEventListener('click',()=>choose(t.dataset.engFilter)));
  search?.addEventListener('input',()=>{show=12;display()});
  more?.addEventListener('click',()=>{show=Math.min(visible.length,show+24);display()});
  fetch('catalog/engineering_collection.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
   .then(data=>{
      records=data.models||[];
      root.querySelector('#engTotal').textContent=records.length.toLocaleString('en-US');
      root.querySelector('#engEmbedded').textContent=records.filter(x=>x.web_glb).length.toLocaleString('en-US');
      display();
   })
   .catch(e=>{holder.textContent='Engineer archive is temporarily unavailable. Open the team Drive source archive instead.';console.error('[Engineering gallery]',e)});
}
