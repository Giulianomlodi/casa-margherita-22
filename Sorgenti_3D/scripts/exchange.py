"""Convert the architectural components of the presentation model into a classified IFC4 exchange model."""
import struct,json,re,uuid,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import ifcopenshell as ifc
import ifcopenshell.api as api
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];dest=ROOT.parent/'Atlante_3D/modelli'
def stable(value):
 return ifc.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL,'archai/casa-margherita/'+value).hex)
def elements(path):
 data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);binary=memoryview(data)[28+length:]
 def accessor(i):
  a=doc['accessors'][i];bv=doc['bufferViews'][a['bufferView']];offset=bv.get('byteOffset',0)+a.get('byteOffset',0)
  dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];dim={'SCALAR':1,'VEC3':3}[a['type']]
  stride=bv.get('byteStride',np.dtype(dtype).itemsize*dim)
  return np.ndarray((a['count'],dim),dtype=dtype,buffer=binary,offset=offset,strides=(stride,np.dtype(dtype).itemsize))
 result=defaultdict(list)
 def visit(i,parent):
  node=doc['nodes'][i];local=np.eye(4)
  if 'matrix' in node:local=np.array(node['matrix']).reshape(4,4).T
  else:
   local[:3,:3]=Rotation.from_quat(node.get('rotation',[0,0,0,1])).as_matrix()@np.diag(node.get('scale',[1,1,1]));local[:3,3]=node.get('translation',[0,0,0])
  mat=parent@local;extra=node.get('extras',{});layer=extra.get('strato','');room=extra.get('ambiente','');name=re.sub(r'\.\d+$','',node.get('name',''))
  furniture=layer=='Arredi' and any(k in name.lower() for k in ('carrozzeria','telaio bici','banco','cassettiera','scaffale','sommier','piano in castagno','piano disegno','divano','cucina componibile','panca','mobile lavabo','piatto doccia','libreria','vaso sanitario','seduta atelier','secondo banco'))
  if 'mesh' in node and (layer in ('Struttura','Serramenti','Coperture','Quota alta') or furniture):
   for prim in doc['meshes'][node['mesh']]['primitives']:
    vs=accessor(prim['attributes']['POSITION'])@mat[:3,:3].T+mat[:3,3]
    # glTF Y is up; use right-handed Z-up building coordinates in IFC.
    vs=np.column_stack((vs[:,0],-vs[:,2],vs[:,1]));fs=accessor(prim['indices']).reshape(-1,3)
    if furniture:
     low=vs.min(axis=0);high=vs.max(axis=0)
     if np.min(high-low)<.004:continue
     vs=np.array([[x,y,z] for z in (low[2],high[2]) for y in (low[1],high[1]) for x in (low[0],high[0])])
     fs=np.array([(0,2,3),(0,3,1),(4,5,7),(4,7,6),(0,1,5),(0,5,4),(1,3,7),(1,7,5),(3,2,6),(3,6,7),(2,0,4),(2,4,6)])
    result[(room,layer,name)].append((vs,fs))
  for child in node.get('children',[]):visit(child,mat)
 for root in doc['scenes'][doc.get('scene',0)]['nodes']:visit(root,np.eye(4))
 return result
def category(name,layer):
 s=name.lower()
 if layer=='Arredi':return 'IfcFurniture'
 if 'muratur' in s or 'parete' in s or 'divisorio' in s:return 'IfcWall'
 if 'pavimento' in s or 'pianerottolo' in s or 'impalcato' in s or 'battuto' in s or 'balcone spezzato' in s:return 'IfcSlab'
 if 'gradino' in s:return 'IfcStairFlight'
 if 'pilastro' in s or 'montante indipendente' in s:return 'IfcColumn'
 if 'arco' in s or 'trave' in s or 'travetto' in s:return 'IfcBeam'
 if 'copertura' in s or 'falda' in s:return 'IfcRoof'
 if 'volta' in s:return 'IfcCovering'
 if 'parapetto' in s or 'corrimano' in s or 'bacchetta' in s:return 'IfcRailing'
 if 'anta' in s or 'porta terrazza' in s:return 'IfcDoor'
 if 'vetro' in s or 'finestra' in s:return 'IfcPlate'
 return 'IfcBuildingElementProxy'
