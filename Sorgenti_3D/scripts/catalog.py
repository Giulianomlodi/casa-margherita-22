"""Build a private, self-contained viewer shell and the illustrated catalog of verified views."""
from pathlib import Path
from PIL import Image
import json,sys,os,re,shutil
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1]; A=ROOT.parent/'Atlante_3D';cv2.setNumThreads(2)
DATA=json.loads((ROOT/'scripts/geometry.json').read_text())
titles={
 'P00':('Stato attuale · appartamento','La scala, i due vani sulla piazza, il vano centrale con la quinta vetrata e la terrazza aperta. Le forme delle volte sono ricostruzioni indicative.'),
 'P01':('Conservare la sequenza','Una camera sulla piazza e due ambienti di soggiorno separati dalla quinta in legno. Il deposito in alto libera il ripostiglio.'),
 'P02':('Due camere sulla piazza','Il divisorio traslato crea due camere con accessi indipendenti. Il giardino completo è una proposta da verificare con gli enti.'),
 'P03':('Atelier dietro il vetro','Due postazioni vicino alla finestra sul giardino e un filtro trasparente tra lavoro e soggiorno. Il volume alto ospita l’archivio.'),
 'P04':('La cucina degli ospiti','Due fronti di lavoro e il pranzo nel vano finestrato. La dispensa alta occupa la fascia finale della cucina.'),
 'P05':('Il salotto sulla piazza','Il giorno si sposta al balcone. La camera sul retro conserva davanti alla finestra la parte aperta del terrazzo.'),
 'G00':('Stato attuale · garage','Locale sul vicolo con pilastro centrale e archi. Posizione e dimensioni del piano alto osservato nel video sono ipotizzate.'),
 'GA':('G-A · Allestimento essenziale','Una vettura, una bicicletta e scaffalatura mobile. Riferimento per confrontare lo spazio libero.'),
 'GB':('G-B · Banco e biciclette','Una vettura sulla destra, due biciclette, banco da lavoro e cassettiere sul lato opposto alla manovra.'),
 'G01':('G-C · Deposito in quota','Il progetto G01 nella configurazione più completa. Il deposito alto su montanti laterali richiede verifiche strutturali e autorizzative.')}
concepts={'P01':[('P01','La quinta recuperata'),('P01-camera','Camera e guardaroba')],'P02':[('P02','Giardino d’inverno'),('P02-camera','La seconda camera'),('P02-alto','Il deposito sul filtro')],'P03':[('P03','Atelier sul giardino'),('P03-filtro','Dalla sala all’atelier')],'P04':[('P04','Il pranzo serale'),('P04-cucina','La cucina a due fronti')],'P05':[('P05','Salotto sul balcone'),('P05-parziale','La serra parziale')],'GA':[('GA','Garage essenziale')],'GB':[('GB','Banco e biciclette')],'G01':[('G01','Garage e banco')]}
sources={'P01':'f09','P01-camera':'f05','P02':'f15','P02-camera':'f07','P02-alto':'f04','P03':'f10','P03-filtro':'f09','P04':'f10','P04-cucina':'f12','P05':'f05','P05-parziale':'f15','G01':'v2-05','GA':'v2-05','GB':'v2-05'}
previews='--preview' in sys.argv
def rectilinear(pan,dest,pitch):
 if dest.exists() and dest.stat().st_mtime>=pan.stat().st_mtime:return
 im=cv2.imread(str(pan));H,W=im.shape[:2]
 w,h=1552,1008;f=w/(2*np.tan(np.deg2rad(79)/2))
 u=(np.arange(w,dtype=np.float32)+.5-w/2)/f
 v=-(np.arange(h,dtype=np.float32)+.5-h/2)/f
 xx,yy=np.meshgrid(u,v);rad=np.deg2rad(pitch);z=np.cos(rad)-yy*np.sin(rad);y=np.sin(rad)+yy*np.cos(rad)
 lon=np.arctan2(xx,z);lat=np.arctan2(y,np.sqrt(xx*xx+z*z))
 mx=((lon/(2*np.pi)+.5)*W-.5).astype(np.float32);my=((.5-lat/np.pi)*H-.5).astype(np.float32)
 rect=cv2.remap(im,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_WRAP)
 Image.fromarray(cv2.cvtColor(rect,cv2.COLOR_BGR2RGB)).save(dest,quality=90,method=4)
