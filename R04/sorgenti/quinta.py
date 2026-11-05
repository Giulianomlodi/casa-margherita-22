from pathlib import Path
import math,bpy,os
from mathutils import Vector
root=Path(__file__).resolve().parent;id=os.environ['CASE_R04'];out=root.parent/'decisioni';sc=bpy.context.scene;s=.0254
def xy(x,y,z):return ((x-215)*s,(550-y)*s,z)
def rehome(ob):
 ob['ambiente']='Sala sul giardino';ob['strato']='Serramenti';ob['versione']=id
def bar(name,a,b,z,h,depth,mat):
 dx=(b[0]-a[0])*s;dy=(a[1]-b[1])*s
 bpy.ops.mesh.primitive_cube_add(size=1,location=xy((a[0]+b[0])/2,(a[1]+b[1])/2,z));o=bpy.context.object;o.name=name;o.dimensions=(math.hypot(dx,dy),depth,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler.z=math.atan2(dy,dx)
 o.data.materials.append(mat);rehome(o);return o
timber=bpy.data.materials['Castagno mordenzato della quinta'];glass=bpy.data.materials['Vetro stampato storico']
parts=[o for o in sc.objects if o.name.startswith('Quinta in legno')];cy=390 if id!='T' else 389
def xval(o):return o.location.x/s+215
for o in parts:
 name=o.name.lower()
 if ('vetro' in name and xval(o)<244) or ('montante' in name and 205<xval(o)<227):
  bpy.data.objects.remove(o,do_unlink=True)
for o in list(sc.objects):
 if o.name.startswith('Traversa lignea da F09') and o.location.z<1:o.location.x+=(245.6-215)*s*.5;o.scale.x*=(338-245.6)/(338-215)
# F01/F09 show two open leaves along the clear passage. Model their swing; 1.5 m nominal clear span is a visual hypothesis.
for side,x in [(-1,184.3),(1,245.3)]:
 end=(x+side*.7,cy-29)
 for xx,yy in [(x,cy),(end[0],end[1])]:bar('Battente aperto · montante',(xx-.5,yy),(xx+.5,yy),1.5,2.97,.053,timber)
 for z,h in [(.065,.11),(.78,.10),(2.945,.08)]:bar('Battente aperto · traversa',(x,cy),end,z,h,.046,timber)
 bar('Battente aperto · vetro', (x,cy-1), (end[0],end[1]+1),1.5,2.84,.009,glass)
bar('Montante del sopraluce',(214.4,cy),(216,cy),3.30,.56,.055,timber)
# Keep privacy leaf parked outside the double-leaf opening.
for obj in list(sc.objects):
 if obj.name.startswith('Anta scorrevole aperta'):obj.location.x+=30*s
sc['Quinta_documentazione']='F01 F09 F11 e V1 32 s, due battenti aperti; posizione e luce di passaggio interpretate.'
bpy.context.preferences.filepaths.save_version=0
sc.camera=bpy.data.objects.get('R04 | Dal salone verso la quinta');bpy.ops.wm.save_as_mainfile(filepath=str(out/(id+'.blend')),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects:
 if o.type in ('MESH','CURVE') and o.get('strato')!='Contesto':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/(id+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
pref=bpy.context.preferences.addons['cycles'].preferences
for t in ['OPTIX','CUDA']:
 try:
  pref.compute_device_type=t;pref.refresh_devices();devices=[d for d in pref.devices if d.type==t]
  if devices:
   for d in pref.devices:d.use=d in devices
   sc.cycles.device='GPU';break
 except:pass
sc.cycles.samples=22;sc.cycles.max_bounces=6;sc.cycles.glossy_bounces=2;sc.cycles.transmission_bounces=4;sc.cycles.adaptive_threshold=.06;sc.cycles.use_denoising=True
sc.render.resolution_x=1440;sc.render.resolution_y=960;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='WEBP';sc.render.image_settings.quality=91
for name,label in [('sala','Dal salone verso la quinta'),('detail','Retro verso la quinta')]:
 sc.camera=bpy.data.objects['R04 | '+label];sc.render.filepath=str(out/(id+'-'+name+'.webp'));bpy.ops.render.render(write_still=True)
print('QUINTA_OK',id,flush=True)
