#!/usr/bin/env python3
"""Evidence-based, non-AI-oriented source model prospecting from Objaverse-1.0.

Only author-uploaded historic Sketchfab objects that were openly CC BY / CC0
and downloadable when the dataset was collected. This writes candidate
metadata, NOT an assertion that 4000 models were downloaded, nor certified
human-made, nor complete booth stands. Do not rehost until current licence
and binary integrity checks.
"""
from __future__ import annotations
import collections,concurrent.futures as cf,gzip,json,math,pathlib,re,requests,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'catalog';OUT.mkdir(exist_ok=True,parents=True)
API='https://huggingface.co/api/datasets/allenai/objaverse/tree/main/metadata?limit=500'
FILES='https://huggingface.co/datasets/allenai/objaverse/resolve/main/'
HEADERS={'User-Agent':'ExpoVault-Open-Model-Curation/1.0'}
FULL=re.compile(r'\b(?:exhibition[\s_-]*(?:stand|booth|stall)|expo[\s_-]*(?:stand|booth)|trade[\s_-]*show[\s_-]*(?:stand|booth)|tradeshow[\s_-]*(?:booth|stand)|exhibition[\s_-]*design|show[\s_-]*booth|convention[\s_-]*booth|expo[\s_-]*pavilion)\b',re.I)
ENV=re.compile(r'\b(?:showroom|exhibition[\s_-]*hall|exhibition[\s_-]*room|exhibition[\s_-]*space|trade[\s_-]*fair|conference[\s_-]*hall|expo[\s_-]*hall|retail[\s_-]*store|store[\s_-]*interior|shop[\s_-]*interior|shopping[\s_-]*mall|shopfront|storefront|museum[\s_-]*interior|art[\s_-]*gallery|display[\s_-]*room|art[\s_-]*exhibit|event[\s_-]*stage|retail[\s_-]*shop|fashion[\s_-]*shop|commercial[\s_-]*interior|interior[\s_-]*design)\b',re.I)
FIXTURE=re.compile(r'\b(?:display[\s_-]*(?:stand|rack|counter|case|cabinet|shelf|shelves|shelving|unit|wall|panel|kiosk)|brochure[\s_-]*(?:stand|rack|holder)|reception[\s_-]*(?:desk|counter)|information[\s_-]*(?:desk|kiosk|stand)|retail[\s_-]*(?:stand|display|rack|counter)|promotional[\s_-]*(?:stand|display)|exhibition[\s_-]*(?:panel|furniture|display|counter)|booth[\s_-]*(?:counter|table|wall|furniture)|pedestal|podium|plinth|lightbox|light[\s_-]*box|truss|freestanding[\s_-]*sign|digital[\s_-]*signage|sign[\s_-]*stand|poster[\s_-]*stand|display[\s_-]*screen|backdrop|lectern)\b',re.I)
SUPPORT=re.compile(r'\b(?:sofa|armchair|office[\s_-]*chair|dining[\s_-]*chair|modern[\s_-]*chair|lounge[\s_-]*chair|chair|stool|bench|meeting[\s_-]*table|coffee[\s_-]*table|side[\s_-]*table|table|desk|cabinet|shelf|shelving|lounge|lamp|spotlight|floor[\s_-]*lamp|pendant[\s_-]*lamp|monitor|television|tv[\s_-]*screen|projector|led[\s_-]*screen|lcd[\s_-]*screen|signage|plant[\s_-]*pot|potted[\s_-]*plant|office[\s_-]*furniture|display[\s_-]*furniture|kiosk|screen|banner|panel)\b',re.I)
EXCLUDE=re.compile(r'\b(?:weapon|gun|pistol|rifle|knife|blade|sword|armor|armour|tank|soldier|war|battle|skull|corpse|zombie|minecraft|roblox|fortnite|pokemon|anime|medieval|fantasy|nsfw|explicit|slot[\s_-]*machine|gore|gambling|poker|blood)\b',re.I)
AIFLAG=re.compile(r'\b(?:ai[\s_-]*generated|made[\s_-]*with[\s_-]*ai|text[\s_-]*to[\s_-]*3d|tripo[\s_-]*ai|meshy[\s_-]*ai|sloyd[\s_-]*ai|generated[\s_-]*by[\s_-]*ai|luma[\s_-]*genie)\b',re.I)
def scan(path):
 for attempt in range(3):
  try:
   r=requests.get(FILES+path,headers=HEADERS,timeout=38);r.raise_for_status()
   obj=json.loads(gzip.decompress(r.content));result=[];num=collections.Counter()
   for uid,v in obj.items():
    num['all']+=1
    if not v.get('isDownloadable') or v.get('isAgeRestricted'):continue
    lic=v.get('license')
    slug=lic.get('slug') if isinstance(lic,dict) else (lic if isinstance(lic,str) else '')
    if slug not in ('by','cc0'):continue
    num['permissive']+=1
    name=str(v.get('name') or '').strip();description=str(v.get('description') or '').strip()[:1200]
    taglist=[str(t.get('slug') or t.get('name') or '') for t in v.get('tags') or [] if isinstance(t,dict)]
    catlist=[str(t.get('name') or '') for t in v.get('categories') or [] if isinstance(t,dict)]
    tags=' '.join(taglist)
    if not name or AIFLAG.search(name+' '+tags+' '+description):continue
    if EXCLUDE.search(name):continue
    faces=int(v.get('faceCount') or 0)
    views=int(v.get('viewCount') or 0)
    likes=int(v.get('likeCount') or 0)
    if faces<500 or faces>4000000:continue
    if FULL.search(name) or FULL.search(tags):
      tier='COMPLETE_BOOTH_CANDIDATE';priority=900
    elif ENV.search(name) or ENV.search(tags):
      tier='EXHIBITION_RETAIL_ENVIRONMENT';priority=700
    elif FIXTURE.search(name) or FIXTURE.search(tags):
      tier='DISPLAY_OR_STAND_COMPONENT';priority=540
    elif SUPPORT.search(name) or SUPPORT.search(tags):
      tier='FURNITURE_OR_BOOTH_FIXTURE';priority=340
    else:continue
    # Source metadata pre-dates the peak of general 3D AI, but a hard
    # "human-made" guarantee would require an individual artist audit.
    if faces<1800 and tier!='COMPLETE_BOOTH_CANDIDATE':continue
    if views<40 and likes<2 and not v.get('staffpickedAt'):continue
    user=v.get('user') or {}
    creator=str(user.get('username') or 'Unknown') if isinstance(user,dict) else 'Unknown'
    if not creator or creator=='Unknown':continue
    top=sorted((v.get('thumbnails') or {}).get('images') or [],key=lambda x:abs(int(x.get('width',0))-720))
    thumbnail=str(top[0]['url']) if top else ''
    score=priority+min(120, math.log1p(views)*15)+min(110, math.sqrt(max(likes,0))*8)+min(30,math.log1p(faces)*2)
    if v.get('staffpickedAt'):score+=85
    if 'low-poly' in tags or 'lowpoly' in tags:score-=35
    if len(taglist)>=6:score+=8
    if 'architecture' in catlist:score+=10
    result.append({
     'uid':uid,'title':name[:210],'creator':creator,'creator_uid':str(user.get('uid') or ''),
     'tier':tier,'score':round(score,2),'archive_license':slug,
     'views':views,'likes':likes,'faces':faces,'thumbnail':thumbnail,
     'tags':taglist[:18],'categories':catlist[:8],
     'sketchfab_url':v.get('viewerUrl') or 'https://sketchfab.com/models/'+uid,
     'source_metadata_shard':path,'status':'METADATA_CANDIDATE_NOT_DOWNLOADED',
     'human_authorship_verified':False,'source_file_validated':False,
    })
    num[tier]+=1
   return (num,result,None)
  except Exception as e:
   if attempt==2:return collections.Counter(),[],path+': '+str(e)[:140]
   time.sleep(.8*(attempt+1))
