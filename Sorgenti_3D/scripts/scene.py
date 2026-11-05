"""Parametric representation of Palazzo Lombardo. Inputs use DOCFA drawing pixels and heights in metres."""
import bpy, bmesh, json, math, os, random
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parent.parent
CACHE=ROOT/'cache'; ATLAS=ROOT.parent/'Atlante_3D'
DATA=json.loads((ROOT/'scripts/geometry.json').read_text())
S=.0254
SCHEME=os.environ.get('CM_SCHEME','P02')
BOX=SCHEME.startswith('G')
MEZZ=json.loads((ROOT/'scripts/mezzanines.json').read_text(encoding='utf-8-sig')).get(SCHEME)
N={'G00':0,'GA':1,'GB':2,'G01':3}[SCHEME] if BOX else (MEZZ['base'] if MEZZ else int(SCHEME[1:]))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
materials={};objects=[];lib={};shape_cache={}
zone='Casa';layer='Struttura'
def group(room,category):
 global zone,layer
 zone,layer=room,category
def xy(x,y):return ((x-(215 if not BOX else 215))*S,(550-y if not BOX else 300-y)*S)
def point(x,y,z):return (*xy(x,y),z)
def material(name,c,rough=.58,metal=0,texture=None,alpha=1):
 m=bpy.data.materials.new(name);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 m.diffuse_color=(*c,alpha)
 if alpha<1:bs.inputs['Alpha'].default_value=alpha;bs.inputs['IOR'].default_value=1.45;m.surface_render_method='DITHERED'
 if texture:
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(CACHE/texture),check_existing=True);m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if name=='Vetro opalino':
  bs.inputs['Emission Color'].default_value=(1,.72,.4,1);bs.inputs['Emission Strength'].default_value=.8
 materials[name]=m;return m
for args in [('Calce',(.79,.73,.61)),('Cornice',(.93,.87,.74)),('Pietra',(.44,.38,.31)),('Castagno',(.26,.125,.06),.44,0,'oak-planks.jpg'),('Bronzo',(.19,.115,.058),.34,.63),('Ferro',(.11,.125,.10),.43,.60),('Graniglia',(.59,.42,.37),.38,0,'graniglia.jpg'),('Scaglie',(.70,.59,.47),.42,0,'scaglie.jpg'),('Lava',(.20,.21,.20),.58,0,'basalto.jpg'),('Salvia',(.30,.40,.32)),('Lino',(.79,.72,.58)),('Avorio',(.92,.88,.74)),('Cuoio',(.40,.20,.105)),('Terracotta',(.50,.235,.115)),('Smalto',(.86,.88,.81),.21),('Acqua',(.28,.46,.43),.20,.12),('Vetro',(.68,.85,.82),.14,.1,None,.16),('Vetro opalino',(.94,.79,.54),.30),('Argilla',(.65,.46,.35)),('Ardesia',(.12,.16,.16)),('Cemento',(.38,.36,.32)),('Rame',(.51,.28,.15),.33,.55),('Blu',(.15,.22,.27)),('Gomma',(.047,.05,.044))]:material(*args)
needed={'sofa','lounge_chair','dining_chair','coffee_table','side_table','floor_lamp','art','kitchen','pendant','rug','pot_terracotta','pot_ceramic','olive_pot_a','shrub','dining_table','sheer_2.62'}
with bpy.data.libraries.load(str(CACHE/'archai.blend'),link=False) as (available,loaded):
 loaded.meshes=[m for m in available.meshes if m.removeprefix('ADM_') in needed]
for me in loaded.meshes:lib[me.name.removeprefix('ADM_')]=me
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(materials[mat]);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 uv=me.uv_layers.new(name='Metri')
 for poly in me.polygons:
  axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=((1,2),(0,2),(0,1))[axis]
  for idx in poly.loop_indices:
   v=me.vertices[me.loops[idx].vertex_index].co;uv.data[idx].uv=(v[axes[0]]*.77,v[axes[1]]*.77)
 return me
def instance(name,me,location=(0,0,0),rot=0,scale=(1,1,1)):
 ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);ob.location=location;ob.rotation_euler.z=rot;ob.scale=scale
 ob['ambiente']=zone;ob['strato']=layer;ob['versione']=SCHEME;objects.append(ob);return ob
def cube_shape(w,d,h,mat,bevel=0):
 key=(round(w,5),round(d,5),round(h,5),mat,round(bevel,4))
 if key not in shape_cache:
  a,b,c=w/2,d/2,h/2
  me=mesh(mat,[(x,y,z) for z in (-c,c) for y in (-b,b) for x in (-a,a)],[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],mat)
  if bevel:
   bm=bmesh.new();bm.from_mesh(me);bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(w,d,h)*.42),segments=3,affect='EDGES');bm.to_mesh(me);bm.free()
  shape_cache[key]=me
 return shape_cache[key]
def cube(name,x,y,z,w,d,h,mat,bevel=0,rot=0):
 return instance(name,cube_shape(w,d,h,mat,bevel),point(x,y,z),rot)
def block(name,x,y,w,d,z,h,mat,bevel=0):return cube(name,x+w/2,y+d/2,z+h/2,w*S,d*S,h,mat,bevel)
def bar(name,a,b,depth,height,z,mat):
 vx,vy=xy(*a);wx,wy=xy(*b)
 return instance(name,cube_shape(math.hypot(wx-vx,wy-vy),depth,height,mat,.002),((vx+wx)/2,(vy+wy)/2,z),math.atan2(wy-vy,wx-vx))
