#!/usr/bin/env python3
"""Create 4,200 locally authored booth thumbnails from the actual parameter manifest.
No third-party images are copied. Draws architectural isometric elevations with Pillow.
Run: python scripts/render_thumbnails.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pathlib, math, random, json, time

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"thumbs"
W,H=380,440
SS=1
PALETTES=[
 ("#e96d50","#f9fbfa","#cbd2ce","#ecdfd3"),("#51aebd","#f5f6f1","#c8d4dc","#e5d8c4"),
 ("#ffbb49","#1d2631","#424c57","#d4c9b7"),("#4cc9af","#f5eee9","#d1c6c4","#e7d2a7"),
 ("#ec5b79","#222632","#586270","#cad1cb"),("#bc9bfd","#f2f1ed","#c5c4ca","#ded8d6"),
 ("#f8a65a","#272c2d","#5d5e55","#ded1c0"),("#5971ce","#faf9f3","#c4c7d0","#c8c4c0"),
 ("#ca8f54","#eeece5","#d8cab9","#ded5c9"),("#9dd354","#242c28","#465849","#cfc9b9"),
 ("#c5a2fd","#fafafa","#dbd6e4","#d9d4cc"),("#48b8f0","#f5f6f7","#bbc7ce","#cfd7d8"),
]
NAMES=("PAW CLUB","NOVA","KINETIC","NORTH","FORMA","MOTION","STUDIO N","FUTURA","RISE","ATELIER","ORBIT","AURA","HABIT","ELEMENT","CLUB 24","LUMEN")
def mix(color,amt):
 c=tuple(int(color.lstrip('#')[i:i+2],16) for i in (0,2,4))
 return tuple(max(0,min(255,round(x*amt))) for x in c)
def hexrgb(color):
 return mix(color,1)
def rgba(color,a):return (*hexrgb(color),a)
def font(sz,bold=False):
 try:return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",sz)
 except OSError:return ImageFont.load_default()
TINY=font(13,True);SMALL=font(14,True);MED=font(20,True)
def render(v):
 idn=int(v["id"].split("-")[1])
 rnd=random.Random(idn*3917)
 accent,whitewall,darkwall,sand=PALETTES[idn%len(PALETTES)]
 dark=(idn//3)%5==0 or idn%len(PALETTES) in (2,4,6,9)
 wall="#242c37" if dark else whitewall
 backdrop=("#cbd7d9","#eae4d9","#d8dbe1","#e4e6df","#d4dad5","#dcd5d6")[idn%6]
 bg=Image.new("RGB",(W,H),backdrop);draw=ImageDraw.Draw(bg)
 # Gentle studio-lit gradient — not a sourced photographic render.
 R,G,B=hexrgb(backdrop)
 for y in range(H):
  factor=.92+.14*(1-y/H)
  draw.line([(0,y),(W,y)],fill=(min(255,int(R*factor)),min(255,int(G*factor)),min(255,int(B*factor))))
 # Thin grid for architectural setting
 for z in range(0,H,35):
  draw.line([(0,z),(W,z)],fill=(max(0,R-8),max(0,G-8),max(0,B-8)),width=1)
 width,depth=v["width_m"],v["depth_m"]
 sc=min(25,150/(width+depth)*1.8)
 sx=sc*1.30; sz=sc*.67; sy=sc*1.56
 ox=W*.51;oy=H*.68
 def pt(x,z,y=0):
  return (round(ox+(x-z)*sx),round(oy+(x+z)*sz-y*sy))
 def polygon(ps,col):
  draw.polygon([pt(*p) for p in ps],fill=col)
 def stroke(ps,col,width=2):
  draw.line([pt(*p) for p in ps],fill=col,width=width,joint="curve")
 def cuboid(x,z,y,wd,dp,ht,base,top=None,lightness=1):
  x1,x2=x-wd/2,x+wd/2; z1,z2=z-dp/2,z+dp/2
  p1=(x1,z1,y);p2=(x2,z1,y);p3=(x2,z2,y);p4=(x1,z2,y)
  q1=(x1,z1,y+ht);q2=(x2,z1,y+ht);q3=(x2,z2,y+ht);q4=(x1,z2,y+ht)
  polygon([p2,p3,q3,q2],mix(base,.82*lightness))
  polygon([p4,p3,q3,q4],mix(base,.95*lightness))
  polygon([q1,q2,q3,q4],hexrgb(top or base))
  stroke([q4,q3,q2],mix(base,.75),1)
 def txt(x,z,y,message,color,size=14):
  X,Y=pt(x,z,y);f=MED if size>16 else SMALL
  # Approximate original brand sign; same layout as 3D sign texture.
  bx=draw.textbbox((0,0),message,font=f)
  draw.text((X-(bx[2]-bx[0])/2,Y-(bx[3]-bx[1])/2),message,font=f,fill=color)
 draw.ellipse((56,330,360,399),fill=mix(backdrop,.86))
 # Landing platform.
 cuboid(0,0,0,width,depth,.13,sand,whitewall if not dark else "#434b55")
 # Structural elements; shallow wall on back, optional side walls.
 h=3.2
 exposure=v["booth_type"]
 if exposure!="Island":cuboid(0,-depth/2+.07,.12,width,.17,h,wall)
 if exposure in ("Corner","Inline"):cuboid(-width/2+.09,0,.12,.15,depth,h,wall)
 if exposure=="Inline":cuboid(width/2-.08,0,.12,.15,depth,h,wall)
 style=v["style"]
 if style in ("Portal","Canopy"):
  cuboid(-width/2+.2,depth/2-.22,.13,.28,.38,h,accent)
  cuboid(width/2-.2,depth/2-.22,.13,.28,.38,h,accent)
  cuboid(0,depth/2-.22,2.97,width,.38,.32,accent)
 if style=="Truss":
  for x in (-width/2+.16,width/2-.16):
   for z in (-depth/2+.16,depth/2-.16):
    cuboid(x,z,.13,.11,.11,h+.23,"#717a7c")
  for z in (-depth/2+.16,depth/2-.16):cuboid(0,z,h+.25,width,.1,.12,"#b1b8ba")
  for x in (-width/2+.16,width/2-.16):cuboid(x,0,h+.25,.12,depth,.1,"#b1b8ba")
 if style=="Canopy":cuboid(0,0,h+.18,width*.85,depth*.67,.17,whitewall if not dark else "#3b444a")
 if style=="Feature Wall":
  cuboid(0,-depth/2+.4,.25,min(width*.58,3.9),.23,2.7,accent)
  cuboid(0,-depth/2+.12,.7,min(width*.46,2.9),.34,.14,"#ffffff")
 if exposure=="Island":
  cuboid(0,0,.13,min(width*.43,3),.45,2.25,accent)
 # Fitting elements
 fit=v["fitout"]
 if fit=="Reception":
  cuboid(0,depth/2-.62,.14,min(width*.51,1.8),.63,1.02,accent,whitewall)
  cuboid(0,depth/2-.62,1.15,min(width*.52,1.9),.7,.08,whitewall)
 if fit=="Meeting":
  for x in (-1.0,1.0):
   cuboid(x,.1,.14,.45,.51,.75,accent)
  cuboid(0,.1,.86,min(width*.48,1.6),.95,.09,whitewall)
  for x in (-.56,.56):
   for z in (-.32,.32):cuboid(x,z,.12,.08,.08,.75,"#7f8a88")
 if fit=="Retail":
  for x in (-width*.24,0,width*.24):
   cuboid(x,0,.14,.7,.72,.85,wall,accent)
   cuboid(x,0,1.01,.75,.78,.09,accent)
 if fit=="Digital":
  cuboid(0,-depth/2+.28,1.14,min(width*.58,3.3),.18,1.6,accent)
  cuboid(0,-depth/2+.1,1.2,min(width*.53,3.1),.05,1.45,"#1a313f")
  cuboid(0,depth/2-.67,.14,1.5,.7,1.0,wall)
 if fit=="Storage":
  cuboid(width/2-.82,-depth/2+.88,.12,1.25,.12,2.4,accent)
  cuboid(width/2-1.48,-depth/2+.2,.12,.12,1.25,2.4,wall)
  cuboid(0,depth/2-.7,.12,1.15,.6,1.0,whitewall)
 # Highlight brand sign on visible structure.
 brand=NAMES[(idn//5)%len(NAMES)]
 if exposure!="Island":
  cuboid(0,-depth/2+.22,2.63,min(width*.7,3.2),.14,.42,"#17232b")
  txt(0,-depth/2+.45,2.94,brand,"#ffffff",20 if width>4 else 14)
 else:txt(0,.29,2.1,brand,"#fffdf7",14)
 # Light dots and detail accents, subtle architectural strokes.
 if style in ("Portal","Canopy","Truss"):
  for x in (-width*.23,0,width*.23):
   X,Y=pt(x,depth/2-.22,h+.03);draw.ellipse((X-3,Y-3,X+3,Y+3),fill="#fff3ce")
 # Foreground decorative product / planter
 if idn%4==0:
  x,z=width*.33,depth*.3
  cuboid(x,z,.13,.36,.36,.45,"#d2c5aa")
  X,Y=pt(x,z,.82);draw.ellipse((X-9,Y-20,X+9,Y+7),fill="#547b60")
 # Card header overlay and code, simple editorial treatment
 draw.rounded_rectangle((13,15,115,39),radius=8,fill="#ffffffee")
 draw.text((24,22),v["id"],fill="#253039",font=TINY)
 # Tag bottom
 label=f'{width} × {depth} m   ·   {fit.upper()}'
 bb=draw.textbbox((0,0),label,font=SMALL)
 tw=bb[2]-bb[0]+30
 draw.rounded_rectangle((14,H-51,14+tw,H-19),radius=8,fill="#ffffffee")
 draw.text((29,H-41),label,fill="#334047",font=SMALL)
 OUT.mkdir(parents=True,exist_ok=True)
 bg.save(OUT/(v["id"]+".webp"),format="WEBP",quality=81,method=4)
def main():
 start=time.monotonic()
 data=json.loads((ROOT/"catalog"/"generated_manifest.json").read_text(encoding="utf-8"))
 for i,v in enumerate(data["items"],1):
  render(v)
  if i%500==0:print("Rendered",i,"/",len(data["items"]),"in",round(time.monotonic()-start,1),"sec",flush=True)
 print("THUMBNAILS",len(list(OUT.glob("*.webp"))),"elapsed",round(time.monotonic()-start,1),flush=True)
if __name__=="__main__":main()
