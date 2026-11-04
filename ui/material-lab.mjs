/* ExpoVault v3 material-lab: opt-in Sketchfab Viewer API integration.
   Scene materials are modified only in the currently open viewer session.
   No source mesh, texture archive or creator file is downloaded or redistributed.
   https://sketchfab.com/developers/viewer/functions
*/
const $=id=>document.getElementById(id);
let uid=null,client=null,api=null,materials=[],token=0,apiLoad=null;
function status(msg){$('materialStatus').textContent=msg}
function resetState(){
 token++;client=null;api=null;materials=[];
 $('labControls').hidden=true;$('materialSelect').replaceChildren();
 $('enableMaterialLab').disabled=false;$('enableMaterialLab').hidden=false;
 $('enableMaterialLab').textContent='✳  Enable 3D recolouring';
 $('applyMaterialColor').disabled=true;
 status('Viewer editing is experimental. Available materials depend on the creator’s 3D scene.');
}
window.addEventListener('expovault:model-open',event=>{uid=event.detail.uid;resetState()});
window.addEventListener('expovault:model-close',()=>{uid=null;resetState()});
function sdk(){
 if(typeof window.Sketchfab==='function')return Promise.resolve();
 if(apiLoad)return apiLoad;
 apiLoad=new Promise((resolve,reject)=>{
  const script=document.createElement('script');
  script.src='https://static.sketchfab.com/api/sketchfab-viewer-1.12.1.js';
  script.async=true;script.onload=()=>typeof window.Sketchfab==='function'?resolve():reject(new Error('Viewer API was not available'));
  script.onerror=()=>reject(new Error('Viewer API could not load'));
  document.head.append(script);
 });
 return apiLoad;
}
$('enableMaterialLab').onclick=async()=>{
 if(!uid)return;
 const current=uid;const seq=++token;
 const start=$('enableMaterialLab');start.disabled=true;start.textContent='Connecting to the material editor…';
 status('Opening the editor on the original viewer. This may reload the 3D scene.');
 try{
  await sdk();
  if(seq!==token||current!==uid)return;
  const iframe=$('sketchfabFrame');
  client=new window.Sketchfab('1.12.1',iframe);
  client.init(current,{
   autostart:1,ui_controls:1,ui_infos:1,ui_watermark:1,ui_hint:2,
   success(instance){
    if(seq!==token)return;
    api=instance;api.start();
    api.addEventListener('viewerready',()=>{
     if(seq!==token)return;
     api.getMaterialList((error,list)=>{
      if(seq!==token)return;
      if(error||!Array.isArray(list)||!list.length){
       start.disabled=false;start.textContent='Try editor again';status('No accessible material slots in this model. Regular 3D preview is still available.');return;
      }
      materials=list;
      const select=$('materialSelect');
      select.replaceChildren();
      materials.forEach((m,i)=>{
       const option=document.createElement('option');option.value=String(i);option.textContent=(m.name||'Material '+(i+1));select.append(option);
      });
      const preferred=materials.findIndex(m=>/wall|panel|plastic|white|fabric|paint|frame|base/i.test(m.name||''));
      select.value=String(Math.max(0,preferred));
      $('labControls').hidden=false;$('applyMaterialColor').disabled=false;start.hidden=true;
      status('Connected: '+materials.length+' materials. Choose one, pick a colour and apply it to the live 3D preview.');
     });
    });
   },
   error(){
    if(seq!==token)return;
    start.disabled=false;start.textContent='Try editor again';
    status('This original scene does not currently support the material editor. The normal viewer remains available.');
   }
  });
 }catch(error){if(seq!==token)return;start.disabled=false;start.textContent='Try editor again';status(error.message)}
};
$('materialColor').oninput=e=>$('labHex').textContent=e.target.value.toUpperCase();
$('applyMaterialColor').onclick=()=>{
 const idx=Number($('materialSelect').value);
 if(!api||!materials[idx]){status('Open the material editor first.');return}
 const hex=$('materialColor').value;
 const color=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255);
 const material=JSON.parse(JSON.stringify(materials[idx]));
 if(!material.channels){status('This material has no editable colour channels.');return}
 let updates=0;
 for(const name of ['AlbedoPBR','DiffusePBR','DiffuseColor']){
  const channel=material.channels[name];
  if(channel&&Array.isArray(channel.color)){
   channel.color=color;
   if('enable' in channel&&channel.enable===false)channel.enable=true;
   updates++;
  }
 }
 if(!updates&&material.channels.AlbedoPBR){
  material.channels.AlbedoPBR.color=color;material.channels.AlbedoPBR.enable=true;updates++;
 }
 if(!updates){status('Selected material does not expose an editable base colour.');return}
 $('applyMaterialColor').disabled=true;
 try{
  api.setMaterial(material,()=>{
   if(!uid)return;
   $('applyMaterialColor').disabled=false;
   status('Colour applied to live preview only. Original model and creator files are unchanged.');
  });
 }catch(error){$('applyMaterialColor').disabled=false;status('The viewer did not accept this colour: '+error.message)}
};
$('resetMaterialLab').onclick=()=>{
 if(!uid)return;
 const current=uid;resetState();
 const iframe=$('sketchfabFrame');
 iframe.src='https://sketchfab.com/models/'+current+'/embed?autostart=1&preload=1&ui_controls=1&ui_infos=1&ui_watermark=1&ui_hint=2';
 status('Original materials restored by reloading the untouched model.');
};
