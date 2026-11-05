from pathlib import Path
import json,html,math,shutil,base64
from shapely.geometry import Polygon,box
from shapely import affinity
D=Path(__file__).resolve().parent;out=D.parent/'decisioni';au=json.loads((out/'audit.json').read_text(encoding='utf8'));options=json.loads((D/'variants.json').read_text(encoding='utf-8-sig'));s=au['scale']
def wr(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf8')
au['findings'][0]='Il vano a cuneo misura circa 8 m². In tre sezioni trasversali (righe 819, 900 e 965 del ritaglio) la larghezza grafica passa da circa 0,60 a 1,89 e 2,90 m. Il DOCFA lo identifica come ripostiglio.'
au['findings'][1]='Idealista riporta 157 m² calpestabili. Il modello 1NB totalizza 112 m² utili e il ricalcolo restituisce circa 113 m². Lo scarto di 45 m² fra annuncio e dichiarazione richiede un rilievo prima di valutare il prezzo al metro.'
au['sources'][2][2]='Riporta 165 m² commerciali e 157 calpestabili: 45 in più dei 112 utili DOCFA. Foto segnalata come modificata IA, esclusa dalla misura.'
au['units'].insert(1,dict(label='Scarto con la pubblicità',doc='157 m² calpestabili · Idealista',draw='45 m² rispetto al DOCFA',note='Chiedere il conteggio analitico e un rilievo. Non ridimensionare la pianta per forzarla a 157.'))
wr(out/'audit.json',au)
for id,o in options.items():o.update(id=id,link='/decisioni/atlante.html?variante='+id,photo='/decisioni/'+id+'-'+{'A':'fronte','B':'detail','C':'detail','D':'detail','E':'fronte'}[id]+'.webp')
wr(out/'case.json',dict(houses=[dict(id='margherita',name='Casa Margherita',place='San Gregorio di Catania',hero='/materiali/f01.jpg',options=list(options.values()),area='112 m² utili dichiarati',rooms='1 · proposta A',garage='Separato · 52 m² utili')]))
g=json.loads((D.parents[1]/'Sorgenti_3D/scripts/geometry.json').read_text());rooms=au['polygons']
def optrect(id):
 base=[('Guard.',(330,899,344.6,960),'small'),('Cucina',(65.1,252,93,362),'k'),('Giardino',(182,154,241,182),'terr')]
 if id!='E':base+=[('Letto',(240.5,880,319.5,942),'big')]
 if id in ('A','C','E'):base+=[('Pranzo',(220,483,293,521),'liv')]
 else:base+=[('Pranzo',(211,413.5,249,486.5),'liv')]
 if id=='A':base+=[('Divano',(230,268.4,316,309.6),'liv')]
 if id in ('B','D'):base+=[('Divano',(279.4,505,320.6,591),'liv')]
 if id=='B':base+=[('Singola',(279,264,315,343),'liv')]
 if id=='C':base+=[('Pedana',(270,264,338,379),'liv'),('Scala',(237,267,270,303),'liv'),('Poltrona',(284,318,319.3,352),'liv')]
 if id=='D':base+=[('Scrivania',(203,251,258,278),'liv'),('Scrivania',(265,251,320,278),'liv')]
 if id=='E':base+=[('Letto',(247,253,310,332),'liv'),('Divano',(247.4,852,288.6,938),'big')]
 return base
def text(x,y,t,size=8,color='#1d3631'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="middle">{html.escape(t)}</text>'
for id in options:
 fh=optrect(id);shapes=[]
 # check footprints against independently measured contours (two raster pixels reading margin).
 for n,(x,y,X,Y),k in fh:
  assert Polygon(rooms[k]).buffer(2).covers(box(x,y,X,Y)),(id,n)
 pairs=[]
 for i,v in enumerate(fh):
  for w in fh[i+1:]:
   if {v[0],w[0]}=={'Pedana','Poltrona'}:continue
   assert box(*v[1]).intersection(box(*w[1])).area<1,(id,v,w)
 for n,(x,y,X,Y),k in fh:
  fill='#cfb399' if n in ('Letto','Singola') else '#c49b74' if n in ('Pedana','Scala') else '#adc5b6'
  shapes+=[f'<rect x="{x}" y="{y}" width="{X-x}" height="{Y-y}" fill="{fill}" stroke="#34493e" stroke-width=".9"/>']
  if n not in ('Pedana','Scala','Guard.'):shapes+=[text((x+X)/2,(y+Y)/2+2,n,7)]
 for name,x,y in [('RIP.',382,956),('ING.',198,719),('WC',90,169)]:shapes.append(text(x,y,name,8))
 shapes.append('<path d="M184 390H339" stroke="#b35e3f" stroke-width="2" stroke-dasharray="6 3"/>')
 # Full-height plate with raster anatomy printed legibly underneath.
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="38 78 445 991"><rect x="38" y="78" width="445" height="991" fill="#faf8f3"/><image href="data:image/png;base64,{base64.b64encode((D.parents[1]/"materiali/plan11.png").read_bytes()).decode()}" x="0" y="0" width="590" height="1105"/>'+''.join(shapes)+'</svg>'
 (out/(id+'-pianta.svg')).write_text(svg,encoding='utf8')
 # Public DXF with independent contours and the same furniture extents as the visible plan.
 import ezdxf
 doc=ezdxf.new('R2010');doc.units=6;m=doc.modelspace()
 for ln,c in [('VANI_RICALCOLATI',7),('ARREDI',3),('QUINTA_IPOTETICA',30)]:doc.layers.add(ln,color=c)
 def line(coords,layer,closed=True):m.add_lwpolyline([((x-49)*s,(1055-y)*au['scaleY']) for x,y in coords],close=closed,dxfattribs={'layer':layer})
 for k,pts in rooms.items():
  if k!='garage':line(pts,'VANI_RICALCOLATI')
 for n,(x,y,X,Y),k in fh:line([(x,y),(X,y),(X,Y),(x,Y)],'ARREDI')
 line([(184,390),(339,390)],'QUINTA_IPOTETICA',False);doc.saveas(out/(id+'.dxf'))
print('Cinque piante CAD e controllo degli ingombri')