def lathe(name,x,y,z,profile,mat,stretch=(1,1,1),segments=28):
 key=('profile',tuple(profile),mat,segments)
 if key not in shape_cache:
  verts=[(r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),h) for r,h in profile for i in range(segments)]
  faces=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i) for j in range(len(profile)-1) for i in range(segments)]
  me=mesh(name,verts,faces,mat)
  for p in me.polygons:p.use_smooth=True
  shape_cache[key]=me
 return instance(name,shape_cache[key],point(x,y,z),scale=stretch)
def prism(name,d,z,h,mat):
 count=len(d['v']);verts=[point(x,y,Z) for Z in (z,z+h) for x,y in d['v']]
 faces=[tuple(t) for t in d['f']]+[tuple(i+count for i in t) for t in d['f']]+[(a,b,b+count,a+count) for a,b in d['e']]
 return instance(name,mesh(name,verts,faces,mat))
def polygon_prism(name,pts,z,h,mat):
 vec=[Vector((*xy(*a),0)) for a in pts];tris=tessellate_polygon([vec])
 d={'v':pts,'f':tris,'e':[(i,(i+1)%len(pts)) for i in range(len(pts))]}
 return prism(name,d,z,h,mat)
def asset(key,name,x,y,z=0,angle=0,s=(1,1,1)):
 return instance(name,lib[key],point(x,y,z),math.radians(angle),s)
def light(name,kind,x,y,z,power,tint=(1,.85,.67),size=1,aim=None):
 data=bpy.data.lights.new(name,kind);data.energy=power;data.color=tint
 if kind=='AREA':data.shape='DISK';data.size=size
 if kind=='POINT':data.shadow_soft_size=size
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=point(x,y,z)
 if aim:ob.rotation_euler=(Vector(point(*aim))-ob.location).to_track_quat('-Z','Y').to_euler()
 return ob
def opening(name,a,b,z0,z1,panes=2,walk=False,mat='Castagno',transom=False):
 def lerp(t):return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
 length=math.dist(a,b)*S
 for t in range(panes+1):
  c=lerp(t/panes);cube(name+' montante',*c,(z0+z1)/2,.053,.058,z1-z0,mat,.004)
 for z in [z0+.024,z1-.025]+([z1-.56] if transom else []):bar(name+' traverso',a,b,.067,.049,z,mat)
 for i in range(panes):
  if walk and i==0:continue
  bar(name+' vetro',lerp(i/panes+.018/length),lerp((i+1)/panes-.018/length),.012,z1-z0-.09,(z0+z1)/2,'Vetro')
def rail(a,b):
 bar('Corrimano',a,b,.052,.055,1.02,'Ferro');bar('Traverso parapetto',a,b,.036,.035,.18,'Ferro')
 count=max(2,round(math.dist(a,b)*S/.135))
 for i in range(count+1):
  t=i/count;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
  cube('Bacchetta',x,y,.57,.018,.018,.89,'Ferro')
def mould(pts):
 for a,b in zip(pts,pts[1:]+pts[:1]):
  for z,w,h in [(3.9,.06,.065),(3.96,.09,.065),(4.01,.13,.046)]:bar('Cornice a gola',a,b,w,h,z,'Cornice')
def vault(pts):
 # A shallow curved soffit; the plan is known, arch rise and springing are indicative.
 unique=sorted(set(y for _,y in pts));ys=sorted(set(unique+[min(unique)+(max(unique)-min(unique))*t/22 for t in range(1,22)]))
 verts=[];faces=[];nx=16
 for y0 in ys:
  y=min(max(y0,min(ys)+.03),max(ys)-.03);xs=[]
  for (x1,y1),(x2,y2) in zip(pts,pts[1:]+pts[:1]):
   if min(y1,y2)<=y<max(y1,y2):xs.append(x1+(x2-x1)*(y-y1)/(y2-y1))
  if len(xs)<2:continue
  for j in range(nx+1):
   u=j/nx;v=(y-min(ys))/(max(ys)-min(ys));rise=.37*(max(0,4*u*(1-u))*max(0,4*v*(1-v)))**.55
   verts.append(point(min(xs)+(max(xs)-min(xs))*u,y,4.015+rise))
 rows=len(verts)//(nx+1)
 for i in range(rows-1):
  for j in range(nx):
   a=i*(nx+1)+j;faces.append((a,a+1,a+nx+2,a+nx+1))
 me=mesh('Intradosso',verts,faces,'Cornice')
 for f in me.polygons:f.use_smooth=True
 instance('Volta ribassata indicativa',me)
def doorframe(x,y,w,d):
 horiz=w>d;a=(x,y+d/2) if horiz else (x+w/2,y);b=(x+w,y+d/2) if horiz else (x+w/2,y+d)
 for p in (a,b):cube('Mostra porta',*p,1.36,.085,.085,2.72,'Cornice',.006)
 bar('Architrave',a,b,.1,.09,2.70,'Cornice')
def lamp(x,y,h=2.57):
 group(zone,'Illuminazione')
 cube('Rosone soffitto',x,y,3.98,.13,.13,.04,'Bronzo',.015)
 cube('Cavo pendente',x,y,(h+4)/2,.013,.013,4-h,'Ferro')
 lathe('Paralume in ottone',x,y,h,[(.20,0),(.21,.016),(.15,.14),(.045,.23),(.015,.24)],'Bronzo')
 lathe('Diffusore',x,y,h-.015,[(.01,0),(.176,0),(.19,.012)],'Vetro opalino')
 light('Lampada serale','POINT',x,y,h-.12,42,(1,.70,.43),.23)
