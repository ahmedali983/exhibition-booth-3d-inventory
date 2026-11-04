#!/usr/bin/env python3
"""Build creator-contact shortlist for REAL EXHIBITION BOOTH designs.

Metadata only. Never downloads any scene geometry or mines private contact data.
All records start with rights_status='permission_not_verified'.
"""
import csv,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
records=[]
for filename in ['sketchfab_index.json','creator_discovery.json']:
    records.extend(json.loads((ROOT/'catalog'/filename).read_text(encoding='utf-8')).get('items',[]))
seen=set()
ranks=[]
for asset in records:
    if asset.get('id') in seen:continue
    seen.add(asset['id'])
    name=(asset.get('title') or '').strip()
    t=name.lower()
    positive=[
        ('exhibition booth',80),('exhibition stand',80),('expo stand',74),('expo booth',74),
        ('trade show booth',73),('trade show stand',73),('tradeshow',63),('trade fair booth',66),
        ('exhibit booth',68),('modular exhibition',62),('event booth',50),
        ('pavilion',34),('exhibition interior',33),('showroom',25),('kiosk',20)
    ]
    score=sum(w for phrase,w in positive if phrase in t)
    score=min(score,100)
    if re.search(r'\b(3d design|corporate|shell scheme|island|peninsula|custom|truss|panel)\b',t):score+=10
    if re.search(r'\b(dj|nightclub|photobooth|photo booth|guard booth|voting|phone booth|sound booth|game|anime|toy|character|tabletop)\b',t):score-=70
    score+=min(10,int((asset.get('view_count') or 0)**.22))
    if score<30:continue
    author=(asset.get('author') or 'Unknown').strip()
    profile=asset.get('author_url') or ('https://sketchfab.com/'+author if author!='Unknown' else '')
    ranks.append({
        'priority_score':score,'model_id':asset['id'],'title':name,'creator':author,
        'source_model':asset.get('url') or '','creator_profile':profile,
        'license_as_indexed':asset.get('license') or 'Unknown',
        'source_download_flag':bool(asset.get('is_downloadable')),
        'rights_status':'PERMISSION_NOT_VERIFIED',
        'required_grant':'Public hosting and direct downloadable GLB file redistribution; modifications and team access',
        'contact_method':'Creator profile or original business website; do not scrape private details',
        'project_stage':'Research lead only — no original GLB hosted',
    })
ranks.sort(key=lambda x:(-x['priority_score'],x['title'].lower()))
ranks=ranks[:200]
target=ROOT/'catalog'/'creator_booth_permission_shortlist.csv'
with target.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(ranks[0]));writer.writeheader();writer.writerows(ranks)
print('Created',len(ranks),'public creator-model leads',target,flush=True)
