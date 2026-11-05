"""Architectural drawing primitives shared by the annotated SVGs and metre-based DXFs."""
import json,math,html
from pathlib import Path
from xml.etree import ElementTree as ET
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'geometry.json').read_text(encoding='utf8'))
CASES=json.loads((HERE/'mezzanines.json').read_text(encoding='utf-8-sig'))
OUT=HERE/'output';(OUT/'tavole').mkdir(parents=True,exist_ok=True);(OUT/'CAD').mkdir(exist_ok=True)
S=.0254
ink='#30473e';lite='#c8cfc4';paper='#faf9f2';wood='#e8cfa8';aqua='#c8ddd4';green='#3f735f';red='#a55e3d';stone='#e8e7db';gray='#77857b';ivory='#fffdf4'
def it(v,n=2):return f'{v:.{n}f}'.replace('.',',')
class Drawing:
 def __init__(self,bounds,section=False):
  self.shape=[];self.bounds=bounds;self.section=section
 def poly(self,pts,fill='none',stroke=ink,width=1,layer='ARREDI',dash=''):
  self.shape.append(('polygon',list(pts),fill,stroke,width,layer,dash))
 def rect(self,x,y,w,h,fill='none',stroke=ink,width=1,layer='ARREDI',dash=''):
  self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],fill,stroke,width,layer,dash)
 def line(self,a,b,col=ink,width=1,layer='ARREDI',dash=''):
  self.shape.append(('line',[a,b],'none',col,width,layer,dash))
 def circle(self,x,y,r,fill,stroke='none',width=1,layer='ARREDI'):
  self.shape.append(('circle',(x,y,r),fill,stroke,width,layer,''))
 def text(self,x,y,label,size=15,col=ink,layer='TESTI',anchor='middle'):
  self.shape.append(('text',(x,y,label,size,anchor),'none',col,0,layer,''))
 def marker(self,x,y,n):
  self.circle(x,y,11.8,ink,ivory,1.4,'TESTI');self.text(x,y+4.6,str(n),13,ivory)
 def svg(self):
  x,y,w,h=self.bounds;out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}">']
  for typ,p,fill,col,sw,ly,dash in self.shape:
   if typ=='text':
    X,Y,st,size,align=p;out.append(f'<text x="{X}" y="{Y}" fill="{col}" text-anchor="{align}" font-family="Arial, sans-serif" font-size="{size}">{html.escape(st)}</text>');continue
   fmt=f'fill="{fill}" stroke="{col}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"'+(f' stroke-dasharray="{dash}"' if dash else '')
   if typ=='circle':out.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="{p[2]}" {fmt}/>')
   else:
    coords=' '.join(f'{a:.3f},{b:.3f}' for a,b in p);tag='polygon' if typ=='polygon' else 'polyline';out.append(f'<{tag} points="{coords}" {fmt}/>')
  return ''.join(out)+'</svg>'
 def write(self,name):
  (OUT/'tavole'/(name+'.svg')).write_text(self.svg(),encoding='utf8')
  doc=ezdxf.new('R2010');doc.units=units.M;ms=doc.modelspace()
  layers={'ESISTENTE':7,'SOTTOSTANTE':8,'ARREDI':32,'SOPPALCO':3,'SCALA_NUOVA':30,'SERRAMENTI':4,'SEZIONE':1,'TESTI':5}
  for ly,num in layers.items():doc.layers.add(ly,color=num)
  def world(x,y):return ((x-55)/64,(402-y)/64) if self.section else ((x-49)*S,(1055-y)*S)
  for typ,p,fill,col,sw,ly,dash in self.shape:
   if ly=='CAMPITURA':continue
   attr={'layer':ly}
   if typ=='text':
    x,y,label,size,anchor=p;al={'middle':TextEntityAlignment.CENTER,'start':TextEntityAlignment.LEFT,'end':TextEntityAlignment.RIGHT}[anchor]
    ms.add_text(label,height=size*(1/64 if self.section else S)*.55,dxfattribs=attr).set_placement(world(x,y),align=al)
   elif typ=='circle':ms.add_circle(world(p[0],p[1]),p[2]*(1/64 if self.section else S),dxfattribs=attr)
   elif typ=='line':ms.add_line(world(*p[0]),world(*p[1]),dxfattribs=attr)
   elif col!='none':ms.add_lwpolyline([world(*pt) for pt in p],close=True,dxfattribs=attr)
  doc.set_modelspace_vport(height=11 if self.section else 31,center=(5,3 if self.section else 12));doc.saveas(OUT/'CAD'/(name+'.dxf'))