def main():
 resp=requests.get(API,headers=HEADERS,timeout=25);resp.raise_for_status()
 files=sorted(x['path'] for x in resp.json() if str(x.get('path','')).endswith('.json.gz'))
 if len(files)<100:raise RuntimeError('Metadata list unexpectedly short')
 counts=collections.Counter();candidates=[];errors=[]
 print('SCANNING',len(files),'source metadata shards',flush=True)
 with cf.ThreadPoolExecutor(max_workers=10) as pool:
  fs=[pool.submit(scan,f) for f in files]
  for i,future in enumerate(cf.as_completed(fs),1):
   nums,found,error=future.result();counts.update(nums);candidates.extend(found)
   if error:errors.append(error)
   if i%20==0 or i==len(files):
    print('SCAN',i,'/',len(files),'OPEN',counts['permissive'],'USEFUL',len(candidates),
          'STANDS',counts['COMPLETE_BOOTH_CANDIDATE'],'ERRORS',len(errors),flush=True)
 byid={c['uid']:c for c in candidates}
 sorted_candidates=sorted(byid.values(),key=lambda v:-v['score'])
 # Every creator and each item title can contribute a few unique assets,
 # preventing one prolific source or repeated text from dominating.
 creator_counts=collections.Counter();title_counts=collections.Counter();selected=[]
 per_tier=collections.Counter()
 for row in sorted_candidates:
  if creator_counts[row['creator']]>=65:continue
  key=re.sub(r'[^a-z0-9]+',' ',row['title'].lower()).strip()
  if title_counts[key]>=38:continue
  selected.append(row);creator_counts[row['creator']]+=1;title_counts[key]+=1;per_tier[row['tier']]+=1
  if len(selected)>=5000:break
 summary={
  'source':'Objaverse-1.0 — historically downloadable CC BY and CC0 Sketchfab uploads',
  'total_metadata_rows':counts['all'],'permissive_downloadable_historical':counts['permissive'],
  'models_relevant_to_exhibition_stands_retail_fixtures':len(byid),
  'top_5000_candidate_metadata':len(selected),
  'by_tier_before_quality_ranking':{k:counts[k] for k in ('COMPLETE_BOOTH_CANDIDATE','EXHIBITION_RETAIL_ENVIRONMENT','DISPLAY_OR_STAND_COMPONENT','FURNITURE_OR_BOOTH_FIXTURE')},
  'top_5000_by_tier':dict(per_tier),
  'failed_shards':errors,
  'warning':'These records are historical metadata only and are NOT local model files. Quality, art provenance, current CC licence and file download must all be independently validated before a model is counted as ingested.'
 }
 (OUT/'real_3d_5000_source_candidates.json').write_text(json.dumps({'summary':summary,'candidates':selected},ensure_ascii=False,indent=2),encoding='utf8')
 print('TOTAL_SELECTED',len(selected),'BREAKDOWN',dict(per_tier),flush=True)
 print('TOP_25',[(v['tier'],v['title'][:52],v['views']) for v in selected[:25]],flush=True)
if __name__=='__main__':main()