def bed(x,y,w,h):
 block('Sommier',x,y,w,h,.07,.27,'Castagno',.045)
 block('Materasso imbottito',x+.6,y+.6,w-1.2,h-1.2,.33,.20,'Lino',.065)
 block('Testiera tessile',x-1,y-2,w+2,4,.20,.88,'Salvia',.048)
 block('Piumone',x+1,y+22,w-2,h-23,.52,.095,'Avorio',.045)
 block('Plaid piegato',x+1,y+h-20,w-2,11,.61,.04,'Cuoio',.012)
 count=2 if w>45 else 1
 for i in range(count):block('Guanciale',x+2+i*(w-4)/count,y+4,(w-4)/count-1,15,.53,.13,'Lino',.05)
def table(x,y,w,d,chairs=True):
 block('Piano in castagno',x,y,w,d,.73,.055,'Castagno',.024)
 for xx in (x+4,x+w-4):
  for yy in (y+4,y+d-4):cube('Gamba tavolo',xx,yy,.38,.046,.046,.72,'Bronzo',.006)
 if chairs:
  for xx in (x+w*.25,x+w*.74):
   asset('dining_chair','Sedia imbottita',xx,y-8,angle=180,s=(.87,.87,.94));asset('dining_chair','Sedia imbottita',xx,y+d+8,s=(.87,.87,.94))
 lathe('Ciotola in ceramica',x+w*.53,y+d*.50,.785,[(.03,0),(.10,.01),(.13,.065),(.12,.07),(.09,.027),(.02,.024)],'Terracotta')
def plant(x,y,scale=1):
 group(zone,'Verde');asset('pot_terracotta','Vaso in cotto',x,y,s=(scale,)*3);asset('olive_pot_a','Ulivo ornamentale',x,y,.46*scale,s=(scale*.76,)*3)
def shelving(x,y,w,d):
 block('Schienale libreria',x,y,w,1.3,.12,1.65,'Castagno')
 for z in (.12,.54,.97,1.4,1.78):
  block('Ripiano',x,y,w,d,z,.032,'Castagno')
  if z>1.5:continue
  for j in range(max(1,int(w/4)-2)):
   block('Volume rilegato',x+2+j*2.9,y+1.6,2,6,z+.034,.20+(j%3)*.022,['Salvia','Lino','Cuoio','Ardesia'][j%4],.002)
def bath(x,y,w,d,compact=False):
 group(zone,'Arredi')
 block('Piatto doccia',x+1,y+1,w-2,30,.02,.04,'Smalto',.015)
 bar('Vetro doccia',(x+1,y+31),(x+w*.60,y+31),.018,1.9,.99,'Vetro')
 cube('Asta doccia',x+3,y+13,1.35,.025,.025,1.25,'Bronzo');cube('Soffione',x+6,y+13,1.97,.16,.16,.023,'Bronzo',.012)
 lathe('Vaso sanitario',x+w*.43,y+d*.62,.01,[(.12,0),(.13,.14),(.20,.30),(.20,.41),(.155,.42),(.13,.35)],'Smalto',(1,1.35,1))
 block('Mobile lavabo',x+2,y+d-20,w*.58,14,.31,.47,'Castagno',.012)
 lathe('Catino lavabo',x+w*.34,y+d-13,.78,[(.14,0),(.20,.11),(.185,.12),(.12,.035)],'Smalto',(1,.8,1))
 cube('Miscelatore',x+w*.34,y+d-18,.97,.026,.026,.18,'Bronzo')
def high_store(x,y,w,d):
 group(zone,'Quota alta');block('Impalcato deposito ipotetico',x,y,w,d,2.40,.16,'Castagno',.012)
 for xx in (x+2,x+w-2):
  for yy in (y+2,y+d-2):cube('Montante indipendente',xx,yy,1.20,.045,.045,2.40,'Ferro',.003)
 for j in range(3):block('Modulo stagionale',x+2+j*(w-4)/3,y+3,(w-4)/3-1,d-6,2.56,.55,'Lino',.02)
 bar('Guida sportelli',(x,y+d),(x+w,y+d),.046,.055,3.13,'Bronzo')
rooms_it={'wc':'Bagno sul retro','terr':'Terrazzo','k':'Cucina','liv':'Sala sul giardino','entry':'Ingresso','rip':'Servizi centrali','big':'Stanza sulla piazza','small':"Vano d’angolo",'stairs':'Scala'}
def make_garden():
 group('Giardino d’inverno','Serramenti')
 x1,x2,y1,y2=134,(204 if N==5 else 337),108,230
 for a,b,panes in [((x1,y1),(x2,y1),max(2,round((x2-x1)/42))),((x2,y1),(x2,y2),3)]:
  opening('Giardino - profilo in bronzo',a,b,.16,2.66,panes,mat='Bronzo',transom=True)
 group('Giardino d’inverno','Coperture')
 # Shed-roof members follow the slope toward the open parapet.
 for i in range(max(3,round((x2-x1)/40))+1):
  x=x1+(x2-x1)*i/max(3,round((x2-x1)/40))
  ob=cube('Travetto serra',x,(y1+y2)/2,2.76,.046,(y2-y1)*S,.07,'Bronzo');ob.rotation_euler.x=-.058
 roof=cube('Copertura trasparente', (x1+x2)/2,(y1+y2)/2,2.79,(x2-x1)*S,(y2-y1)*S,.023,'Vetro');roof.rotation_euler.x=-.058
 for x in range(x1+2,x1+int((x2-x1)*.48),4):
  ob=cube('Lamella schermatura esterna',x,(y1+y2)/2,2.84,.063,(y2-y1)*S,.017,'Castagno');ob.rotation_euler.x=-.058
 plant(x2-18,y1+19,.45);plant(x2-17,y2-18,.33)
 if N!=5:
  group(zone,'Arredi');table(182,154,59,28,False)
  asset('dining_chair','Sedia giardino',197,145,angle=180,s=(.80,)*3);asset('dining_chair','Sedia giardino',221,190,s=(.80,)*3)
 else:
  group(zone,'Arredi');block('Panca della serra',137,146,13,52,.32,.11,'Castagno',.02);plant(308,128,.40)