def arrow(d,a,b,c=green):
 d.line(a,b,c,2.2,'SCALA_NUOVA')
 angle=math.atan2(b[1]-a[1],b[0]-a[0])
 points=[b]+[(b[0]-9*math.cos(angle+t),b[1]-9*math.sin(angle+t)) for t in (-.48,.48)]
 d.poly(points,c,c,1,'SCALA_NUOVA')
def table(d,x,y,w,h):
 for xx in (x+w*.25,x+w*.75):
  for yy in (y-7,y+h-3):d.rect(xx-6,yy,12,10,'#e9d6ba',gray,.9)
 d.rect(x,y,w,h,wood,gray,1.2)
def bed(d,x,y,w,h):
 d.rect(x,y,w,h,'#e5e8dd',gray,1.3);d.rect(x+2,y+2,w-4,16,ivory,gray,.7);d.line((x,y+25),(x+w,y+25),gray,.9)
def plant(d,x,y,r):
 for a in (0,1.3,2.5,3.75,5.1):d.circle(x+math.cos(a)*r*.45,y+math.sin(a)*r*.45,r*.57,'#b4c6a8','#789176',.8)
def deck_stair(d,c,upper):
 x,y,w,h=c['deck'];sx,top,di,n,g,sw=c['flight'];right=sx+sw/S;foot=top-di*(n-1)*g/S
 if upper:
  d.rect(x,y,w,h,'#d4e4d5',green,2.4,'SOPPALCO')
  for yy in range(int(y+7),int(y+h),7):d.line((x+2,yy),(x+w-2,yy),'#aec6b4',.7,'CAMPITURA')
 else:d.rect(x,y,w,h,'none',red,2.0,'SOPPALCO','8 5')
 d.rect(sx,min(foot,top),sw/S,abs(foot-top),'#ebdeca',red,1.6,'SCALA_NUOVA')
 for j in range(n-1):
  Y=foot+di*g*j/S;d.line((sx,Y),(right,Y),red,1,'SCALA_NUOVA')
 arrow(d,((sx+right)/2,foot+di*4),((sx+right)/2,top-di*4),red)
 if upper:
  d.line((sx,top),(right,top),'#d4e4d5',3.3,'SCALA_NUOVA')
  d.rect(sx,top if di==1 else top-sw/S,sw/S,sw/S,'none',red,1.1,'SOPPALCO','3 3')
  if c['upperSeat']:
   for X in [244,292]:d.rect(X-11,552,22,25,'#a6b8a0',green,1.1)
   d.circle(266,577,7,wood,gray,1)
  if c['office']:
   for j in range(3):d.rect(x+3,y+3+j*19,14,17,'#b2c1ac',gray,1)
  if c['upperDesk']:
   d.rect(168,504,52,25,wood,gray,1);d.rect(191,534,15,11,'#a4b59d',green,1)
  d.text(x+w/2,y+h/2+7,'+'+it(c['level']),14,green)
 return foot
