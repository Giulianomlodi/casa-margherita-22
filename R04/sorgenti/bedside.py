import bpy,os
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'decisioni';id=os.environ['CASE_R04'];sc=bpy.context.scene
o=bpy.data.objects['Comodino'];o.location.y-=.30;sc['Comodino_R04']='correzione 30 cm verso sud lungo il lato libero della matrimoniale'
bpy.context.preferences.filepaths.save_version=0;sc.camera=bpy.data.objects['R04 | Dal salone verso la quinta'];bpy.ops.wm.save_as_mainfile(filepath=str(out/(id+'.blend')),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in sc.objects:
 if ob.type in ('MESH','CURVE') and ob.get('strato')!='Contesto':ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/(id+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
p=bpy.context.preferences.addons['cycles'].preferences
for t in ['OPTIX','CUDA']:
 try:
  p.compute_device_type=t;p.refresh_devices();ds=[x for x in p.devices if x.type==t]
  if ds:
   for x in p.devices:x.use=x in ds
   sc.cycles.device='GPU';break
 except:pass
sc.camera=bpy.data.objects['R04 | Camera rettangolare'];sc.cycles.samples=20;sc.cycles.max_bounces=6;sc.cycles.adaptive_threshold=.065;sc.cycles.use_denoising=True;sc.render.resolution_x=1440;sc.render.resolution_y=960;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='WEBP';sc.render.image_settings.quality=91;sc.render.filepath=str(out/(id+'-fronte.webp'));bpy.ops.render.render(write_still=True)
