"""Build both conditional loft arrangements on the audited R04 apartment shell."""
from pathlib import Path
import sys,os,math,bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from design import DATA,NAMES,ORIGIN,S,DEPTH,LEVEL,walk
out=ROOT.parent/'due-camere';v=os.environ['R05_VARIANT'];level=LEVEL[v];thick=DEPTH[v];sc=bpy.context.scene
def pos(k,x,y,z):
 a,b=ORIGIN[k];return ((a-215)*S+x,(550-b)*S-y,z)
def worldpix(x,y,z):return ((x-215)*S,(550-y)*S,z)
def erase(objs):
 for o in list(objs):bpy.data.objects.remove(o,do_unlink=True)
def material(name,col,rough=.60,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*col,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;return m
wood=material('Rovere affumicato per impalcato',(.26,.135,.065),.48);ash=material('Frassino oliato',(.46,.29,.155),.52);iron=material('Ferro patinato',(.066,.079,.073),.40,.6);lime=material('Intonaco di calce chiara',(.68,.66,.55));felt=material('Tessuto salvia',(.28,.35,.25));paper=material('Carta e oggetti da lettura',(.61,.48,.30))
def flag(o,k,lay):
 o['camera_alta']=k;o['ambiente']=NAMES[k];o['strato']='Quota alta';o['elemento_R05']=lay;o['versione']=v
def box(k,n,b,z,h,m,lay,bevel=.008):
 x,y,X,Y=b
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos(k,(x+X)/2,(y+Y)/2,z+h/2));o=bpy.context.object;o.name=k+' | '+n;o.dimensions=(X-x,Y-y,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Spigoli reali','BEVEL');mod.width=min(bevel,h/3,(X-x)/4,(Y-y)/4);mod.segments=2
  mod=o.modifiers.new('Normali','WEIGHTED_NORMAL')
 o.data.materials.append(m);flag(o,k,lay);return o
def beam(k,n,a,b,r,mat,lay):
 A=Vector(pos(k,*a));B=Vector(pos(k,*b));delta=B-A
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=delta.length,location=(A+B)/2)
 o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.name=k+' | '+n;o.data.materials.append(mat);flag(o,k,lay);return o
erase(o for o in sc.objects if o.type=='MESH' and (v=='L' and o.get('ambiente')=='Camera sulla piazza' and o.get('strato')=='Arredi' or (o.get('ambiente')=='Sala sul giardino' and o.name.startswith(('Divano','Tappeto','Tavolino in pietra','Lampada da lettura')))))
# Remove pendants inside proposed bedrooms while retaining the rest of the historic shell.
for k,r in DATA[v].items():
 x,y,X,Y=r['deck'];cx,cy,_=pos(k,0,0,0)
 for o in list(sc.objects):
  if o.get('strato')!='Illuminazione' or not hasattr(o,'bound_box'):continue
  pts=[o.matrix_world@Vector(a) for a in o.bound_box];center=sum(pts,Vector())/len(pts)
  if x-.3<center.x-cx<X+.3 and y-.3<cy-center.y<Y+.3:erase([o])
# A single finished bed, authored in the local Blender MCP, is instanced twice with real geometry.
with bpy.data.libraries.load(str(ROOT/'letto-mcp.blend'),link=False) as (src,dst):
 assert 'Letto_R05' in src.collections,src.collections;dst.collections=['Letto_R05']
sc.collection.children.link(dst.collections[0]);bpy.context.view_layer.update()
bed_parts=[o for o in dst.collections[0].all_objects if o.type=='MESH']
bed_world=[(ob,ob.matrix_world.copy()) for ob in bed_parts]
sc.collection.children.unlink(dst.collections[0])
# Realise parts with world transforms so GLB and native geometry match even if the library uses parenting.
def make_bed(k,x,y):
 from mathutils import Matrix
 tr=Matrix.Translation(Vector(pos(k,x,y,level)))
 for source,original in bed_world:
  ob=source.copy();ob.parent=None;sc.collection.objects.link(ob);ob.matrix_world=tr@original;ob.name=k+' | letto · '+source.name;flag(ob,k,'arredi alti')
