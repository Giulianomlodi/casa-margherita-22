from pathlib import Path
import cv2,numpy as np,json,base64,html
from shapely.geometry import Polygon,box,LineString
from shapely.geometry.polygon import orient
from PIL import Image
from shapely import affinity
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'decisioni';OUT.mkdir(exist_ok=True)
SOURCE=ROOT.parents[1]/'materiali'
GEOM=json.loads((ROOT.parents[1]/'Sorgenti_3D/scripts/geometry.json').read_text())
S=(595.5156/72*.0254*200)/1654
SY=(842.507/72*.0254*200)/2340
assert abs(S-SY)<1e-6
def traced(page,seed):
 clip=cv2.imread(str(SOURCE/f'plan{page}.png'),0)
 full_path=SOURCE/f'map{page}-0.png'
 raw=cv2.imread(str(full_path),0) if full_path.exists() else None
 if raw is not None:
  score=cv2.minMaxLoc(cv2.matchTemplate(raw,clip,cv2.TM_CCOEFF_NORMED))
  assert score[1]>.9999 and score[3]==(520,735)
 binary=(clip>190).astype('uint8')
 _,labels,_,_=cv2.connectedComponentsWithStats(binary,connectivity=4)
 mask=(labels==labels[seed[1],seed[0]]).astype('uint8')
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 curves,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 c=max(curves,key=cv2.contourArea)
 g=Polygon(cv2.approxPolyDP(c,1.15,True).reshape(-1,2)).buffer(1,join_style=2)
 return g
def metres(g):return g.area*S*SY
spec=[('wc','Bagno sul retro',(100,125),'Un solo servizio documentato.'),('terr','Terrazzo',(230,130),'Superficie aperta al netto del WC. Chiusura da verificare.'),('k','Cucina',(110,300),'Vano irregolare: la parte a ridosso della scala si stringe.'),('liv','Salone in sequenza',(250,290),'La quinta vetrata compare nelle foto. La sua posizione esatta non è quotata.'),('entry','Ingresso',(220,710),'Distribuisce zona giorno e fronte.'),('rip','Ripostiglio centrale',(270,700),'Nessuna nuova camera o superficie abitabile attribuita.'),('big','Camera rettangolare sulla piazza',(190,870),'Portafinestra sul balcone. Qui è collocata la matrimoniale nelle tre proposte.'),('small','Ripostiglio a cuneo',(360,910),'In pianta è RIP. La larghezza cambia lungo il vano. Destinato a guardaroba.'),('balcony','Balcone sulla piazza',(230,1040),'Esterno distinto dal terrazzo e dal netto interno.'),('garage','Garage, subalterno 10',(250,300),'Area interna con il pilastro centrale sottratto. Accesso da Vico Piazza.')]
polys={};rows=[];pal=['#729d9b','#759276','#bd9468','#bd805d','#ada387','#beb59f','#788f93','#986f65','#92a798','#94979c']
def it(x,n=1):return f'{x:.{n}f}'.replace('.',',')
for key,name,seed,note in spec:
 p=traced(13 if key=='garage' else 11,seed)
 if key=='garage':p=p.difference(box(177,244,201,266))
 polys[key]=p
 old=Polygon(GEOM['garageInner'] if key=='garage' else GEOM['balcony'] if key=='balcony' else GEOM['rooms'][key])
 b=p.bounds;w=(b[2]-b[0])*S;h=(b[3]-b[1])*SY
 lo,hi=[metres(p.buffer(q,join_style=2)) for q in (-2,2)]
 rows.append(dict(id=key,name=name,area=it(metres(p))+' m²',span=it(w,2)+' × '+it(h,2)+' m · inviluppo',note=note,value=round(metres(p),3),old=round(metres(old),3),range=[round(lo,2),round(hi,2)]))
