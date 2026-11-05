"""Presentation cutaways generated from the same editable scene, with capped horizontal wall sections."""
import bpy,bmesh,math
from mathutils import Vector
from pathlib import Path
r=Path(__file__).resolve().parents[1];atlas=r.parent/'Atlante_3D'
import os
for f in sorted((atlas/'modelli').glob('*.blend')):
 if os.environ.get('CM_RESTRICT') and f.stem not in os.environ['CM_RESTRICT'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(f));scene=bpy.context.scene;scene.frame_set(1)
 scene.cycles.samples=5;scene.cycles.denoiser='OPTIX';scene.cycles.use_denoising=True;scene.render.use_persistent_data=False
 pref=bpy.context.preferences.addons['cycles'].preferences
 try:
  pref.compute_device_type='OPTIX';pref.refresh_devices()
  for d in pref.devices:d.use=d.type=='OPTIX'
  scene.cycles.device='GPU'
 except Exception:pass
 points=[];garage=f.stem.startswith('G');cut=1.20 if not garage else 1.45
 for ob in list(scene.objects):
  if ob.type!='MESH':continue
  layer=ob.get('strato','')
  if layer in ('Contesto','Coperture','Illuminazione'):ob.hide_render=True;continue
  bounds=[ob.matrix_world@Vector(c) for c in ob.bound_box];heights=[v.z for v in bounds]
  section=layer in ('Struttura','Serramenti','Finiture') and not (garage and ('Concio' in ob.name or 'Pilastro' in ob.name))
  if section and min(heights)>=cut:ob.hide_render=True;continue
  if section and max(heights)>cut+.001:
   local=ob.matrix_world.inverted()@Vector((0,0,cut));normal=ob.matrix_world.to_3x3().transposed()@Vector((0,0,1))
   me=ob.data.copy();ob.data=me;bm=bmesh.new();bm.from_mesh(me)
   res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=local,plane_no=normal.normalized(),clear_outer=True,dist=.00001)
   edges=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
   if edges:
    try:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
    except RuntimeError:pass
   bm.to_mesh(me);bm.free()
  points.extend(Vector((v.x,v.y,min(v.z,cut) if section else v.z)) for v in bounds)
 camera=scene.camera;camera.data.type='ORTHO'
 direction=Vector((1.15,-.38,1.25)).normalized();rot=(-direction).to_track_quat('-Z','Y');right=rot@Vector((1,0,0));up=rot@Vector((0,1,0))
 xs=[p.dot(right) for p in points];ys=[p.dot(up) for p in points];ds=[p.dot(direction) for p in points]
 center=right*((min(xs)+max(xs))/2)+up*((min(ys)+max(ys))/2)+direction*((min(ds)+max(ds))/2)
 camera.location=center+direction*65;camera.rotation_euler=rot.to_euler();camera.data.ortho_scale=max(max(xs)-min(xs),(max(ys)-min(ys))*1.58)*1.10
 z=min(x.z for x in points)-.08
 bpy.ops.mesh.primitive_plane_add(size=260,location=(0,0,z));floor=bpy.context.object;mat=bpy.data.materials.new('Fondale studio');mat.diffuse_color=(.66,.69,.61,1);floor.data.materials.append(mat)
 light=bpy.data.lights.new('Softbox','AREA');light.energy=4400;light.shape='DISK';light.size=13
 ob=bpy.data.objects.new('Softbox',light);scene.collection.objects.link(ob);ob.location=(3,0,18)
 scene.render.resolution_x=1664;scene.render.resolution_y=1052;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='WEBP';scene.render.image_settings.quality=90
 scene.render.filepath=str(atlas/'render'/(f.stem+'-spaccato.webp'));bpy.ops.render.render(write_still=True);print(f.stem,'SPACCATO',flush=True)
