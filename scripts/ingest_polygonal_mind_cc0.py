"""Ingest selected CC0 source-authored exhibition and event objects as local GLB files."""
import concurrent.futures,hashlib,json,pathlib,requests,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'/'open-3d';OUT.mkdir(parents=True,exist_ok=True)
CAT=ROOT/'catalog'/'open_3d_cc0.json'
PREFIX='https://raw.githubusercontent.com/ToxSam/cc0-models-Polygonal-Mind/main/'
GITHUB='https://github.com/ToxSam/cc0-models-Polygonal-Mind/blob/main/'
SOURCE_LICENSE='https://github.com/ToxSam/cc0-models-Polygonal-Mind/blob/main/License.md'
FILES=[
('cryptoavatars-retro-booth/RetroComputerBooth.glb','Retro computer exhibition booth'),
('cryptoavatars-retro-booth/Computer_Screen.glb','Exhibition display screen'),
('cryptoavatars-retro-booth/Computer_Structure.glb','Exhibit computer framework'),
('avatar-show/Table_Futuristic.glb','Futuristic display counter'),
('avatar-show/Table_Round_01.glb','Round meeting table'),
('avatar-show/StudioLight_Armature.glb','Studio showcase lighting rig'),
('avatar-show/Lamp_Stand.glb','Freestanding spotlight'),
('avatar-show/Long_Chair.glb','Exhibition lounge bench'),
('abm/InfoPanel01_Art.glb','Information wall panel 1'),
('abm/InfoPanel02_Art.glb','Information wall panel 2'),
('ca-world/Shelf_01_a.glb','Merchandising shelf 1'),
('ca-world/Shelf_02_a.glb','Merchandising shelf 2'),
('ca-world/Shelf_03_a.glb','Merchandising shelf 3'),
('ca-world/Shelf_04_a.glb','Merchandising shelf 4'),
('lunar-year/ArchBanner.glb','Exhibition entrance arch'),
('lunar-year/Banner.glb','Hanging event banner'),
('chromatic-chaos/ComputerScreen_Retro.glb','Vintage digital screen'),
('chromatic-chaos/Screen_Retro_01.glb','Retro display panel'),
('avatar-garden/StandPedestal01.glb','Product showcase pedestal'),
('avatar-garden/StandArc01.glb','Freestanding exhibit arch')
]
def one(entry):
 index,(path,label)=entry
 identity='CC0-'+str(9000000+index)
 rel='projects/'+path
 target=OUT/(identity+'.glb')
 if target.exists():
  data=target.read_bytes()
 else:
  url=PREFIX+rel
  for attempt in range(3):
   try:
    r=requests.get(url,timeout=60,headers={'User-Agent':'ExpoVault-CC0-Asset-Curator'})
    r.raise_for_status();data=r.content
    if len(data)>55_000_000:raise ValueError('Excessive file size')
    if data[:4]!=b'glTF' or int.from_bytes(data[4:8],'little')!=2 or int.from_bytes(data[8:12],'little')!=len(data):raise ValueError('Invalid binary glTF')
    target.write_bytes(data)
    break
   except Exception as e:
    if attempt==2:raise
    time.sleep(attempt+1)
 if data[:4]!=b'glTF' or int.from_bytes(data[8:12],'little')!=len(data):raise ValueError('Existing GLB invalid')
 return {
  'id':identity,'name':label,'pack':'Polygonal Mind — Exhibition & Furniture',
  'pack_slug':'polygonal-mind-exhibition',
  'kind':'Original creator-authored exhibition asset',
  'description':'CC0 source-authored 3D component from Polygonal Mind; may have artistic stylization rather than manufacturing dimensions.',
  'source_url':GITHUB+rel,'license':'CC0-1.0','license_evidence_url':SOURCE_LICENSE,
  'source_creator':'Polygonal Mind','ai_generated':False,
  'file_size':len(data),'triangles':0,
  'source_glb':PREFIX+rel,'source_thumb':None,
  'glb':'assets/open-3d/'+identity+'.glb',
  'thumbnail':'assets/open-3d/'+identity+'.webp',
  'sha256':hashlib.sha256(data).hexdigest()
 }
def main():
 fromfiles=list(enumerate(FILES,1))
 done=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(one,row):row for row in fromfiles}
  for i,future in enumerate(concurrent.futures.as_completed(futures),1):
   try:done.append(future.result())
   except Exception as e:errors.append((futures[future][1][0],str(e)))
   if i%5==0:print('DONE',i,'SAVED',len(done),'ERRORS',len(errors),flush=True)
 old=json.loads(CAT.read_text(encoding='utf-8'))
 existing={x['id']:x for x in old['assets']}
 for a in done:existing[a['id']]=a
 old['assets']=list(existing.values());old['count']=len(old['assets'])
 old['bytes']=sum(int(a.get('file_size',0)) for a in old['assets'])
 old['packs']=[x for x in old['packs'] if x['slug']!='polygonal-mind-exhibition']
 if done:old['packs'].append({'slug':'polygonal-mind-exhibition','title':'Polygonal Mind — Exhibition & Furniture','license':'CC0 1.0 Universal','available':len(done)})
 CAT.write_text(json.dumps(old,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('RESULT',len(done),'TOTAL',old['count'],'ERRORS',errors,'MB',round(sum(a['file_size'] for a in done)/1048576,1),flush=True)
if __name__=='__main__':main()
