from pathlib import Path
import bpy,math,os,json,sys
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parent;out=root.parent/'decisioni';out.mkdir(exist_ok=True)
id=os.environ['CASE_R04'];sc=bpy.context.scene;S=.0254
def pt(x,y,z):return Vector(((x-215)*S,((300 if id.startswith("G") else 550)-y)*S,z))
def loc(ob,x,y,z):ob.location=pt(x,y,z)
def room(o):return o.get('ambiente','')
def delete(objs):
 for o in list(objs):bpy.data.objects.remove(o,do_unlink=True)
def move(objs,src,dst,rot=0):
 m=Matrix.Translation(pt(*dst))@Matrix.Rotation(math.radians(rot),4,'Z')@Matrix.Translation(-pt(*src))
 for o in objs:o.matrix_world=m@o.matrix_world
def extra(n,x,y,w,h,z,height,mat,zone,edge=.012):
 bpy.ops.mesh.primitive_cube_add(size=1)
 o=bpy.context.object;o.name=n;loc(o,x+w/2,y+h/2,z+height/2)
 o.dimensions=(w*S,h*S,height);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if edge:
  mod=o.modifiers.new('Spigoli lavorati','BEVEL');mod.width=edge;mod.segments=3
  o.modifiers.new('Normali','WEIGHTED_NORMAL')
 material=bpy.data.materials.get(mat)
 if material:o.data.materials.append(material)
 o['ambiente']=zone;o['strato']='Arredi';o['versione']=id
 return o
def items(roomname,starts):
 return [o for o in sc.objects if room(o)==roomname and any(o.name.startswith(n) for n in starts)]
def group_of_names(starts):return [o for o in sc.objects if any(o.name.startswith(n) for n in starts)]
def bed_new(x,y,w,h):
 extra('Telaio letto',x,y,w,h,.08,.23,'Castagno','Camera sul retro',.028)
 extra('Materasso in lino',x+1,y+1,w-2,h-2,.31,.23,'Lino','Camera sul retro',.065)
 extra('Piumino',x+1,y+21,w-2,h-23,.53,.10,'Lino','Camera sul retro',.052)
 extra('Testiera',x,y,w,2.2,.07,.93,'Salvia','Camera sul retro',.028)
 for off in ([3] if w<45 else [3,w*.53]):
  extra('Guanciale tessile',x+off,y+5,(w-7 if w<45 else w*.41),14,.53,.10,'Lino','Camera sul retro',.049)
def cabinet(x,y,w,h,z,height,zone):
 extra('Falegnameria su misura',x,y,w,h,z,height,'Castagno',zone,.015)
 for j in range(3):
  yy=y+j*h/3+.4
  extra('Anta con fuga',x+w,yy,.6,h/3-.8,z+.03,height-.06,'Salvia',zone,.008)
  extra('Tirante brunito',x+w+.65,yy+2,1,3.4,min(z+height-.15,1.12),.018,'Bronzo',zone,.005)