def make_house():
 group('Casa','Struttura')
 for z,Z,shape in DATA['walls']['2' if N==2 else '0']:prism('Murature DOCFA',shape,z,Z-z,'Calce')
 for key,d in DATA['floors'].items():
  group(rooms_it[key],'Struttura')
  if key=='stairs':continue
  mat='Graniglia' if key=='liv' else ('Pietra' if key=='terr' else ('Acqua' if key=='wc' else 'Scaglie'))
  prism('Pavimento '+rooms_it[key],d,-.17,.17,mat)
  if key not in ('terr',):
   group(zone,'Coperture');vault(DATA['rooms'][key]);group(zone,'Finiture');mould(DATA['rooms'][key])
 group('Scala','Struttura')
 for i in range(21):
  y=957-i*12;z=-(20-i)*.178;block('Gradino '+str(i+1),94,y,47,12,z-.18,.18,'Pietra')
 block('Pianerottolo',78,630,63,79,-.17,.17,'Scaglie')
 group('Balcone','Struttura');prism('Balcone spezzato',DATA['balconyFloor'],-.20,.20,'Lava')
 group('Balcone','Serramenti');rail((98,1054),(334,1054));rail((334,1054),(464,1016));rail((464,1016),(454,982));rail((98,1054),(98,1019))
 group('Terrazzo','Serramenti');rail((130,100),(347,100));rail((347,100),(347,232))
 for r in DATA['doors']:
  if N==2 and r==DATA['doors'][-1]:continue
  group('Soglie','Serramenti');doorframe(*r);x,y,w,d=r
  block('Soglia',x,y,w,d,-.025,.025,'Pietra')
 group('Retro','Serramenti');opening('Finestrino WC',(91,99),(110,99),2,2.8,1)
 opening('Finestra sul terrazzo',(207,239),(316,239),.86,2.78,4)
 bar('Davanzale di pietra',(203,239),(319,239),.36,.065,.85,'Pietra')
 opening('Porta terrazza',(143,238),(169,238),0,2.73,1,mat='Castagno')
 group('Balcone','Serramenti')
 opening('Portafinestra camera grande',(212,1011),(269,1011),0,3.05,2,transom=True)
 opening('Portafinestra obliqua',(362,1000),(400,988),0,3.05,2,transom=True)
 for x in (211,269):
  cube('Cornice infisso sulla piazza',x,1004,1.5,.11,.09,3.0,'Cornice',.012)
 group('Sala sul giardino','Serramenti')
 screen=[389,390,389,407,412,408][N]
 if N!=5:opening('Quinta in legno con sopraluce',(184,screen),(338,screen),.01,3.60,5,walk=True,mat='Castagno',transom=True)
 else:
  for x,w in [(184,115),(322,16)]:block('Nuovo divisorio camera',x,407,w,5,0,4.16,'Calce')
  bar('Sopraporta camera',(299,410),(322,410),.127,1.5,3.43,'Calce')
 group('Bagno sul retro','Arredi');bath(65,107,53,126)
 for x,y,z in [(254,337,2.95),(233,525,2.78),(233,901,2.81),(105,376,2.72),(201,719,2.64),(357,936,2.70)]:lamp(x,y,z)
 if not N:return
 make_garden()
 group('Cucina','Arredi')
 asset('kitchen','Cucina componibile con cappa e lavello',79,307,angle=90,s=(1.02,.83,1))
 block('Dispensa bassa',66,365,23,67,.07,.85,'Salvia',.014)
 block('Piano in pietra lavica',66,365,24,67,.91,.045,'Lava',.008)
 if N==4:
  block('Secondo banco',116,267,21,83,.07,.84,'Castagno',.013);block('Piano di servizio',115,266,23,85,.91,.045,'Lava',.007)
 group('Sala sul giardino','Arredi')
 layouts={1:(241,277,220,483,73,38),2:(256,263,218,474,80,40),3:(245,473,177,536,53,27),4:(231,510,220,287,79,43),5:(165,862,214,485,74,40)}
 x,y,tx,ty,tw,td=layouts[N];table(tx,ty,tw,td)
 if N==5:group('Salotto di piazza','Arredi')
 asset('sofa','Divano rivestito in tessuto',x+32,y+12,s=(.74,.8,.94))
 asset('rug','Tappeto tessuto',x+32,y+43,s=(.80,.64,1))
 asset('coffee_table','Tavolino in pietra',x+32,y+52,s=(.67,.67,.84))
 asset('floor_lamp','Lampada da lettura',x+6,y+36,s=(.9,)*3)
 if N==5:
  asset('lounge_chair','Poltrona da lettura',279,950,angle=155)
  group('Camera sul retro','Arredi');bed(259,263,64,79)
  group('Vano d’angolo','Arredi');shelving(335,932,47,11)
 else:
  group('Camera sulla piazza','Arredi');bx,by=[(0,0),(256,873),(155,864),(165,892),(248,878)][N];bed(bx,by,62,79)
  asset('side_table','Comodino',bx+69,by+10,s=(.68,.68,.75))
  if N==2:
   group('Camera singola','Struttura');block('Parete spostata',279,817,4,187,0,4.19,'Calce')
   block('Traccia pavimento ripristinato',324,817,6,187,-.02,.02,'Scaglie')
   group('Camera singola','Arredi');bed(293,878,36,78)
  group('Vano d’angolo','Arredi');shelving(336,936,34,9)
 if N==3:
  group('Atelier','Arredi')
  for x in [221,265]:
   block('Piano disegno',x,263,42,24,.74,.045,'Castagno',.018)
   for xx in (x+2,x+39):
    for yy in (265,284):cube('Gamba scrivania',xx,yy,.37,.04,.04,.74,'Ferro')
   asset('dining_chair','Seduta atelier',x+19,297,s=(.89,)*3)
  shelving(300,319,30,10)
 if N>=2:
  group('Secondo servizio','Struttura')
  block('Parete del filtro',249,696,43,2.6,0,2.40,'Calce')
  for y,d in [(697,12),(742,55)]:block('Parete del servizio',290,y,2.5,d,0,2.40,'Calce')
  group(zone,'Arredi');bath(249,703,40,91,True)
 if N==4:
  group('Dispensa','Quota alta');high_store(75,474,61,106)
 else:
  group('Servizi centrali','Quota alta');high_store(*{1:(251,705,67,76),2:(253,697,64,80),3:(250,668,66,88),5:(252,704,68,72)}[N])
