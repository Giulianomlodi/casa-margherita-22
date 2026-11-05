from pathlib import Path
import json,struct,math
import numpy as np
import ezdxf,ifcopenshell
from scipy.spatial.transform import Rotation
from shapely.geometry import box
from design import *
d=Path(__file__).resolve().parents[1]/'due-camere'
for v in 'FL':
 b=(d/(v+'.glb')).read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);raw=memoryview(b)[28+n:];records={k:[] for k in NAMES}
 def visit(i,p):
  node=j['nodes'][i];m=np.eye(4)
  if 'matrix' in node:m=np.array(node['matrix']).reshape(4,4).T
  else:
   m[:3,:3]=Rotation.from_quat(node.get('rotation',[0,0,0,1])).as_matrix()@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0])
  m=p@m;e=node.get('extras',{});k=e.get('camera_alta')
  if k in NAMES and ' | letto' in node.get('name','') and 'mesh' in node:
   pts=[];px,py=ORIGIN[k]
   for prim in j['meshes'][node['mesh']]['primitives']:
    acc=j['accessors'][prim['attributes']['POSITION']];bv=j['bufferViews'][acc['bufferView']]
    xyz=np.ndarray((acc['count'],3),'<f4',buffer=raw,offset=bv.get('byteOffset',0)+acc.get('byteOffset',0),strides=(bv.get('byteStride',12),4))@m[:3,:3].T+m[:3,3]
    pts.append(np.stack((xyz[:,0]-(px-215)*S,xyz[:,2]-(py-550)*S,xyz[:,1]),axis=1))
   records[k].append(np.vstack(pts))
  for c in node.get('children',[]):visit(c,m)
 for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,np.eye(4))
 for k,parts in records.items():
  assert len(parts)==12,(v,k,len(parts))
  pts=np.vstack(parts);lo=pts.min(axis=0);hi=pts.max(axis=0)
  assert abs(lo[2]-LEVEL[v])<.035 and hi[2]<LEVEL[v]+1.23,(v,k,lo,hi)
  assert .87<hi[0]-lo[0]<.906 and 1.95<hi[1]-lo[1]<2.006,(v,k,lo,hi)
  r=DATA[v][k];net=box(*r['deck']).buffer(-.08,join_style=2);foot=box(lo[0],lo[1],hi[0],hi[1]);assert net.covers(foot) and not foot.intersects(box(*r['land'])) and not foot.intersects(box(*r['ward']))
  print(v,k,'letto esportato',np.round(hi-lo,3),'quota',round(lo[2],3))
 for label in ['L0','L1','sezione','sezione-piazza']:
  cad=ezdxf.readfile(d/(v+'-'+label+'.dxf'));assert cad.units==6 and not cad.audit().errors
 f=ifcopenshell.open(str(d/(v+'.ifc')));assert len(f.by_type('IfcSpace'))==2 and len(f.by_type('IfcBuildingStorey'))==2
 stairs=sorted(ob.NumberOfRisers for ob in f.by_type('IfcStairFlight') if ' | Rampa' in ob.Name)
 assert stairs==([5,12,17] if v=='F' else [6,6]),stairs
