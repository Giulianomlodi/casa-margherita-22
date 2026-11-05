"""Companion A3 portfolio. Uses the same verified asset catalog as the live 3D experience."""
from pathlib import Path
from io import BytesIO
import json,sys
from PIL import Image,ImageOps
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3,landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parents[1];a=root.parent/'Atlante_3D';catalog=json.loads((root/'cache/catalog.json').read_text(encoding='utf8'))
for n,f in [('Titolo','georgia.ttf'),('Testo','segoeui.ttf'),('Grassetto','segoeuib.ttf')]:pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
W,H=landscape(A3);draft='--preview' in sys.argv
filename=root/'cache'/'Anteprima_atmosfere.pdf' if draft else a/'Album_render.pdf'
c=Canvas(str(filename),pagesize=(W,H),pageCompression=1);c.setTitle('Casa Margherita | Atlante dei render e delle versioni 3D');c.setAuthor('ARCHAI / Casa Margherita');num=0
ink='#203c32';chalk='#f8f6ee';sage='#5a7263';ochre='#935d41'
def text(x,y,s,font,size,colour=ink):
 c.setFillColor(HexColor(colour));c.setFont(font,size);c.drawString(x,y,s)
def wrap(x,y,s,w,font='Testo',size=13,leading=18,colour=ink):
 words=s.split();line=''
 for word in words:
  if line and pdfmetrics.stringWidth(line+' '+word,font,size)>w:
   text(x,y,line,font,size,colour);y-=leading;line=word
  else:line=(line+' '+word).strip()
 if line:text(x,y,line,font,size,colour);y-=leading
 return y
def img(path,x,y,w,h,cover=False):
 with Image.open(a/path) as im:
  im=im.convert('RGB')
  if cover:im=ImageOps.fit(im,(round(w*1.65),round(h*1.65)),method=Image.Resampling.LANCZOS)
  else:
   scale=min(w/im.width,h/im.height);dw,dh=im.width*scale,im.height*scale;x+=(w-dw)/2;y+=(h-dh)/2;w,h=dw,dh
  im.thumbnail((2000,1650));buf=BytesIO();im.save(buf,format='JPEG',quality=90,optimize=True);buf.seek(0);c.drawImage(ImageReader(buf),x,y,w,h)
def start(code,title,sub):
 global num
 num+=1;c.setFillColor(HexColor(chalk));c.rect(0,0,W,H,fill=1,stroke=0)
 text(38,H-32,'A R C H A I   /   C A S A   M A R G H E R I T A', 'Grassetto',10)
 text(W-300,H-32,'ATLANTE VISIVO     /     '+code,'Grassetto',10,sage)
 c.setStrokeColor(HexColor('#c4c8b9'));c.line(38,H-44,W-38,H-44)
 text(38,H-97,title,'Titolo',38);wrap(40,H-124,sub,W-80,size=14)
 c.setStrokeColor(HexColor('#c4c8b9'));c.line(38,36,W-38,36);text(38,21,'PALAZZO LOMBARDO  /  SAN GREGORIO DI CATANIA     ·     STUDIO PRELIMINARE', 'Grassetto',8,sage);text(W-94,21,f'R02   /   {num:02}','Grassetto',8,sage)
def finish():c.showPage()
for ident in ['P02','P01','P03','P04','P05','GA','GB','G01']:
 v=catalog[ident];concepts=[i for i in v['items'] if i['kind']=='concept']
 for idx,shot in enumerate(concepts):
  start(ident+'   /   ATMOSFERA',shot['name'],v['label']+'  ·  '+v['brief'])
  img(shot['image'],38,69,W-76,H-220,False)
  text(40,51,'Veduta interpretativa elaborata con ImageGen a partire da una fotografia della visita o dell’annuncio. Proporzioni e dettagli si verificano nelle tavole e nei modelli.','Testo',10,sage);finish()
if not draft:
 for ident,v in catalog.items():
  start(ident+'   /   MODELLO',v['label'],v['brief'])
  primary=next(i for i in v['items'] if i['key']=='assonometria')
  img(primary['image'],38,236,W*.48,440);text(40,216,'Spaccato del modello Blender. La visita digitale comprende i filtri per strato e il taglio orizzontale.','Testo',10,sage)
  keys=['sala','giardino','fronte','servizi'] if ident.startswith('P') else ['accesso','archi','banco','quota']
  for j,k in enumerate(keys):
   i=next(i for i in v['items'] if i['key']==k);x=W*.53+(j%2)*W*.22;y=427-(j//2)*223
   img(i['image'],x,y,W*.205,174,False);text(x,y-9,i['name'],'Grassetto',11)
  y=wrap(40,163,'La scena contiene '+str(v['nodes'])+' elementi. Il file GLB comprende arredi e materiali. Il modello IFC4 organizza gli elementi edilizi per ambiente e riporta gli ingombri principali degli arredi.',W*.46,size=13)
  wrap(W*.53,160,'Nel tour si può ruotare a 360° da cinque posizioni, sia di giorno sia di sera. Le volte e gli appoggi sono ipotesi geometriche. Il confronto fra versioni utilizza punti di ripresa coincidenti.',W*.42,size=13)
  finish()
if not draft:
 for subject,ids,heading in [('giardino',['P00','P01','P02','P03','P04','P05'],'Dalla soglia del terrazzo'),('fronte',['P00','P01','P02','P03','P04','P05'],'Dalla stanza sulla piazza'),('archi',['G00','GA','GB','G01'],'Sotto gli archi del garage')]:
  start('CONFRONTO',heading,'La medesima posizione e la medesima direzione dello sguardo rendono leggibili le differenze tra le versioni.')
  cols=3 if len(ids)==6 else 2;slot=(W-76)/cols
  for j,ident in enumerate(ids):
   v=catalog[ident];i=next(e for e in v['items'] if e['key']==subject)
   x=38+(j%cols)*slot;y=449-(j//cols)*287
   img(i['image'],x,y,slot-12,224)
   wrap(x,y-18,v['label'],slot-15,font='Grassetto',size=12)
  finish()
c.save();print(filename.name,num,'pagine.')