def arch(a,b,width,spring,rise):
 # Extruded arch ring with voussoirs expressed by radial joints.
 x1,y1=a;x2,y2=b;dx=x2-x1;dy=y2-y1;L=math.hypot(dx,dy);nx=-dy/L;ny=dx/L
 for i in range(17):
  t0=i*math.pi/17+.002;t1=(i+1)*math.pi/17-.002
  vertices=[]
  for dep in (-width/2,width/2):
   for t,r in [(t0,0),(t1,0),(t1,.24),(t0,.24)]:
    x=(x1+x2)/2+(dx/2+r*dx/L/S)*math.cos(t)+nx*dep/S
    y=(y1+y2)/2+(dy/2+r*dy/L/S)*math.cos(t)+ny*dep/S
    vertices.append(point(x,y,spring+(rise+r)*math.sin(t)))
  instance('Concio arco',mesh('Concio',vertices,[(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'Pietra'))
def vehicle():
 # An ergonomic proxy with modeled wheels and glazing.
 group('Posto auto','Arredi');cx,cy=281,270
 def hull(name,stations,mat):
  verts=[];faces=[]
  for y,w,bottom,top in stations:
   # Section across sill, shoulders and subtly crowned surface.
   for amount,height in [(-.88,0),(-1,.23),(-1,.72),(-.90,.92),(-.58,.987),(0,1),(.58,.987),(.90,.92),(1,.72),(1,.23),(.88,0)]:
    verts.append((w*amount,y,bottom+(top-bottom)*height))
  ring=11
  for j in range(len(stations)-1):
   for i in range(ring):faces.append((j*ring+i,j*ring+(i+1)%ring,(j+1)*ring+(i+1)%ring,(j+1)*ring+i))
  faces+=[tuple(range(ring)),tuple(range((len(stations)-1)*ring,len(stations)*ring))]
  me=mesh(name,verts,faces,mat)
  for poly in me.polygons:poly.use_smooth=True
  return instance(name,me,point(cx,cy,0))
 hull('Carrozzeria compatta',[(-2.18,.70,.46,.80),(-2.08,.86,.33,.99),(-1.88,.89,.29,1.06),(-1.42,.92,.27,1.07),(-.72,.93,.29,1.08),(.35,.92,.29,1.06),(1.07,.90,.29,.96),(1.65,.87,.31,.89),(2.04,.81,.35,.81),(2.18,.70,.45,.70)],'Blu')
 hull('Abitacolo vetrato',[(-1.80,.76,.88,1.01),(-1.46,.79,.91,1.39),(-.97,.75,.94,1.53),(.10,.73,.94,1.55),(.49,.74,.93,1.44),(1.18,.77,.88,.99)],'Ardesia')
 hull('Padiglione verniciato',[(-1.23,.67,1.42,1.48),(-.92,.70,1.49,1.54),(.05,.68,1.49,1.56),(.29,.66,1.44,1.51)],'Blu')
 for sign in (-1,1):
  x=cx+sign*34
  for yy in (cy-51,cy+51):
   ob=lathe('Pneumatico',x,yy,.33,[(.18,-.11),(.30,-.11),(.33,-.07),(.33,.07),(.30,.11),(.18,.11)],'Gomma');ob.rotation_euler.y=math.pi/2
   ob=lathe('Cerchio',x,yy,.33,[(0,-.12),(.205,-.12),(.205,.12),(0,.12)],'Ferro');ob.rotation_euler.y=math.pi/2
   for j in range(5):
    o=cube('Razza cerchio',x+sign*4.9,yy,.33,.012,.39,.025,'Pietra',.007);o.rotation_euler.x=j*math.pi/5
  for oy in (-14,32):cube('Maniglia carrozzeria',cx+sign*35.4,cy+oy,.93,.03,.14,.03,'Ferro',.008)
  cube('Specchio retrovisore',cx+sign*38.4,cy-20,1.10,.20,.17,.105,'Blu',.04)
  cube('Montante finestrino',cx+sign*29.6,cy+10,1.24,.042,.08,.50,'Gomma',.012)
  cube('Fanale anteriore',cx+sign*22.4,cy-81,.728,.41,.07,.077,'Vetro opalino',.031)
  cube('Fanale posteriore',cx+sign*24,cy+80.5,.855,.34,.09,.079,'Rame',.03)
 cube('Griglia anteriore',cx,cy-84.2,.54,.81,.043,.12,'Gomma',.02)
def cycle(x,y):
 for yy in (y,y+42):
  ob=lathe('Ruota bici',x,yy,.34,[(.30,-.022),(.34,-.022),(.34,.022),(.30,.022),(.30,-.022)],'Gomma');ob.rotation_euler.y=math.pi/2
  for t in range(9):
   a=t*math.pi/9;ob=cube('Raggio',x,yy,.34,.006,.62,.006,'Ferro');ob.rotation_euler.x=a
 for yy,z,dy,dz in [(y+11,.54,.58,.42),(y+29,.59,.55,-.51),(y+22,.75,.58,.04)]:
  ob=cube('Telaio bici',x,yy,z,.03,math.hypot(dy,dz),.032,'Salvia');ob.rotation_euler.x=-math.atan2(dz,dy)
 cube('Sella bici',x,y+32,.96,.15,.25,.058,'Cuoio',.02)
def garage():
 group('Autorimessa','Struttura');prism('Battuto di cemento',DATA['garageFloor'],-.17,.17,'Lava')
 for z,Z,d in DATA['garageWalls']:prism('Muratura perimetrale',d,z,Z-z,'Pietra')
 block('Pilastro isolato',177,244,24,23,0,3.15,'Pietra')
 for point_ in [(83,256),(352,256),(189,140),(189,440)]:arch((189,256),point_,.46,2.56,1.37)
 group(zone,'Coperture')
 for x1,x2 in [(80,189),(189,353)]:
  for y1,y2 in [(139,256),(256,441)]:vault([(x1,y1),(x2,y1),(x2,y2),(x1,y2)])
 group('Porta sul vicolo','Serramenti')
 for j in range(8):block('Serranda parzialmente aperta',226,123,126,3,2.54+j*.065,.061,'Ferro',.005)
 for x in (225,351):cube('Guida serranda',x,125,1.52,.055,.09,3.04,'Ferro')
 for x,y in [(92,186),(349,376),(94,354),(349,185)]:
  group('Autorimessa','Illuminazione')
  cube('Applique a parete',x,y,2.53,.11,.40,.10,'Ferro',.01)
  cube('Diffusore lineare',x,y,2.59,.105,.37,.023,'Vetro opalino',.005)
  light('Lampada serale','POINT',x+(8 if x<200 else -8),y,2.68,55,(1,.76,.56),.21)
 if N==1:
  vehicle();group('Ricovero mobile','Arredi');cycle(108,307)
  for j in range(3):block('Scaffale mobile',98,367,62,15,.12+j*.49,.035,'Castagno')
  for x in (100,157):
   for y in (368,381):cube('Montante scaffale',x,y,.63,.03,.03,1.25,'Ferro')
 elif N:
  vehicle();group('Banco e biciclette','Arredi')
  block('Banco da lavoro',98,329,26,98,.86,.075,'Castagno',.014)
  for xx in (100,122):
   for yy in (332,423):cube('Gamba banco',xx,yy,.43,.045,.045,.86,'Ferro')
  for j in range(5):block('Cassettiera',131+j*17,406,16,23,.08,.75,'Salvia',.005)
  cycle(105,245);cycle(120,248)
  if N==3:high_store(106,166,59,103)
 else:
  group('Piano alto osservato / ingombro ipotizzato','Quota alta')
  for j in range(12):block('Assito esistente ipotizzato',88+j*7,148,6.8,88,2.40,.08,'Castagno')
  for y in (154,221):block('Trave piano alto',88,y,84,4,2.24,.16,'Ferro')
def context():
 group('Contesto indicativo','Contesto')
 if BOX:
  block('Selciato del vicolo',33,10,380,113,-.16,.13,'Lava');return
 # Low near roofs form the rear horizon, isolated from the measured subaltern.
 for i,(x,y,w,d,h) in enumerate([(-90,-36,190,90,1.18),(106,-80,187,116,1.1),(319,-60,155,116,1.69),(415,88,128,200,.9),(10,1110,315,62,2.0)]):
  block('Fabbricato vicino indicativo',x,y,w,d,-3.80,3.8+h,'Argilla')
  for side in (-1,1):
   roof=cube('Falda vicina',x+w/2,y+d/2+side*d/4,h+.22,w*S+.13,d*S*.52,.09,'Terracotta');roof.rotation_euler.x=side*.19
def joinery_detail():
 for key in ('liv','entry','big','small','k'):
  group(rooms_it[key],'Finiture')
  pts=DATA['rooms'][key]
  # Split skirtings around actual portals and balcony doors instead of crossing thresholds.
  gaps=[(x-2,y-2,x+w+2,y+d+2) for x,y,w,d in DATA['doors']]+[(208,998,274,1020),(354,978,405,1008)]
  for a,b in zip(pts,pts[1:]+pts[:1]):
   n=max(1,round(math.dist(a,b)/2));segments=[];start=None
   for j in range(n+1):
    u=j/n;x=a[0]+(b[0]-a[0])*u;y=a[1]+(b[1]-a[1])*u;clear=not any(l<=x<=r and top<=y<=bottom for l,top,r,bottom in gaps)
    if clear and start is None:start=(x,y)
    if start and (not clear or j==n):
     if math.dist(start,(x,y))>1:bar('Battiscopa in graniglia',start,(x,y),.045,.105,.056,'Lava')
     start=None
 for x,y in [(195,632),(243,808),(181,370),(93,626)]:
  cube('Placca interruttori',x,y,1.13,.096,.022,.074,'Avorio',.008)
 for xx in [214,265]:
  group('Balcone','Serramenti');cube('Scuretto ripiegato',xx,1001,1.50,.085,.28,2.88,'Lino',.014)
 for yy in (248,505):
  group('Sala sul giardino','Finiture')
  # Framed edition on the solid wall, facing inward.
  if N:
   ob=asset('art','Stampa incorniciata',335 if yy<460 else 331,yy+28,1.65,angle=-90,s=(.8,.8,.76))
 if N:
  group('Sala sul giardino','Arredi')
  if N in (1,2,3,4):
   asset('side_table','Tavolino di appoggio',195,482,s=(.70,.70,.8))
   lathe('Vaso tornito',195,482,.51,[(.06,0),(.12,.05),(.11,.18),(.047,.26),(.05,.28)],'Terracotta')
  group('Camera sulla piazza','Finiture')
  asset('sheer_2.62','Telo di lino finestra',212,996,0.02,s=(.22,.52,1.13))
 else:
  group('Zona giorno','Illuminazione')
  for x,y in [(245,528),(231,904)]:
   cube('Catena lampadario',x,y,3.66,.015,.015,.64,'Bronzo')
   for j in range(6):
    a=j*math.tau/6;xx=x+math.cos(a)*12;yy=y+math.sin(a)*12
    bar('Braccio lampadario',(x,y),(xx,yy),.021,.021,3.32,'Bronzo')
    lathe('Candela opalina',xx,yy,3.32,[(.017,0),(.027,.08),(.021,.13),(.003,.16)],'Vetro opalino')
 if not N:
  group('Cucina','Finiture')
  for j in range(11):
   block('Zoccolo ceramico',65.1,249+j*18,1,17.8,.11,1.27,'Pietra')
  for j in range(7):cube('Doghe di soffitto cucina',83+j*11,357,3.95,.22,5.25,.022,'Castagno')
if BOX:garage()
else:
 make_house()
 joinery_detail()
 if MEZZ:
  import sys
  sys.path.insert(0,str(ROOT/'scripts'))
  from mezzanine import build_mezzanine
  build_mezzanine(globals(),MEZZ)
context()
# Local texture and shader detail. The geometry exported below and all camera renders share objects.
def colour_bs(m):
 return next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m and m.use_nodes else None
for m in bpy.data.materials:
 bs=colour_bs(m)
 if not bs:continue
 if m.name in ('Calce','Cornice','Pietra','Cemento','Lino','Fabric','Sage','Scaglie','Graniglia','Lava'):
  nodes=m.node_tree.nodes;links=m.node_tree.links;tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=58 if m.name in ('Calce','Cornice') else 105
  bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.012
  links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 if m.name=='Contact':
  bs.inputs['Alpha'].default_value=0.0
 if m.name=='Oak':
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(CACHE/'oak-planks.jpg'),check_existing=True);m.node_tree.links.new(tex.outputs[0],bs.inputs['Base Color'])
 if m.name=='Leaf':
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(CACHE/'foliage-atlas.png'),check_existing=True);m.node_tree.links.new(tex.outputs[0],bs.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
for o in objects:o.select_set(True)
bpy.context.view_layer.update()
glb=ATLAS/'modelli'/(SCHEME+'.glb')
if not os.environ.get('CM_SKIP_EXPORT'):
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_image_format='AUTO')
scene.render.engine='CYCLES'
pref=bpy.context.preferences.addons['cycles'].preferences
try:
 pref.compute_device_type='OPTIX';pref.refresh_devices()
 for d in pref.devices:d.use=(d.type=='OPTIX')
 if any(d.use for d in pref.devices):scene.cycles.device='GPU'