def house(id,upper=False):
 c=CASES[id];v=c['base'];d=Drawing((14,24,480,1076));rm=DATA['rooms']
 d.poly(DATA['balcony'],'#f4f1e6',lite,1.5,'SOTTOSTANTE' if upper else 'ESISTENTE')
 for k,p in rm.items():d.poly(p,('#f6f5ed' if upper else {'terr':aqua,'liv':'#eee6d3','wc':'#dce8e6','k':'#e8dbc0','stairs':'#e2e3d8'}.get(k,'#eceee3')),'none',0,'CAMPITURA')
 wall=next(p for lo,hi,p in DATA['walls']['2' if v==2 else '0'] if lo<=1.15<hi)
 for f in wall['f']:d.poly([wall['v'][j] for j in f],lite if upper else ink,lite if upper else ink,.35,'CAMPITURA')
 for u,vv in wall['e']:d.line(wall['v'][u],wall['v'][vv],lite if upper else ink,1 if upper else 1.3,'SOTTOSTANTE' if upper else 'ESISTENTE')
 if v==2:d.rect(279,817,4,187,lite if upper else green,lite if upper else green,1,'SOTTOSTANTE' if upper else 'ESISTENTE')
 for j in range(21):d.line((94,710+12*j),(141,710+12*j),lite if upper else gray,1,'SOTTOSTANTE' if upper else 'ESISTENTE')
 if not upper:
  d.rect(132,107,206,122,'none',green,2.3,'SERRAMENTI');table(d,182,154,59,28);plant(d,315,125,12);plant(d,311,207,10)
  d.rect(66,252,24,186,wood,gray,1);d.rect(70,267,14,26,aqua,gray,1);d.rect(69,369,17,25,ink)
  for x,y,w,h in [(68,109,46,30),(68,159,16,21),(68,197,20,22),(251,707,21,24),(251,766,25,26)]:d.rect(x,y,w,h,ivory,gray,1)
  for a,b in [((250,697),(291,697)),((291,697),(291,709)),((291,742),(291,796))]:d.line(a,b,green,2.4,'ESISTENTE')
  if id=='P06':
   bed(d,155,864,62,78);bed(d,293,878,36,78)
   d.line((184,389),(338,389),green,2,'SERRAMENTI')
  else:
   bed(d,165 if id=='P07' else 248,881,64,79);sy=325 if id=='P07' else 411;d.line((185,sy),(242,sy),green,2,'SERRAMENTI')
  if c['office']:
   for X in (218,260):d.rect(X,256,39,22,wood,gray);d.rect(X+12,284,14,12,'#a4b59d',green)
   d.rect(320,333,13,82,wood,gray)
  if c['couch']:
   X,Y,rot=c['couch'];ww,hh=(29,70) if rot==90 else (70,29);d.rect(X-ww/2,Y-hh/2,ww,hh,'#b9c9b7',gray,1.3)
  table(d,*c['dining']);d.rect(336,936,34,9,wood,gray)
  for a,b in [((91,99),(110,99)),((207,239),(316,239)),((212,1011),(269,1011)),((362,1000),(400,988))]:d.line(a,b,green,2,'SERRAMENTI')
  for x,y,n in [(93,149,1),(248,192,2),(100,457,3),(192,437,4),(199,703,5),(273,650,6),(232,844,7),(352,901,8)]:d.marker(x,y,n)
 deck_stair(d,c,upper)
 if not upper:
  X=c['flight'][0]+c['flight'][5]/S/2;d.line((X,252),(X,619),red,.9,'SEZIONE','10 6 2 6');d.text(X+6,614,'A',15,red,'SEZIONE','start')
 else:
  d.text(212,733,'VUOTO',15,gray);d.text(235,923,'PIANO',14,gray);d.text(235,943,'SOTTOSTANTE',14,gray)
 d.text(214,78,'RETRO  /  GIARDINO',14,green);d.text(262,1082,'BALCONE  /  PIAZZA',14,green)
 d.line((62,43),(94,62),ink,1.5,'TESTI');d.text(48,46,'N',13)
 for i in range(2):d.rect(296+i*39.37,53,39.37,4,ink if not i else ivory,ink,.6,'TESTI')
 d.text(296,73,'0',11);d.text(375,73,'2 m',11)
 return d