def furnish():
 sc.frame_set(1)
 delete(o for o in sc.objects if (room(o)=='Vano d’angolo' and o.get('strato')=='Arredi') or o.get('strato')=='Quota alta')
 cabinet(330,899,14,61,.015,1.38,'Vano d’angolo')
 cabinet(250,702,19,83,.01,1.86,'Servizi centrali')
 # The existing bedside table projected through the party wall. Relocate the double bed group together.
 bedroom=items('Camera sulla piazza',('Sommier','Materasso','Testiera','Piumone','Plaid','Guanciale','Comodino'))
 bedroom+=[o for o in sc.objects if o not in bedroom and ('cuscino' in o.name.lower() or 'cuscitura' in o.name.lower()) and room(o)=='Camera sulla piazza']
 sofa=items('Sala sul giardino',('Divano','Tappeto','Tavolino in pietra','Lampada da lettura'))
 delete(items('Sala sul giardino',('Tavolino di appoggio','Vaso tornito')))
 dining=items('Sala sul giardino',('Piano in castagno','Gamba tavolo','Ciotola','Sedia imbottita'))
 move(bedroom,(287,912.5,0),(280,911,0),-90)
 if id in ('B','D'):
  # Dining north of the entrance, sofa south-east. Avoid the 0.97 m kitchen opening.
  move(dining,(256.5,502,0),(230,450,0),90)
  move(sofa,(273,289,0),(300,548,0),-90)
 if id=='B':bed_new(279,264,36,79)
 if id=='D':
  for x in [203,265]:
   extra('Piano lavoro',x,251,55,27,.735,.04,'Castagno','Atelier')
   for xx in [x+2,x+51]:
    for yy in [253,274]:extra('Gamba scrivania',xx,yy,1.5,1.5,0,.735,'Ferro','Atelier',.003)
   ob=bpy.data.objects.get('Sedia giardino').copy();ob.data=ob.data.copy();sc.collection.objects.link(ob);ob.name='Sedia atelier';loc(ob,x+27,291,0);ob['ambiente']='Atelier'
 if id=='E':
  delete(bedroom);bed_new(247,253,63,79)
  move(sofa,(273,289,0),(268,895,0),-90)
  for o in sofa:o['ambiente']='Stanza sulla piazza'
 if id=='C':
  # Deck along the solid right wall, guard and steps away from the historic screen passage.
  couch=[o for o in sofa if o.name.startswith('Divano')]
  delete([o for o in sofa if o not in couch])
  delete(couch)
  for x in [287,314]:
   for y in [321,348]:extra('Piede poltrona',x,y,2,2,.72,.19,'Castagno','Pedana')
  extra('Poltrona imbottita',285,319,33,33,.9,.24,'Salvia','Pedana',.08)
  extra('Schienale',285,318,33,5,1.08,.50,'Salvia','Pedana',.07)
  for x in [284,315]:extra('Bracciolo',x,320,4.3,32,1.12,.20,'Salvia','Pedana',.047)
  for xx in range(272,337,4):extra('Bacchetta lato nord',xx,264,.65,.65,.72,1,'Ferro','Pedana',.002)
  extra('Corrimano lato nord',270,264,68,1.6,1.72,.055,'Castagno','Pedana')
  extra('Pedana chiusa +0,72',270,264,68,115,0,.72,'Castagno','Pedana')
  for j in range(3):
   extra('Cassettone estraibile',269.3,311+j*22,.7,21,0.06,.58,'Salvia','Pedana')
  for j in range(3):
   extra('Pedata in castagno',237+j*11,267,11,36,0,.18*(j+1),'Castagno','Pedana')
  for yy in [307,341,375]:extra('Montante parapetto',270,yy,1.3,1.3,.72,1.02,'Ferro','Pedana')
  extra('Corrimano bordo',270,306,1.5,71,1.72,.055,'Castagno','Pedana')
  for yy in range(309,376,4):extra('Bacchetta',270,yy,.65,.65,.72,1,'Ferro','Pedana',.002)
  for xx in range(271,337,4):extra('Bacchetta testata',xx,377,.65,.65,.72,1,'Ferro','Pedana',.002)
  extra('Corrimano testata',270,377,68,1.5,1.72,.055,'Castagno','Pedana')
 # Place the sink on the long wall, freeing the illustrated kitchen-to-bath opening.
 sink=items('Bagno sul retro',('Mobile lavabo','Catino lavabo','Miscelatore'))
 move(sink,(82,220,0),(77,206,0),90)
 for o in sc.objects:
  if o.type=='MESH':o['versione']=id
 sc['Descrizione']='R04 - pianta catastale controllata; altezze e profili locali da rilevare.'
 sc.name='Casa Margherita R04 | '+id

