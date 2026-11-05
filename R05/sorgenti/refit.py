from pathlib import Path
import os,sys,math,bpy
from mathutils import Vector
d=Path(__file__).resolve().parent;sys.path.insert(0,str(d));from design import LEVEL,DATA,ORIGIN,S
v=os.environ['R05_VARIANT'];out=d.parent/'due-camere';sc=bpy.context.scene;z=LEVEL[v]
def pos(k,x,y,h):
 a,b=ORIGIN[k];return Vector(((a-215)*S+x,(550-b)*S-y,h))
def aim(cam,eye,target):
 cam.location=eye;cam.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
cams={k:bpy.data.objects['R05 | '+k] for k in ('piazza','retro')}
cam=bpy.data.objects['R05 | retro interno']
aim(cam,pos('retro',1.22,2.70,z+(.78 if v=='F' else 1.45)),pos('retro',3.27,1.34,z+.52))
cam.data.lens=27
for k,c in cams.items():
 x,y,X,Y=DATA[v][k]['deck'];cx=(x+X)/2;cy=(y+Y)/2
 aim(c,pos(k,cx+(8 if k=='piazza' else -8),cy+(-6 if k=='piazza' else 6),z+7.5),pos(k,cx,cy,z))
p=bpy.context.preferences.addons['cycles'].preferences
for t in ('OPTIX','CUDA'):
 try:
  p.compute_device_type=t;p.refresh_devices();ds=[x for x in p.devices if x.type==t]
  if ds:
   for x in p.devices:x.use=x in ds
   sc.cycles.device='GPU';break
 except:pass
sc.cycles.samples=20;sc.cycles.adaptive_threshold=.065;sc.cycles.max_bounces=5;sc.cycles.use_denoising=True
def shot(tag,c):
 sc.camera=c;changed=[];vis=[]
 ortho=tag in ('piazza','retro','insieme');sc.render.resolution_x=1440;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.film_transparent=ortho
 for o in sc.objects:
  if o.type not in ('MESH','CURVE'):continue
  k=o.get('camera_alta');typ=o.get('elemento_R05','')
  hide=False
  if tag=='insieme':
   hide=not k and not o.name.startswith(('Pavimento','Balcone spezzato','Gradino','Pianerottolo','Murature DOCFA')) or not k and o.name.startswith('Murature DOCFA') and o.name!='Murature DOCFA'
   hide=hide or (k and typ in ('pareti alte','porta') and o.get('lato') in ('W','S'))
  elif ortho:
   sides=('N','E') if k=='piazza' else ('W','S')
   hide=k!=tag or (typ=='pareti alte' and o.get('lato') in sides) or typ=='porta'
  if hide:changed.append((o,o.hide_render));o.hide_render=True
  elif not o.hide_render:vis.append(o)
 if ortho:
  bpy.context.view_layer.update();qx=c.rotation_euler.to_quaternion();u=qx@Vector((1,0,0));w=qx@Vector((0,1,0))
  pts=[o.matrix_world@Vector(p) for o in vis for p in o.bound_box]
  xs=[(p-c.location).dot(u) for p in pts];ys=[(p-c.location).dot(w) for p in pts]
  c.location+=u*((min(xs)+max(xs))/2)+w*((min(ys)+max(ys))/2)
  c.data.ortho_scale=max(max(xs)-min(xs),(max(ys)-min(ys))*sc.render.resolution_x/sc.render.resolution_y)*1.12
 sc.render.image_settings.file_format='WEBP';sc.render.image_settings.quality=91;sc.render.filepath=str(out/(v+'-'+tag+'.webp'));bpy.ops.render.render(write_still=True)
 for obj,val in changed:obj.hide_render=val
shot('retro-interno',cam)
for tag,c in cams.items():shot(tag,c)
shot('insieme',bpy.data.objects['R05 | Due camere in sezione'])
sc.render.film_transparent=False;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/(v+'.blend')),compress=True)