def walls(k,d):
 x,y,X,Y=d['deck'];side,a,b=d['door']
 # F uses a cut at the documented envelope, L shows full-height enclosing joinery with an open sliding door.
 top=4.01 if v=='F' else 4.0
 spans={'N':(x,X),'S':(x,X),'W':(y,Y),'E':(y,Y)}
 def edge(st,u,w,z,h):
  if w<=u+.002 or h<=.002:return
  bb={'N':[u,y,w,y+.08],'S':[u,Y-.08,w,Y],'W':[x,u,x+.08,w],'E':[X-.08,u,X,w]}[st]
  ob=box(k,'Parete camera '+st,bb,z,h,lime,'pareti alte');ob['lato']=st
 for st,(lo,hi) in spans.items():
  if k=='retro' and st=='N':continue  # Existing north wall, with the window onto the terrace.
  if k=='piazza' and st=='S':
   # Internal glazing facing the recessed existing facade. No new external window is assumed.
   edge(st,lo,hi,level,.68)
   edge(st,lo,lo+.22,level+.68,top-level-.68);edge(st,hi-.22,hi,level+.68,top-level-.68)
   pane=material('Vetro interno '+v,(.57,.68,.62),.18);bs=pane.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.24;pane.diffuse_color=(.57,.68,.62,.24)
   ob=box(k,'Vetrata verso balcone · solo interna',[lo+.22,Y-.045,hi-.22,Y-.031],level+.68,top-level-.68,pane,'pareti alte');ob['lato']='S'
   continue
  if st!=side:edge(st,lo,hi,level,top-level);continue
  edge(st,lo,a,level,top-level);edge(st,b,hi,level,top-level)
  if top-level>2.10:edge(st,a,b,level+2.10,top-level-2.10)
 if v=='L':
  # Sliding panel is shown parked along the inside face (door does not sweep the landing).
  w=b-a
  if side=='W':bb=[x+.085,b+.015,x+.12,b+.015+w]
  else:bb=[a-w-.025,y+.085,a-.025,y+.12]
  box(k,'Anta scorrevole aperta',bb,level+.015,2.05,ash,'porta')
def support(k,d):
 x,y,X,Y=d['deck'];box(k,'Impalcato',d['deck'],level-thick,thick,wood,'solaio')
 if v=='F':
  for xx,yy in [(x+.07,y+.07),(X-.07,y+.07),(x+.07,Y-.07),(X-.07,Y-.07)]:box(k,'Montante da dimensionare',[xx-.045,yy-.045,xx+.045,yy+.045],0,level-thick,iron,'appoggi')
 else:
  box(k,'Base chiusa di stivaggio',[x+.025,y+.025,X-.025,Y-.025],.018,level-thick-.018,wood,'contenimento')
  # Faces toward the free ground route, accessed without entering the storage.
  for i in range(4):
   yy=y+(Y-y)*i/4+.015;face=x+.012 if k=='piazza' else x+.010
   box(k,'Frontale apribile',[face-.01,yy,face+.01,yy+(Y-y)/4-.025],.07,level-thick-.12,ash,'contenimento',.003)
 for name,b in [('Pianerottolo alto',d['land'])]:box(k,name,b,level-.13,.13,wood,'sbarco')
 if k=='retro':box(k,'Soglia di raccordo',[.90,.105,.92,.895],level-.055,.055,ash,'sbarco',.002)
 rsum=0;n=sum(f[4] for f in d['flights']);rise=level/n
 for ix,f in enumerate(d['flights']):
  dr,fx,fy,w,nn,g=f;steps=list(walk(f))
  for j,b in enumerate(steps,1):
   z=(rsum+j)*rise;box(k,'Rampa '+str(ix+1)+' pedata '+str(j),b,z-.055,.055,ash,'scala',.005)
  dx,dy={'N':(0,-1),'W':(-1,0),'E':(1,0)}[dr];vx,vy=(w,0) if dr=='N' else (0,w)
  for side in (0,1):
   ox,oy=side*vx,side*vy
   beam(k,'Cosciale rampa',(fx+ox,fy+oy,(rsum+1)*rise-.09),(fx+(nn-1)*g*dx+ox,fy+(nn-1)*g*dy+oy,(rsum+nn)*rise-.09),.032,iron,'scala')
   beam(k,'Corrimano rampa',(fx+ox,fy+oy,(rsum+1)*rise+.90),(fx+(nn-1)*g*dx+ox,fy+(nn-1)*g*dy+oy,(rsum+nn)*rise+.90),.018,wood,'scala')
   for j in range(0,nn-1,2):
    xx=fx+(j+.45)*g*dx+ox;yy=fy+(j+.45)*g*dy+oy;z=(rsum+j+1)*rise
    beam(k,'Montante parapetto',(xx,yy,z),(xx,yy,z+.92),.012,iron,'scala')
  rsum+=nn
  if ix==0 and 'turn' in d:box(k,'Ripiano di volta',d['turn'],rsum*rise-.13,.13,wood,'scala')
 # Guard free, non-access edges of the upper landing.
 b=d['land'];x0,y0,x1,y1=b
 edges=([(x0,y0,x0,y1),(x0,y0,x1,y0)] if k=='retro' else ([(x0,y0,x0,y1),(x0,y0,x1,y0)] if v=='F' else [(x1,y0,x1,y1),(x0,y0,x1,y0)]))
 for x0,y0,x1,y1 in edges:
  beam(k,'Protezione sbarco',(x0,y0,level+1.0),(x1,y1,level+1.0),.018,iron,'sbarco')
  for j in range(7):
   t=j/6;xx=x0+(x1-x0)*t;yy=y0+(y1-y0)*t;beam(k,'Bacchetta sbarco',(xx,yy,level),(xx,yy,level+1),.008,iron,'sbarco')