def cam(n,eye,aim,lens=32,ortho=0):
 d=bpy.data.cameras.new(n);ob=bpy.data.objects.new('R04 | '+n,d);sc.collection.objects.link(ob)
 ob.location=pt(*eye);ob.rotation_euler=(pt(*aim)-ob.location).to_track_quat('-Z','Y').to_euler()
 d.lens=lens;d.clip_start=.03
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return ob
def native_and_glb():
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.file.pack_all()
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(id+'.blend')),compress=True)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in sc.objects:
  if ob.type=='MESH' and ob.get('strato')!='Contesto':ob.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(out/(id+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
def render(n,c,cut=False):
 sc.camera=c
 changes=[]
 if cut:
  for o in sc.objects:
   if o.type=='MESH' and (o.get('strato') in ('Coperture','Contesto','Illuminazione') or o.name.startswith(('Cornice','Modanatura'))):
    changes.append((o,o.hide_render));o.hide_render=True
 sc.render.resolution_x=1440 if not cut else 1300;sc.render.resolution_y=960 if not cut else 1200
 sc.render.resolution_percentage=100;sc.render.filepath=str(out/(id+'-'+n+'.webp'))
 sc.render.image_settings.file_format='WEBP';sc.render.image_settings.quality=91;bpy.ops.render.render(write_still=True)
 for o,val in changes:o.hide_render=val

def finish_existing():
 # F12 and V1 44 s show ceramic wall finishes, oblong high windows and a boarded ceiling in the kitchen.
 if not id.startswith('G'):
  zone='Cucina'
  for row in range(6):
   for j in range(13):
    y=248+j*15.4
    extra('Piastrella a parete',65.6,y,.42,15.2,.1+row*.30,.294,'Pietra' if (row+j)%4 else 'Lino',zone,.002)
  # Show only the visible straight run. Level is a modelling hypothesis, separately labelled in the report.
  for i in range(28):
   y=246+i*7.28
   extra('Doghe soffitto · quota ipotizzata',65.2,y,105.5,7.13,3.34,.032,'Castagno',zone,.002)['strato']='Coperture'
  for y in (267,305,343,381):
   extra('Luce alta · collocazione indicativa',66.25,y,.46,31,2.63,.49,'Vetro opalino',zone,.002)
   for pos in (y-.6,y+15.2,y+31):
    extra('Telaio sopraluce indicativo',66.55,pos,.65,.8,2.62,.51,'Cornice',zone,.001)
  for o in sc.objects:
   if o.name.startswith('Doghe soffitto'):o['strato']='Coperture'
 else:
  from mathutils import Color
  # Video V2: masonry piers and warm, exposed arched soffits, not a newly painted interior.
  def worn(name,a,b,size):
   m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*a,1);nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
   tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=size;tex.inputs['Detail'].default_value=4.5
   ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*a,1);ramp.color_ramp.elements[1].color=(*b,1)
   nt.links.new(tex.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs['Base Color'])
   bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.008;bump.inputs['Strength'].default_value=.29
   nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],bs.inputs['Normal']);bs.inputs['Roughness'].default_value=.89
   return m
  mats=[worn('Argilla cotta '+str(i),(.19+i*.028,.075+i*.013,.043+i*.008),(.43,.25,.16),11) for i in range(4)]
  lime=worn('Pietra e calce con tracce del tempo',(.13,.105,.077),(.43,.365,.28),5.8)
  floor=worn('Battuto esistente',(.065,.068,.062),(.22,.21,.18),24)
  for o in sc.objects:
   if o.type!='MESH':continue
   mat=mats[sum(map(ord,o.name))%4] if o.name.startswith(('Concio','Volta ribassata')) else lime if o.name.startswith(('Muratura perimetrale','Pilastro isolato')) else floor if o.name.startswith('Battuto') else None
   if mat:o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)