except Exception as error:print('Cycles:',error,flush=True)
scene.cycles.denoiser='OPTIX' if scene.cycles.device=='GPU' else 'OPENIMAGEDENOISE'
scene.cycles.samples=min(8,int(os.environ.get('CM_SAMPLES','18')));scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.transparent_max_bounces=12
scene.cycles.adaptive_threshold=.065;scene.render.use_persistent_data=True
scene.render.image_settings.file_format='WEBP';scene.render.image_settings.quality=89
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.35
world=bpy.data.worlds.new('Luce del cielo');world.use_nodes=True;scene.world=world
nd=world.node_tree.nodes;lk=world.node_tree.links;bg=nd.get('Background');env=nd.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(CACHE/'afternoon.hdr'));lk.new(env.outputs[0],bg.inputs[0])
sun=light('Sole','SUN',-250,-500,18,2,(1,.85,.65),aim=(220,600,0));sun.data.angle=.12
fills=[]
if BOX:
 for x,y in [(131,191),(281,220),(136,354),(279,363)]:fills.append(light('Rimbalzo volta','AREA',x,y,3.9,85,(1,.91,.79),2.3))
else:
 for x,y in [(245,319),(246,530),(213,919),(355,934),(100,383),(197,706),(285,726),(90,178)]:
  fills.append(light('Rimbalzo diffuso','AREA',x,y,3.82,80,(1,.92,.80),2.0))
