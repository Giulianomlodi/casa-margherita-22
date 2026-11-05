"""Common coordinate system: each room uses local metres, x right/y down on NCV364 p.11."""
from pathlib import Path
import json
S=.0254
ORIGIN={'piazza':(153,817),'retro':(184,246)}
NAMES={'piazza':'Camera sulla piazza','retro':'Camera sul retro'}
LEVEL={'F':2.92,'L':1.08}
DEPTH={'F':.22,'L':.18}
DATA={
 'F':{
 'piazza':dict(deck=[.04,.925,3.42,3.90],door=['N',1.49,2.33],bed=[.67,2.53],ward=[2.90,2.17,3.31,3.61],land=[1.47,.025,2.37,.925],turn=[3.43,.025,4.33,.925],flights=[['N',3.43,3.84,.90,12,.265],['W',3.43,.025,.90,5,.265]]),
 'retro':dict(deck=[.92,.015,3.90,3.55],door=['W',.105,.895],bed=[3.31,1.78],ward=[1.06,3.04,2.37,3.45],land=[.02,.02,.90,.90],flights=[['N',.02,5.14,.88,17,.265]])},
 'L':{
 'piazza':dict(deck=[.86,1.03,4.33,3.94],door=['N',3.37,4.19],bed=[1.49,2.53],ward=[3.82,2.34,4.22,3.68],land=[3.35,.18,4.20,1.03],flights=[['E',2.05,.18,.85,6,.26]]),
 'retro':dict(deck=[.92,.015,3.90,3.55],door=['W',.105,.895],bed=[3.31,1.78],ward=[1.06,3.04,2.37,3.45],land=[.02,.02,.90,.90],flights=[['N',.02,2.15,.88,6,.25]])}}
def rectarea(b):return (b[2]-b[0])*(b[3]-b[1])
def walk(f):
 dr,x,y,w,n,g=f
 for i in range(n-1):
  if dr=='N':yield [x,y-(i+1)*g,x+w,y-i*g]
  elif dr=='W':yield [x-(i+1)*g,y,x-i*g,y+w]
  else:yield [x+i*g,y,x+(i+1)*g,y+w]
def calc(room):
 x,y,X,Y=room['deck'];area=rectarea(room['deck']);net=(X-x-.16)*(Y-y-.16)
 run=sum(rectarea(b) for f in room['flights'] for b in walk(f))
 return dict(area=round(area,4),net=round(net,4),landing=round(rectarea(room['land']),3),ramp=round(run,3),turn=round(rectarea(room['turn']),3) if 'turn' in room else 0)
def project():
 return {v:{'quota':LEVEL[v],'spessore':DEPTH[v],'camere':{k:{**r,**calc(r)} for k,r in rooms.items()}} for v,rooms in DATA.items()}
if __name__=='__main__':
 from shapely.geometry import box,Polygon
 from shapely.ops import unary_union
 orig=Path(__file__).resolve().parent;out=orig.parent/'due-camere'
 geo=json.loads((orig.parents[1]/'R04/decisioni/audit.json').read_text(encoding='utf8'))
 for v,rooms in DATA.items():
  for k,r in rooms.items():
   dx,dy=ORIGIN[k];p=Polygon([((x-dx)*S,(y-dy)*S) for x,y in geo['polygons']['big' if k=='piazza' else 'liv']])
   net=box(*r['deck']).buffer(-.08,join_style=2);assert net.area>=9
   bx,by=r['bed'];assert net.covers(box(bx-.45,by-1,bx+.45,by+1)) and net.covers(box(*r['ward']))
   pl=box(*r['deck']);land=box(*r['land']);tolerance=.025
   assert pl.distance(land)<.021
   pieces=[box(*b) for f in r['flights'] for b in walk(f)]+[land,pl]
   if 'turn' in r:pieces.append(box(*r['turn']))
   assert all(p.buffer(tolerance).covers(b) for b in pieces),(k,v)
   assert abs(sum(b.area for b in pieces)-unary_union(pieces).area)<.0001,(k,v,'overlap')
   assert sum(f[4] for f in r['flights'])==(17 if v=='F' else 6)
   print(v,k,calc(r))
 (out/'geometria.json').write_text(json.dumps(project(),indent=2,ensure_ascii=False),encoding='utf8')
