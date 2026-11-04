/* ExpoVault in-site licensed creator-model downloads.
 * The official Sketchfab importer performs sign-in and download authorization.
 * No viewer mesh scraping, protected file extraction or mirroring.
 */
const $=id=>document.getElementById(id);
let importer=null,importerLoading=null,requested=null,chosen=null,archive=null,expiry=0,active=false;
const IMPORTER_URL='https://apps.sketchfab.com/web-importer/sketchfab-importer.js';
const SOURCE='https://sketchfab.com/models/';
const VALID_UID=/^[0-9a-z]{20,40}$/i;
function info(message){$('authorizedStatus').textContent=message}
function clean(data){return typeof data==='string'?data:''}
function isTrustedUrl(url){
 try{
  const u=new URL(url);
  if(u.protocol!=='https:')return false;
  const host=u.hostname.toLowerCase();
  return host==='sketchfab.com'||host.endsWith('.sketchfab.com')
    ||host==='amazonaws.com'||host.endsWith('.amazonaws.com')
    ||host==='cloudfront.net'||host.endsWith('.cloudfront.net')
    ||host==='storage.googleapis.com';
 }catch(_){return false}
}
function safeName(str){return clean(str).replace(/[^A-Za-z0-9_\-]+/g,'_').slice(0,60)||'exhibition_model'}
function attribution(){
 const m=chosen?.model||{};
 const user=m.user||{};
 const name=clean(m.name)||requested?.title||'3D design';
 const author=clean(user.displayName)||clean(user.username)||requested?.author||'Original creator';
 const uid=clean(m.uid)||requested?.uid||'';
 const link=uid&&VALID_UID.test(uid)?SOURCE+uid:requested?.source||'';
 const licence=m.license?.label||m.license?.slug||requested?.license||'Unspecified; check publisher';
 return ['ASSET CREDITS / EXPOVAULT','',
  'Title: '+name,'Creator: '+author,'Licence: '+licence,'Original model: '+link,'',
  'Downloaded through the official Sketchfab Importer with model-specific permissions.',
  'Retain this attribution with any derivative as required by the applicable licence.',
  'A downloadable model is not necessarily an engineering-approved booth or an authorized manufacturing design.',
  'Always inspect the actual model licence and creator conditions before using it.',
  ''].join('\n');
}
function saveBlob(name,content,type){
 const url=URL.createObjectURL(new Blob([content],{type}));
 const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),12000);
}
function extractDownload(payload){
 if(!payload||typeof payload!=='object')return null;
 for(const item of [payload,payload.download,payload.data,payload.result,payload[1]]){
  if(!item||typeof item!=='object')continue;
  for(const type of ['gltf','glb','usdz']){
   const location=item[type];
   if(location?.url&&isTrustedUrl(location.url))return{url:location.url,type,expires:Number(location.expires)||300,size:Number(location.size)||0};
  }
 }
 return null;
}
function archiveReady(record,model){
 if(!record){info('The provider has not issued a downloadable file. Sign in and select a permitted model.');return}
 archive=record;expiry=Date.now()+Math.max(5,record.expires-10)*1000;
 chosen={model:model||{uid:requested?.uid,name:requested?.title},download:record};
 $('selectedAssetTitle').textContent=model?.name||requested?.title||'Authorized 3D asset';
 $('saveAuthorizedArchive').disabled=false;
 $('authorizedFallback').hidden=true;
 $('saveAuthorCredits').disabled=false;
 $('saveAuthorizedArchive').textContent=record.type==='usdz'?'↓ Download USDZ 3D model':'↓ Download glTF + textures ZIP';
 info('Creator permission confirmed by Sketchfab. The temporary download is ready. Save the archive and keep the attribution.');
}
function onSelected(result){
 if(!active)return;
 const record=extractDownload(result);
 const model=result?.model||result?.data?.model||null;
 if(record)archiveReady(record,model);
 else info('Model chosen in the importer. Sign in and select its permitted Download action to receive the file.');
}
async function startImporter(){
 if(importer)return importer;
 if(importerLoading)return importerLoading;
 importerLoading=new Promise((resolve,reject)=>{
  if(typeof window.SketchfabImporter==='function')return resolve();
  const script=document.createElement('script');script.src=IMPORTER_URL;script.async=true;
  script.onload=()=>typeof window.SketchfabImporter==='function'?resolve():reject(new Error('Sketchfab importer unavailable'));
  script.onerror=()=>reject(new Error('Could not connect to the official importer'));
  document.head.append(script);
 }).then(()=>{
  if(importer)return importer;
  $('authorizedImporter').replaceChildren();
  importer=new window.SketchfabImporter($('authorizedImporter'),{onModelSelected:onSelected});
  const iframe=$('authorizedImporter').querySelector('iframe');
  if(iframe){iframe.title='Sketchfab official 3D download, search and sign-in';iframe.setAttribute('allow','clipboard-write')}
  $('requestCurrentModel').disabled=false;
  info('Importer loaded. Sign in with Sketchfab and select a downloadable model, or request the currently viewed model after sign-in.');
  return importer;
 }).catch(err=>{
  importerLoading=null;
  $('authorizedImporter').textContent='Importer connection failed. Retry when the provider is available.';
  info(err.message);
  throw err;
 });
 return importerLoading;
}
function hide(){
 active=false;
 $('authorizedModal').hidden=true;$('authorizedBackdrop').hidden=true;
 if($('viewer').hidden)document.body.style.overflow='';
}
function show(data){
 if(!data?.uid||!VALID_UID.test(data.uid))return;
 active=true;requested=data;chosen=null;archive=null;expiry=0;
 $('authorizedModal').hidden=false;$('authorizedBackdrop').hidden=false;document.body.style.overflow='hidden';
 $('authorizedTitle').textContent='Download a licensed 3D design';
 $('authorizedModelTitle').textContent=data.title||'Selected 3D model';
 $('selectedAssetTitle').textContent=data.title||'3D design';
 $('saveAuthorizedArchive').disabled=true;$('saveAuthorCredits').disabled=true;$('authorizedFallback').hidden=true;
 $('saveAuthorizedArchive').textContent='↓ Download glTF + textures ZIP';
 info('Loading the official download importer. Sign in with your Sketchfab account.');
 startImporter().catch(console.warn);
}
$('authorizedClose').onclick=hide;
$('authorizedBackdrop').onclick=hide;
window.addEventListener('expovault:download-open',e=>show(e.detail));
$('requestCurrentModel').onclick=()=>{
 if(!importer||!requested?.uid){info('The official importer is not ready yet');return}
 $('requestCurrentModel').disabled=true;
 let settled=false;
 const timeout=setTimeout(()=>{if(!settled&&active){$('requestCurrentModel').disabled=false;info('No response yet. Sign in with Sketchfab in the importer and retry.')}},18000);
 info('Requesting authorization for '+(requested.title||'the selected model')+'… If not signed in, log in using the embedded importer first.');
 try{
  importer.download(requested.uid,(...values)=>{
   settled=true;clearTimeout(timeout);
   $('requestCurrentModel').disabled=false;
   if(!active)return;
   let record=null,model=null;
   for(const item of values){
    if(!record)record=extractDownload(item);
    if(!model&&item?.model)model=item.model;
   }
   if(record)archiveReady(record,model||{uid:requested.uid,name:requested.title});
   else info('No downloadable archive returned. Confirm your Sketchfab login and creator permission, or select the model inside the importer.');
  });
 }catch(err){settled=true;clearTimeout(timeout);$('requestCurrentModel').disabled=false;info('Provider request failed: '+err.message)}
};
$('saveAuthorizedArchive').onclick=async()=>{
 if(!archive?.url){info('Select a permitted downloadable model first');return}
 if(Date.now()>expiry){
  archive=null;$('saveAuthorizedArchive').disabled=true;
  info('The short-lived link expired. Request the model again after authentication.');return;
 }
 if(!isTrustedUrl(archive.url)){info('Untrusted file host rejected');return}
 const filename=safeName(chosen?.model?.name||requested?.title)+'.'+(archive.type==='usdz'?'usdz':'zip');
 const button=$('saveAuthorizedArchive');
 const fallback=$('authorizedFallback');
 // Prefer direct browser download without navigation. Large files and providers
 // without CORS remain accessible by explicitly clicking their signed link.
 const fallbackUrl=archive.url;
 fallback.href=fallbackUrl;fallback.download=filename;fallback.hidden=true;
 if(archive.size>100*1024*1024){
  fallback.hidden=false;
  info('Large archive ('+Math.round(archive.size/1048576)+' MB). Use the direct authenticated download link below to avoid browser memory pressure.');return;
 }
 button.disabled=true;button.textContent='Fetching authorized 3D file…';
 try{
  const res=await fetch(fallbackUrl,{mode:'cors',cache:'no-store'});
  if(!res.ok)throw Error('Archive host returned HTTP '+res.status);
  const bin=await res.blob();
  if(bin.size>160*1024*1024)throw Error('Archive exceeds safe in-browser transfer size');
  saveBlob(filename,bin,'application/octet-stream');
  info('3D archive saved in your downloads. Use “Save creator attribution” to keep licence credits with the model.');
 }catch(error){
  fallback.hidden=false;
  info('This browser could not save the archive inside ExpoVault: '+error.message+'. Use the authorised direct link below instead.');
 }finally{
  button.disabled=false;button.textContent=archive.type==='usdz'?'↓ Download USDZ 3D model':'↓ Download glTF + textures ZIP';
 }
};
$('saveAuthorCredits').onclick=()=>{
 if(!chosen)return;
 saveBlob(safeName(chosen.model?.name||requested?.title)+'-CREDITS.txt',attribution(),'text/plain;charset=utf-8');
};
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&active){e.stopImmediatePropagation();hide()}},true);