inside=['k','liv','big','wc','entry','rip','small'];total=sum(metres(polys[k]) for k in inside)
units=[dict(label='Interni · abitazione',doc='112 m² utili¹',draw=it(total)+' m²',note='¹ 81 principali + 4 bagno + 27 accessori. Scala ed esterni esclusi dalla somma grafica.'),dict(label='Camere, cucina e salone',doc='81 m² · 3 vani',draw=it(sum(metres(polys[k]) for k in ['k','liv','big']))+' m²',note='L’attribuzione dei vani è un confronto con il modello 1NB.'),dict(label='Bagno',doc='4 m²',draw=rows[0]['area'],note='Il secondo bagno di alcune vecchie varianti era una proposta.'),dict(label='Ingresso e due ripostigli',doc='27 m²',draw=it(sum(metres(polys[k]) for k in ['entry','rip','small']))+' m²',note='Il vano triangolare è compreso negli accessori.'),dict(label='Terrazzo + balcone',doc='25 m² lordi aggregati',draw=it(metres(polys['terr'])+metres(polys['balcony']))+' m² grafici',note='Terrazzo e balcone sono distinti nella tabella dei vani. Annunci: terrazzo 12 e 20 m² circa.'),dict(label='Garage · unità separata',doc='52 m² utili / 66 lordi',draw=rows[-1]['area'],note='Pilastro e rientranze detratti; sagoma del retrobottega esclusa.'),dict(label='Abitazione lorda',doc='159 m² · gruppo A',draw='perimetro non equiparato',note='165 m² pubblicizzati dall’agenzia. Criteri diversi dal netto interno.'),dict(label='Altezza di riferimento',doc='casa 4,20 m · box 4,35 m',draw='nessuna sezione quotata',note='Gli annunci indicano oltre 4 m. Misurare imposta, chiave e ogni sbarco.')]
sources=[('Scheda RE/MAX · MLS 32311140-23','https://domus-nova.remax.it/vendita-appartamento/san-gregorio-di-catania/centro-32311140-23','165 m² di offerta; terrazzo circa 12 m²; garage venduto separatamente, 66 m². Foto F01–F15.'),('Casa.it · 54713813','https://www.casa.it/immobili/54713813/','15 foto; stessa agenzia e descrizione. Volte oltre 4 m; nessuna quota per singolo vano.'),('Idealista · 36796296','https://www.idealista.it/immobile/36796296/','Stessa unità. La foto di copertina porta una segnalazione di modifica IA; esclusa come prova metrica.'),('TrovaCasa · rif. 2347','https://www.trovacasa.it/annunci/ct-tc-59944-73068047','Replica della medesima inserzione. I dati ripetuti hanno un solo emittente.'),('RE/MAX · MLS 32311140-14','https://www.remax.it/trova/immobile/Casa-Indipendente-In-Vendita-San-Gregorio-Di-Catania_32311140-14','Vendita storica dell’intero palazzo. Casa circa 170 m², terrazzo 20, garage 70, bottega distinta.'),('Idealista · palazzo intero, 36 foto','https://www.idealista.it/immobile/35016491/','Vecchio lotto con negozio. L’inserzione segnala un’immagine modificata con IA; 340 m² comprendono più unità.'),('Casa.it · palazzo intero, 30 foto','https://www.casa.it/immobili/53443694/','Serie storica indicizzata di 30 foto; accesso integrale non verificato.'),('Immobiliare.it · rif. 127165429','https://www.immobiliare.it/annunci/127165429/','Scheda storica del lotto da 340 m². Il pozzo è descritto dall’agenzia, da localizzare in visita.')]
findings=['Il vano a cuneo misura circa '+rows[7]['area']+' e al collo nord la larghezza è circa 0,55 m. A metà vano è circa 1,9 m. In tutte le proposte attive ospita contenimento.','Le carte distinguono 112 m² utili dichiarati, 159 m² lordi e 25 m² esterni aggregati. Il dato commerciale di 165 m² non dimensiona gli arredi.','La scala nominale ricostruita su entrambe le pagine è circa 2,54 cm per pixel. La doppia misura raster/poligoni serve a controllare il disegno, non l’esattezza del rilievo originario.','La casa ha un solo bagno documentato. La quota di 4,20 m è riferita all’unità; le quote delle volte vano per vano restano aperte.','I due filmati forniti riscontrano la quinta, il restringimento e gli archi del garage. Nessun altro video pubblico con misure e identità verificabili è stato individuato.']
def pts(g):return [[round(x,2),round(y,2)] for x,y in list(g.exterior.coords)[:-1]]
data=dict(scale=S,scaleY=SY,units=units,rooms=rows,findings=findings,sources=sources,polygons={k:pts(v) for k,v in polys.items()},net=round(total,3))
(OUT/'audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def overlay(garage=False):
 s=13 if garage else 11; img=base64.b64encode((SOURCE/f'plan{s}.png').read_bytes()).decode(); layer=[]
 for i,(k,name,_,_) in enumerate(spec):
  if (k=='garage')!=garage:continue
  p=polys[k];coords=' '.join(f'{x:.1f},{y:.1f}' for x,y in p.exterior.coords)
  layer.append(f'<polygon points="{coords}" fill="{pal[i]}" fill-opacity=".32" stroke="{pal[i]}" stroke-width="2"><title>{html.escape(name)} · {rows[i]["area"]}</title></polygon>')
 if garage:layer.append('<rect x="177" y="244" width="24" height="22" fill="white" stroke="#343434"/>')
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{("40 75 370 420" if garage else "36 80 447 987")}"><title>Confronto con la carta originale in scala 1:200</title><image href="data:image/png;base64,{img}" width="590" height="1105"/>'+''.join(layer)+'</svg>'
for key,g in [('riscontro',False),('garage',True)]:(OUT/(key+'.svg')).write_text(overlay(g),encoding='utf8')
print('Scala',S,SY,'netto',total,[(r['id'],r['area']) for r in rows])
