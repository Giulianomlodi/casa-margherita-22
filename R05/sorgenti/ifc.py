from pathlib import Path
import re,sys,json
import ifcopenshell,ifcopenshell.api as api
from design import DATA,LEVEL,DEPTH,NAMES,calc
D=Path(__file__).resolve().parent
src=D.parents[1]/'Sorgenti_3D/scripts/exchange.py'
code=src.read_text(encoding='utf8').replace("    if furniture:","    if furniture or ' | letto' in name:")
ns={'__file__':str(src),'__name__':'r05_ifc'}
exec(compile(code,str(src),'exec'),ns)
ns['dest']=D.parent/'due-camere';original=ns['elements'];oldcat=ns['category']
def inventory(path):
 from collections import defaultdict
 es=defaultdict(list)
 for (room,layer,name),geometry in original(path).items():
  name=re.sub(r'(Rampa [12]) pedata \d+',r'\1',name)
  es[(room,layer,name)].extend(geometry)
 return es
def category(name,layer):
 if ' | Rampa' in name:return 'IfcStairFlight'
 if ' | letto' in name or 'Armadio basso' in name or 'Comodino' in name:return 'IfcFurniture'
 if 'Impalcato' in name or 'Ripiano di volta' in name:return 'IfcSlab'
 if 'Montante da dimensionare' in name:return 'IfcColumn'
 return oldcat(name,layer)
ns.update(elements=inventory,category=category)
for id in sys.argv[1:] or 'FL':
 ns['create_version'](id)
 path=D.parent/'due-camere'/(id+'.ifc');f=ifcopenshell.open(str(path));b=f.by_type('IfcBuilding')[0]
 upper=api.run('root.create_entity',f,ifc_class='IfcBuildingStorey',name=f'Camere alte +{LEVEL[id]:.2f}');upper.Elevation=LEVEL[id];api.run('aggregate.assign_object',f,products=[upper],relating_object=b)
 for k,r in DATA[id].items():
  space=api.run('root.create_entity',f,ifc_class='IfcSpace',name=NAMES[k]+' · singola in verifica')
  api.run('aggregate.assign_object',f,products=[space],relating_object=upper)
  qs=api.run('pset.add_qto',f,product=space,name='Qto_SpaceBaseQuantities');api.run('pset.edit_qto',f,qto=qs,properties={'NetFloorArea':calc(r)['net']})
  ps=api.run('pset.add_pset',f,product=space,name='ARCHAI_Verifica');api.run('pset.edit_pset',f,pset=ps,properties={'QuotaPiano':LEVEL[id],'AltezzaSopraSeH420':4.2-LEVEL[id],'Uso':'Camera singola ipotizzata; verificare superficie, altezze, finestre e assentibilita.'})
  for ob in f.by_type('IfcElement'):
   name=ob.Name or ''
   if k+' | ' not in name:continue
   if ' | Rampa' in name:
    idx=int(re.search(r'Rampa (\d+)',name).group(1))-1;fl=r['flights'][idx];ob.NumberOfRisers=fl[4];ob.NumberOfTreads=fl[4]-1;ob.RiserHeight=LEVEL[id]/sum(y[4] for y in r['flights']);ob.TreadLength=fl[5]
   elif not any(s in name for s in ('Montante da dimensionare','Base chiusa','Frontale apribile','Cosciale','Ripiano di volta','Corrimano rampa','Montante parapetto')):
    api.run('spatial.assign_container',f,products=[ob],relating_structure=space)
 f.write(str(path));assert len(f.by_type('IfcSpace'))==2 and len(f.by_type('IfcBuildingStorey'))==2