def create_version(id):
 f=api.run('project.create_file',version='IFC4')
 def entity(cl,name):
  x=api.run('root.create_entity',f,ifc_class=cl,name=name);x.GlobalId=stable(id+'/'+cl+'/'+name);return x
 project=entity('IfcProject','Casa Margherita 22 | '+id)
 units=[api.run('unit.add_si_unit',f,unit_type=t) for t in ('LENGTHUNIT','AREAUNIT','VOLUMEUNIT')]
 api.run('unit.assign_unit',f,units=units);model=api.run('context.add_context',f,context_type='Model')
 body=api.run('context.add_context',f,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=model)
 site=entity('IfcSite','San Gregorio di Catania');building=entity('IfcBuilding','Palazzo Lombardo')
 storey=entity('IfcBuildingStorey','Piano terra | C6' if id.startswith('G') else 'Piano primo | A2')
 for parent,child in ((project,site),(site,building),(building,storey)):api.run('aggregate.assign_object',f,products=[child],relating_object=parent)
 cases_path=Path(__file__).with_name('mezzanines.json')
 cases=json.loads(cases_path.read_text(encoding='utf-8-sig')) if cases_path.exists() else {}
 spec=cases.get(id);upper=None;upper_parts=[];lower_parts=[]
 if spec:
  upper=entity('IfcBuildingStorey','Livello superiore | '+spec['short']);upper.Elevation=spec['level']
  api.run('aggregate.assign_object',f,products=[upper],relating_object=building)
 groups=elements(dest/(id+'.glb'));parts=[]
 for (room,layer,name),items in groups.items():
  cl=category(name,layer);element=entity(cl,room+' | '+name)
  element.Tag=id+'/'+layer+'/'+name
  if spec and layer=='Quota alta' and not any(k in name.lower() for k in ('scala','cassetto estraibile','corpo contenitore','montante di studio','presa incassata','alzata')):
   upper_parts.append(element)
  else:lower_parts.append(element)
  if spec and cl=='IfcStairFlight' and 'nuova scala' in name.lower():
   count=spec['flight'][3];element.NumberOfRisers=count;element.NumberOfTreads=count-1;element.RiserHeight=spec['level']/count;element.TreadLength=spec['flight'][4]
  element.Description='Studio preliminare da NCV364 e riscontri fotografici. Profili e quote verticali locali indicativi.'
  coords=[];faces=[]
  for v,tri in items:
   off=len(coords);coords.extend(v.round(5).tolist());faces.extend((tri+off+1).tolist())
  pts=f.create_entity('IfcCartesianPointList3D',CoordList=coords)
  geom=f.create_entity('IfcTriangulatedFaceSet',Coordinates=pts,CoordIndex=faces)
  rep=f.create_entity('IfcShapeRepresentation',ContextOfItems=body,RepresentationIdentifier='Body',RepresentationType='Tessellation',Items=[geom])
  element.Representation=f.create_entity('IfcProductDefinitionShape',Representations=[rep]);parts.append(element)
  ps=api.run('pset.add_pset',f,product=element,name='ARCHAI_Origine')
  api.run('pset.edit_pset',f,pset=ps,properties={'Versione':id,'Ambiente':room,'Strato':layer,'Base':'NCV364 p.13' if id.startswith('G') else 'NCV364 p.11','Fase':'Stato documentario' if id in ('G00','P00') else 'Ipotesi progettuale'})
 api.run('spatial.assign_container',f,products=lower_parts,relating_structure=storey)
 if upper_parts:api.run('spatial.assign_container',f,products=upper_parts,relating_structure=upper)
 out=dest/(id+'.ifc');f.write(str(out))
 reread=ifc.open(str(out));assert len(reread.by_type('IfcElement'))==len(parts) and len(parts)>=5 and len(reread.by_type('IfcTriangulatedFaceSet'))==len(parts)
 print(id,len(parts),'componenti IFC',out.stat().st_size,flush=True)
if __name__=='__main__':
 for s in sys.argv[1:] or [p.stem for p in dest.glob('*.glb')]:create_version(s)