# All cameras refer to the same plan coordinate system as the layers.
stops={
 'sala':('Sala verso il terrazzo',(218,603,1.60),(249,281,1.52)),
 'giardino':('Terrazzo e giardino',(320,213,1.59),(149,152,1.30)),
 'fronte':('Stanza sulla piazza',(174,838,1.54),(264,989,1.44)),
 'cucina':('Cucina',(120,433,1.59),(75,268,1.37)),
 'ingresso':('Ingresso e distribuzione',(178,771,1.58),(221,632,1.48)),
 'servizi':('Deposito alto e servizi',(280,649,1.54),(282,773,2.12)),
 'bagno':('Bagno sul retro',(105,222,1.58),(80,121,1.16)),
 'angolo':('Vano d’angolo',(346,866,1.53),(378,967,1.30)),
 'soglia':('Vano finestrato',(200,379,1.61),(282,247,1.36))}
if N==2 and not BOX:stops['angolo']=('Camera singola',(341,971,1.56),(310,860,1.33))
if N==4 and not BOX:stops['servizi']=('Dispensa in quota',(101,421,1.50),(103,547,2.15))
if N==5 and not BOX:stops['soglia']=('Camera sul giardino',(207,396,1.57),(286,266,1.36))
if BOX:stops={'accesso':('Ingresso dal vicolo',(289,145,1.61),(161,371,1.62)),'archi':('Archi e pilastro',(312,404,1.60),(163,218,1.89)),'banco':('Fascia del banco',(155,288,1.58),(113,405,1.49)),'quota':('Piano alto',(220,317,1.58),(134,185,2.47)),'manovra':('Corsia di manovra',(228,397,1.59),(291,163,1.29))}
if MEZZ:
 stops['sopra']=('Sul livello superiore',MEZZ['upperCam'],MEZZ['upperAim'])
 stops['scala']=('Scala e sbarco',MEZZ['stairCam'],MEZZ['stairAim'])