def architectural_detail():
 if id.startswith('G'):return
 room_='Sala sul giardino'
 def wood():
  m=bpy.data.materials.new('Castagno mordenzato della quinta');m.use_nodes=True;m.diffuse_color=(.22,.091,.039,1)
  nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.38
  tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=8;tex.inputs['Detail'].default_value=2
  col=nt.nodes.new('ShaderNodeValToRGB');col.color_ramp.elements[0].color=(.075,.024,.009,1);col.color_ramp.elements[1].color=(.29,.095,.032,1)
  nt.links.new(tex.outputs['Fac'],col.inputs[0]);nt.links.new(col.outputs[0],bs.inputs['Base Color']);return m
 timber=wood()
 for o in list(sc.objects):
  if o.type!='MESH' or not o.name.startswith('Quinta in legno'):continue
  if 'vetro' in o.name:
   # Original screen has hammered, translucent glass; leave the passage at the left free.
   old=o.data.materials[0];m=bpy.data.materials.get('Vetro stampato storico')
   if not m:
    m=bpy.data.materials.new('Vetro stampato storico');m.use_nodes=True;m.diffuse_color=(.56,.68,.63,.42)
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(.74,.83,.78,1);bs.inputs['Transmission Weight'].default_value=.96;bs.inputs['Roughness'].default_value=.18;bs.inputs['IOR'].default_value=1.48
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=320;tex.inputs['Detail'].default_value=2;b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.27;b.inputs['Distance'].default_value=.0025;nt.links.new(tex.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs[0],bs.inputs['Normal'])
   o.data=o.data.copy();o.data.materials[0]=m
  else:o.data=o.data.copy();o.data.materials[0]=timber
 for z,h in [(.03,.11),(.77,.102),(2.97,.08)]:
  extra('Traversa lignea da F09',215,388.55,123,2.9,z,h,timber.name,room_,.005)['strato']='Serramenti'
 # Removable privacy curtain and a sliding leaf for the proposed rear bedroom.
 if id in ('B','E'):
  extra('Rotaia reversibile',184,383.4,152,1.5,3.07,.052,'Bronzo',room_)['strato']='Serramenti'
  for j in range(8):
   extra('Tenda raccolta per privacy',185+j*2.8,383.6+(j%2)*1.5,3.8,1.9,.11,2.94,'Lino',room_,.016)['strato']='Serramenti'
  extra('Anta scorrevole aperta lato interno',216,384.6,30,1.6,0,2.94,timber.name,room_)['strato']='Serramenti'
 # Replace schematic pendant in the front bay with a five-arm fitting of the type visible in F09.
 for o in list(sc.objects):
  if o.type!='MESH' or not o.name.startswith(('Diffusore','Paralume','Cavo pendente','Rosone soffitto')):continue
  x=o.location.x/S+215;y=550-o.location.y/S
  if 190<x<300 and 248<y<600:delete([o])
 def bulb(n,x,y,z,scale,mat):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=12,location=pt(x,y,z));o=bpy.context.object;o.name=n;o.scale=scale
  o.data.materials.append(bpy.data.materials.get(mat));o['ambiente']=room_;o['strato']='Illuminazione'
 def pipe(n,coords,r,mat):
  c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=2
  sp=c.splines.new('BEZIER');sp.bezier_points.add(len(coords)-1)
  for bp,co in zip(sp.bezier_points,coords):bp.co=pt(*co);bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
  o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.data.materials.append(bpy.data.materials.get(mat));o['ambiente']=room_;o['strato']='Illuminazione'
 for cx,cy in [(240,510),(250,313)]:
  pipe('Sospensione',[(cx,cy,4.34),(cx,cy,3.15)],.007,'Bronzo');bulb('Nodo centrale',cx,cy,3.08,(.065,.065,.12),'Bronzo')
  for j in range(5):
   ang=j*math.tau/5;ux,uy=math.cos(ang),math.sin(ang)
   pipe('Braccio in ottone',[(cx,cy,3.09),(cx+7*ux,cy+7*uy,2.93),(cx+13*ux,cy+13*uy,3.01),(cx+13*ux,cy+13*uy,3.08)],.008,'Bronzo')
   bulb('Coppa',cx+13*ux,cy+13*uy,3.08,(.045,.045,.023),'Bronzo');bulb('Luce candela',cx+13*ux,cy+13*uy,3.15,(.019,.019,.067),'Vetro opalino')

if id in 'ABCDE':furnish()
finish_existing()
architectural_detail()
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.max_bounces=6;sc.cycles.transmission_bounces=4;sc.cycles.diffuse_bounces=3;sc.cycles.glossy_bounces=2;sc.cycles.adaptive_threshold=.065;sc.cycles.use_denoising=True;sc.frame_set(1)
prefs=bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX','CUDA'):
 try:
  prefs.compute_device_type=t;prefs.refresh_devices()
  gpu=[d for d in prefs.devices if d.type==t]
  if gpu:
   for dev in prefs.devices:dev.use=dev in gpu
   sc.cycles.device='GPU';break
 except:pass
else:sc.cycles.device='CPU'
if id.startswith('G'):
 cams={'sala':cam('Vista dal portale',(318,150,1.55),(157,358,2.14),28),'detail':cam('Archi e fondo',(325,414,1.55),(152,215,2.37),29)}
else:
 cams={'sala':cam('Dal salone verso la quinta',(205,602,1.55),(264,336,1.58),32),'detail':cam('Retro verso la quinta',(200,378,1.54),(285,276,1.23),30),'fronte':cam('Camera rettangolare',(181,829,1.53),(291,944,1.36),29),'cuneo':cam('Guardaroba dal lato largo',(410,965,1.53),(336,929,1.03),29),'cucina':cam('Cucina e soffitto ligneo',(112,426,1.55),(111,251,2.0),29),'giardino':cam('Giardino proposto',(321,216,1.54),(161,135,1.43),31)}
sc.camera=cams['sala'];native_and_glb()
for name,c in cams.items():render(name,c)
print('CASE_READY',id,flush=True)