def section(id):
 c=CASES[id];n=c['flight'][3];g=c['flight'][4];level=c['level'];h=c['depth'];deckdepth=c['deck'][3]*S
 sc=64;xo=119;yo=402;top=xo+(n-1)*g*sc;edge=top+deckdepth*sc;maxx=max(edge+68,655);d=Drawing((0,-12,maxx+22,478),True)
 def z(v):return yo-v*sc
 d.line((48,z(4.20)),(maxx,z(4.20)),gray,1.9,'SEZIONE','8 5')
 d.text(50,z(4.2)-8,'4,20 m · altezza media della scheda',14,gray,'SEZIONE','start')
 required=level+c['upperTarget']
 if id!='P06':
  d.line((top-8,z(required)),(edge+30,z(required)),red,1.6,'SEZIONE','5 4')
  d.text(edge+28,z(required)-8,it(required)+' m richiesti¹',13,red,'SEZIONE','end')
 d.rect(55,yo,maxx-64,9,ink,ink,1,'ESISTENTE');d.rect(top,z(level),deckdepth*sc,h*sc,wood,red,1.8,'SOPPALCO')
 if id=='P06':d.rect(top,z(level-h),deckdepth*sc, (level-h)*sc,'#e5d3b5',gray,1,'SOPPALCO')
 else:
  for X in (top+4,edge-5):d.rect(X,z(level-h),3,(level-h)*sc,'#51645b',gray,.8,'SOPPALCO')
 zstep=level/n
 for j in range(n-1):
  X=xo+j*g*sc;d.line((X,z(j*zstep)),(X,z((j+1)*zstep)),ink,1.2,'SCALA_NUOVA')
  d.rect(X,z((j+1)*zstep),g*sc,3,wood,red,.8,'SCALA_NUOVA')
 d.line((xo,z(zstep+1.0)),(top,z(level+1.05)),red,2,'SCALA_NUOVA')
 d.line((top,z(level+1.05)),(edge,z(level+1.05)),red,1,'SOPPALCO')
 for j in range(0,n-1,2):
  X=xo+j*g*sc;d.line((X,z((j+1)*zstep)),(X,z((j+1)*zstep+1.00)),gray,1,'SCALA_NUOVA')
 for j in range(0,round(deckdepth*sc),11):d.line((top+j,z(level)),(top+j,z(level+1.05)),gray,.8,'SOPPALCO')
 # The grey reference silhouette is a 1.70 m standing person; its intersection is visible.
 X=top+deckdepth*sc*.52;head=z(level+1.58)
 d.circle(X,head,.12*sc,'none',ink,1.4,'SEZIONE');d.line((X,head+8),(X-1,z(level+.74)),ink,2,'SEZIONE')
 for k in (-1,1):d.line((X-1,z(level+.74)),(X+k*7,z(level)),ink,1.7,'SEZIONE');d.line((X,z(level+1.28)),(X+k*9,z(level+.86)),ink,1.4,'SEZIONE')
 dimx=edge+17
 for lo,hi,label in [(0,level-h,it(level-h)),(level,4.20,it(4.20-level))]:
  d.line((dimx,z(lo)),(dimx,z(hi)),green,1.2,'SEZIONE')
  for val in [lo,hi]:d.line((dimx-4,z(val)),(dimx+4,z(val)),green,1.2,'SEZIONE')
  d.text(dimx+7,(z(lo)+z(hi))/2+4,label,13,green,'SEZIONE','start')
 d.text(top+4,z(level)+h*sc+17,'+'+it(level)+' m',13,red,'SEZIONE','start')
 d.text(xo+(top-xo)/2,yo+29,'corsa '+it((n-1)*g)+' m',13,red)
 d.text(top+deckdepth*sc/2,yo+46,'impalcato '+it(deckdepth)+' m',13,green)
 d.line((xo,yo+13),(top,yo+13),red,1,'SEZIONE')
 return d
if __name__=='__main__':
 for id in CASES:
  house(id).write(id+'_L0');house(id,True).write(id+'_L1');section(id).write(id+'_AA')