camera_data=bpy.data.cameras.new('Fotocamera');camera=bpy.data.objects.new('Fotocamera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
def lighting(evening):
 bg.inputs[1].default_value=.085 if evening else .72;sun.data.energy=.055 if evening else 2.25
 for f in fills:f.data.energy=34 if evening else (96 if BOX else 102)
 for o in scene.objects:
  if o.type=='LIGHT' and o.name.startswith('Lampada serale'):o.data.energy=(115 if BOX else 85) if evening else 12
 scene.view_settings.exposure=.58 if evening else .35
def render_at(name,eye,target,width,height,path,pano=False,ortho=False):
 camera_data.type='PANO' if pano else ('ORTHO' if ortho else 'PERSP');camera_data.lens=22;camera_data.clip_start=.035
 if pano:camera_data.panorama_type='EQUIRECTANGULAR'
 if ortho:camera_data.ortho_scale=12.5 if BOX else 25.5
 camera.location=eye;v=Vector(target)-camera.location
 if pano:v.z=0
 camera.rotation_euler=v.to_track_quat('-Z','Y').to_euler()
 scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100;scene.render.filepath=str(path)
 bpy.ops.render.render(write_still=True);print('SAVED',path.name,flush=True)
def render_views():
 only=os.environ.get('CM_ONLY','');size=int(os.environ.get('CM_WIDTH','1536'))
 panosize=int(os.environ.get('CM_PANO','3072'));panostops=(['accesso','archi','banco','quota','manovra'] if BOX else ['sala','giardino','fronte','cucina','servizi'])
 if MEZZ:panostops=['sala','giardino','fronte','scala','sopra']
 for evening in (False,True):
  if scene.timeline_markers:scene.frame_set(2 if evening else 1)
  lighting(evening);time='sera' if evening else 'giorno'
  for name,(title,pos,target) in stops.items():
   if only and name!=only:continue
   if evening and name not in panostops:continue
   path=ATLAS/'render'/f'{SCHEME}-{name}-{time}.webp'
   if (only or name not in panostops) and not path.exists():render_at(name,point(*pos),point(*target),size,round(size*.65),path)
   if name in panostops and not only:
    path=ATLAS/'panorami'/f'{SCHEME}-{name}-{time}.webp'
    if not path.exists():render_at(name,point(*pos),point(*target),panosize,panosize//2,path,True)
 if not only:
  lighting(False)
  for o in objects:
   if o['strato'] in ('Contesto','Coperture'):o.hide_render=True
  pos=(14,-23,22) if not BOX else (11,-14,12)
  path=ATLAS/'render'/f'{SCHEME}-assonometria.webp'
  if not path.exists():render_at('Intero',pos,(0,0,.5),size,round(size*.70),path,ortho=True)
meta={'id':SCHEME,'nodi':len(objects),'mesh':len(set(o.data.name for o in objects)),'zone':sorted(set(o['ambiente'] for o in objects)),'strati':sorted(set(o['strato'] for o in objects)),'tappe':{k:{'nome':v[0],'occhio':list(point(*v[1])),'bersaglio':list(point(*v[2]))} for k,v in stops.items()}}
(ATLAS/'modelli'/f'{SCHEME}.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf8')
if os.environ.get('CM_NATIVE')=='1':
 # Native editable scene with every station and two reproducible lighting states.
 cameras=[]
 for name,(title,pos,target) in stops.items():
  data=bpy.data.cameras.new(title);data.lens=23;data.clip_start=.035
  cam=bpy.data.objects.new('Vista | '+title,data);scene.collection.objects.link(cam);cam.location=point(*pos)
  cam.rotation_euler=(Vector(point(*target))-cam.location).to_track_quat('-Z','Y').to_euler();cameras.append(cam)
 bpy.data.objects.remove(camera,do_unlink=True);scene.camera=cameras[0]
 scene.render.resolution_x=1920;scene.render.resolution_y=1280;scene.render.resolution_percentage=100
 scene.frame_start=1;scene.frame_end=2
 for frame,night in [(1,False),(2,True)]:
  scene.frame_set(frame);lighting(night);bg.inputs[1].keyframe_insert(data_path='default_value',frame=frame)
  scene.view_settings.keyframe_insert(data_path='exposure',frame=frame)
  for ob in scene.objects:
   if ob.type=='LIGHT':ob.data.keyframe_insert(data_path='energy',frame=frame)
  scene.timeline_markers.new('Sera' if night else 'Giorno',frame=frame)
 scene.frame_set(1);scene.name='Casa Margherita | '+SCHEME
 scene['Descrizione']='Scala in metri. Frame 1 giorno, frame 2 sera. Quote locali e profili delle volte indicativi.'
 for ob in scene.objects:ob.select_set(False)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.file.pack_all()
 bpy.ops.wm.save_as_mainfile(filepath=str(ATLAS/'modelli'/(SCHEME+'.blend')),compress=True)
if os.environ.get('CM_BUILD_ONLY')!='1':
 if os.environ.get('CM_NATIVE')=='1':
  camera_data=bpy.data.cameras.new('Camera render');camera=bpy.data.objects.new('Camera render',camera_data);scene.collection.objects.link(camera);scene.camera=camera
 render_views()