for k,r in DATA[v].items():
 support(k,r);walls(k,r);make_bed(k,*r['bed'])
 b=r['ward'];box(k,'Armadio basso',b,level+.04,.83,ash,'arredi alti',.015)
 x,y,X,Y=b
 for j in (0,1):box(k,'Fronte a doghe',[x+j*(X-x)/2+.008,y-.007,x+(j+1)*(X-x)/2-.008,y+.006],level+.065,.78,felt,'arredi alti')
 # Narrow bedside shelf with a book.
 bx,by=r['bed'];sx=bx+.51 if k=='piazza' else bx-.76
 box(k,'Comodino',[sx,by-.85,sx+.24,by-.52],level+.03,.39,ash,'arredi alti')
 box(k,'Libro',[sx+.03,by-.81,sx+.2,by-.60],level+.42,.026,paper,'arredi alti')
# Keep informative layout at ground level: a reading table under F, a free route for L.
if v=='F':
 from mathutils import Matrix
 oldbed=[o for o in sc.objects if o.type=='MESH' and o.get('ambiente')=='Camera sulla piazza' and o.get('strato')=='Arredi']
 ref=next(o for o in oldbed if o.name.startswith('Sommier'))
 bpts=[ref.matrix_world@Vector(p) for p in ref.bound_box];c=sum(bpts,Vector())/len(bpts);c.z=0
 tr=Matrix.Translation(Vector(pos('piazza',1.65,2.30,0)))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(-c)
 for ob in oldbed:ob.matrix_world=tr@ob.matrix_world;ob['programma']='Matrimoniale inferiore'
def camera(name,eye,target,lens=32,ortho=None):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new('R05 | '+name,d);sc.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler();d.lens=lens
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o
cams={}
for k,r in DATA[v].items():
 x,y,X,Y=r['deck'];cx=(x+X)/2;cy=(y+Y)/2
 cams[k]=camera(k,pos(k,cx-7,cy+5,level+7),pos(k,cx,cy,level+.1),ortho=6.85 if k=='piazza' else 6.85)
 bx,by=r['bed'];cams[k+'-interno']=camera(k+' interno',pos(k,x+.3,Y-.24,level+(.82 if v=='F' else 1.50)),pos(k,bx,by-.45,level+.56),25)
cams['insieme']=camera('Due camere in sezione',worldpix(-280,780,24),worldpix(236,558,1.4),ortho=24.0)
sc.camera=cams['insieme'];sc['R05']='Camere a quota '+str(level)+' m; camere e altezze da verificare sul posto. Due accessi indipendenti.'
bpy.context.preferences.filepaths.save_version=0
for o in sc.objects:o.select_set(False)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/(v+'.blend')),compress=True)
for o in sc.objects:
 if o.type in ('MESH','CURVE') and o.get('strato')!='Contesto':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/(v+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
sc.render.engine='CYCLES';sc.cycles.samples=22;sc.cycles.max_bounces=5;sc.cycles.adaptive_threshold=.07;sc.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX','CUDA'):
 try:
  prefs.compute_device_type=t;prefs.refresh_devices();gpu=[d for d in prefs.devices if d.type==t]
  if gpu:
   for d in prefs.devices:d.use=d in gpu
   sc.cycles.device='GPU';break
 except:pass
def render(tag,c):
 sc.camera=c;sc.render.image_settings.file_format='WEBP';sc.render.image_settings.quality=92;sc.render.resolution_percentage=100
 sc.render.resolution_x,sc.render.resolution_y=(1250,940) if tag!='insieme' else (1500,1150)
 sc.render.film_transparent=not tag.endswith('interno')
 # Cutaway: retain original floors and source walls at plinth level; isolate the relevant intervention for local shots.
 changed=[]
 for o in sc.objects:
  if o.type not in ('MESH','CURVE'):continue
  k=o.get('camera_alta');layer=o.get('strato','');part=o.get('elemento_R05','')
  if tag.endswith('interno'):hide=layer=='Contesto' and False
  elif tag=='insieme':
   hide=not k and not o.name.startswith(('Pavimento','Balcone spezzato','Gradino','Pianerottolo','Murature DOCFA')) or not k and o.name.startswith('Murature DOCFA') and o.name!='Murature DOCFA'
   hide=hide or k and part in ('pareti alte','porta') and o.get('lato') in ('W','S')
  else:
   hide=(k!=tag or part=='pareti alte' and o.get('lato') in ('W','S') or part=='porta')
  if hide:changed.append((o,o.hide_render));o.hide_render=True
 sc.render.filepath=str(out/(v+'-'+tag+'.webp'));bpy.ops.render.render(write_still=True)
 for o,old in changed:o.hide_render=old
for tag,c in cams.items():render(tag,c)
print('R05_READY',v,flush=True)