def thumbnail(path):
 f=A/path;out=A/'miniature'/(f.parent.name+'-'+f.name)
 if f.exists() and (not out.exists() or out.stat().st_mtime<f.stat().st_mtime):
  im=Image.open(f);im.thumbnail((248,153));im.convert('RGB').save(out,quality=76,method=2)
 return str(out.relative_to(A)).replace('\\','/')
def convert_photo(name,label,source):
 target=A/'atmosfere'/name
 if not target.exists():Image.open(source).convert('RGB').save(target,quality=88)
 return dict(key='documento',name=label,kind='photo',image='atmosfere/'+name)
def generate():
 (A/'miniature').mkdir(exist_ok=True);catalog={}
 for id,(name,brief) in titles.items():
  meta=json.loads((A/'modelli'/f'{id}.json').read_text(encoding='utf8'));items=[]
  for k,(f,t) in enumerate(concepts.get(id,[])):
   ref=sources[f];path=ROOT.parent/'materiali'/(ref+'.jpg')
   src=convert_photo('fonte-'+ref+'.webp','Foto di partenza',path)['image']
   items.append(dict(key='concept' if k==0 else 'concept-'+str(k),name=t,kind='concept',image='atmosfere/'+f+'.webp',reference=src))
  if id in ('P00','G00'):
   folder=ROOT.parent/'materiali'
   items.append(convert_photo(id+'-fonte.webp','Fotografia di riscontro' if id=='P00' else 'Fotogramma della visita',folder/('f09.jpg' if id=='P00' else 'v2-05.jpg')))
  roomplans=list(DATA['rooms'].values()) if id.startswith('P') else [DATA['garageInner'],[(177,244),(201,244),(201,267),(177,267)]]
  ax=f'render/{id}-spaccato.webp';items.append(dict(key='assonometria',kind='render',image=ax,name='Spaccato complessivo'))
  for key,stop in meta['tappe'].items():
   entry=dict(key=key,name=stop['nome'],kind='render',camera=stop['occhio']+stop['bersaglio'])
   delta=np.array(stop['bersaglio'])-np.array(stop['occhio']);pitch=np.rad2deg(np.arctan2(delta[2],np.linalg.norm(delta[:2])))
   for day in ['giorno','sera']:
    pan=A/'panorami'/f'{id}-{key}-{day}.webp';flat=A/'render'/f'{id}-{key}-{day}.webp'
    if pan.exists():
     rectilinear(pan,flat,pitch);entry['pano' if day=='giorno' else 'panoNight']=pan.relative_to(A).as_posix()
    if flat.exists() or day=='giorno':entry['image' if day=='giorno' else 'night']=flat.relative_to(A).as_posix()
   items.append(entry)
  for item in items:
   item['thumb']=thumbnail(item['image'])
   if not previews:
    assert (A/item['image']).is_file(),item
    assert (A/item['thumb']).is_file(),item
  if not previews:
   assert sum(bool(item.get('pano')) for item in items)==5, id
   assert sum(bool(item.get('panoNight')) for item in items)==5, id
  catalog[id]=dict(label=(id+' · ' if id.startswith('P') else '')+name,brief=brief,nodes=meta['nodi'],layers=meta['strati'],plan=roomplans,items=items)
 html=(ROOT/'scripts/template.html').read_text(encoding='utf-8-sig');code=(ROOT/'cache/viewer.bundle.js').read_text(encoding='utf8').replace('</script','<\\/script')
 html=html.replace('__BOOT__','<script id="catalog" type="application/json">'+json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+'</script><script>'+code+'</script>')
 (A/'index.html').write_text(html,encoding='utf8');(ROOT/'cache/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf8')
 print(len(catalog),'versioni;',sum(len(v['items']) for v in catalog.values()),'viste nel catalogo.')
if __name__=='__main__':generate()
