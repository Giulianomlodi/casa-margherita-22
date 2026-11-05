"""Build layered solids from the survey drawing. Coordinates in the source are pixels at 0.0254 m/px."""
from pathlib import Path
import json, ast
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
ROOT=Path(__file__).resolve().parent.parent
src=(ROOT/'scripts/planimetria.py').read_text(encoding='utf8')
drawing={}
for node in ast.parse(src).body:
 if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
  try:drawing[node.targets[0].id]=ast.literal_eval(node.value)
  except (ValueError,TypeError):pass
room_names=['wc','terr','k','liv','entry','rip','big','small','stairs']
rooms={s:drawing[s] for s in room_names}
doors=[(92,231,24,16),(143,231,26,16),(170,331,15,38),(81,598,44,31),(140,636,14,40),(199,620,38,13),(244,638,6,32),(195,796,37,22),(329,796,20,23),(324,826,6,31)]
windows=[(91,91,19,16),(207,231,109,16),(212,1003,57,17)]
sloped=[(360,994),(398,982),(402,995),(364,1005)]
def b(r):
 x,y,w,h=r;return box(x,y,x+w,y+h)
def surface(g):
 vertices=[];faces=[];sides=[];index={}
 def vertex(pt):
  key=tuple(round(v,5) for v in pt[:2])
  if key not in index:index[key]=len(vertices);vertices.append(key)
  return index[key]
 polys=[g] if g.geom_type=='Polygon' else [x for x in getattr(g,'geoms',[]) if x.geom_type=='Polygon']
 for p in polys:
  if p.area<.005:continue
  for triangle in constrained_delaunay_triangles(p).geoms:
   faces.append([vertex(pt) for pt in list(triangle.exterior.coords)[:3]])
  for ring in [p.exterior,*p.interiors]:
   seq=list(ring.coords);sides.extend([[vertex(a),vertex(b)] for a,b in zip(seq,seq[1:])])
 return dict(v=vertices,f=faces,e=sides)
def layered(n):
 face=Polygon(drawing['outer']).difference(unary_union([Polygon(r) for r in rooms.values()]))
 if n==2:face=face.difference(box(324.7,816.9,329.3,1004.1))
 cuts=[(b(r),0,2.75) for r in doors if not(n==2 and r==doors[-1])]
 cuts +=[(b(windows[0]),2.0,2.8),(b(windows[1]),.86,2.78),(b(windows[2]),0,3.05),(Polygon(sloped),0,3.05)]
 # The outer north and east lines of the open terrace are parapets, unlike its blind end.
 cuts +=[(box(120,88,357,106.01),.23,5),(box(338.99,103,358,232.01),.23,5)]
 layers=[];levels=sorted({0,4.24,*[z for _,a,b_ in cuts for z in (a,b_) if z<=4.24]})
 for lo,hi in zip(levels,levels[1:]):
  g=face.difference(unary_union([shape for shape,a,b_ in cuts if a<hi and b_>lo]))
  layers.append([lo,hi,surface(g)])
 return layers
garage_outer=[(63,125),(369,125),(369,467),(76,467)]
garage_inner=[(80,140),(177,140),(177,144),(201,144),(201,140),(353,140),(353,244),(349,244),(349,266),(353,266),(353,441),(201,441),(201,429),(177,429),(177,441),(94,441),(87,266),(91,266),(91,244),(85,244)]
garage_face=Polygon(garage_outer).difference(Polygon(garage_inner))
data=dict(rooms=rooms,outer=drawing['outer'],balcony=drawing['balc'],doors=doors,sloped=sloped,windows=windows,
 walls={str(i):layered(i) for i in (0,2)},floors={k:surface(Polygon(v)) for k,v in rooms.items()},balconyFloor=surface(Polygon(drawing['balc'])),garageFloor=surface(Polygon(garage_inner)),garageInner=garage_inner,
 garageWalls=[[0,3.06,surface(garage_face.difference(box(226,124,352,141)))],[3.06,4.35,surface(garage_face)]])
(ROOT/'scripts'/'geometry.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
