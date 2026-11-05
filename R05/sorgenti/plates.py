from pathlib import Path
import math,html,json,base64,ezdxf
from design import DATA,LEVEL,DEPTH,S,ORIGIN,NAMES,walk,calc
d=Path(__file__).resolve().parent;o=d.parent/'due-camere';audit=json.loads((d.parents[1]/'R04/decisioni/audit.json').read_text(encoding='utf8'))
src=d.parents[1]/'materiali/plan11.png';bg=base64.b64encode(src.read_bytes()).decode()
def it(v,n=2):return f'{v:.{n}f}'.replace('.',',')
def rect(b,fill,stroke='#32493e',lw=.013,dash=''):
 x,y,X,Y=b;return f'<rect x="{x}" y="{y}" width="{X-x}" height="{Y-y}" fill="{fill}" stroke="{stroke}" stroke-width="{lw}" stroke-dasharray="{dash}"/>'
def line(x,y,X,Y,c='#344c41',w=.018,dash=''):return f'<path d="M{x} {y}L{X} {Y}" fill="none" stroke="{c}" stroke-width="{w}" stroke-dasharray="{dash}"/>'
def txt(x,y,s,size=.13,anchor='middle',color='#2e473a'):return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(s)}</text>'
def planpart(v,k,upper):
 r=DATA[v][k];x,y,X,Y=r['deck'];bx,by=r['bed'];out=[]
 out.append(rect(r['deck'],'#e2dfcb' if upper else ('#f2eadc' if v=='L' else '#f6f3e9'),'#7e644c',.038,'' if upper else '.11 .045'))
 if upper:
  out.extend([rect([x+.08,y+.08,X-.08,Y-.08],'none','#958975',.014),rect([bx-.45,by-1,bx+.45,by+1],'#f1ecde','#5c695a',.020),rect([bx-.37,by-.90,bx+.37,by-.59],'#fffdf5'),rect([bx-.42,by-.45,bx+.42,by+.92],'#9aaf98'),rect(r['ward'],'#bd9572'),txt((x+X)/2,Y-.21,'Piazza' if k=='piazza' else 'Retro',.18)])
  side,a,b=r['door']
  if side=='N':out+=[rect([a,y-.018,b,y+.10],'#f8f4e8','none'),line(a,y,b,y,'#a15e37',.045,'.05 .045')]
  else:out+=[rect([x-.018,a,x+.1,b],'#f8f4e8','none'),line(x,a,x,b,'#a15e37',.045,'.05 .045')]
 else:
  if v=='F' and k=='piazza':
   out.extend([rect([.86,1.30,2.44,3.30],'#e5d8c5'),rect([.92,1.38,2.38,1.66],'#fff9ed'),txt(1.65,2.44,'MATRIMONIALE',.12)])
  else:out.append(txt((x+X)/2,(y+Y)/2,'STIVAGGIO' if v=='L' else 'SOGGIORNO',.18))
 out.append(rect(r['land'],'#d1b892'))
 if 'turn' in r:out.append(rect(r['turn'],'#e5d2b4'))
 for f in r['flights']:
  dr,fx,fy,w,n,g=f;steps=list(walk(f))
  for b in steps:out.append(rect(b,'#e9d6bc','#715d43',.02))
  first,last=steps[0],steps[-1];m=lambda b:((b[0]+b[2])/2,(b[1]+b[3])/2)
  x0,y0=m(first);x1,y1=m(last);out.append(line(x0,y0,x1,y1,'#934927',.032));ang=math.atan2(y1-y0,x1-x0)
  for a in (-.58,.58):out.append(line(x1,y1,x1-.13*math.cos(ang+a),y1-.13*math.sin(ang+a),'#934927',.034))
 return ''.join(out)
def polyline(ms,pts,layer):ms.add_lwpolyline(pts,close=True,dxfattribs={'layer':layer})
def draw(v,upper):
 label='L1' if upper else 'L0';svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 690"><rect width="850" height="690" fill="#faf8ee"/>',txt(30,38,('Piano delle camere' if upper else 'Piano di ingresso')+' · '+v,27,'start')]
 svg+=['<g transform="translate(12,44) scale(.61)"><image href="data:image/png;base64,'+bg+'" width="590" height="1105" opacity=".66"/>']
 doc=ezdxf.new('R2010');doc.units=6;ms=doc.modelspace()
 for ly,num in [('VANI_DOCFA',8),('IMPALCATI',3),('RAMPE',32),('SBARCHI',5),('ARREDI',4),('TESTI',7)]:doc.layers.add(ly,color=num)
 for room,pts in audit['polygons'].items():
  if room!='garage':polyline(ms,[((x-49)*S,(1055-y)*S) for x,y in pts],'VANI_DOCFA')
 for k,r in DATA[v].items():
  a,b=ORIGIN[k];svg+=['<g transform="translate('+f'{a} {b}'+') scale('+str(1/S)+')">'+planpart(v,k,upper)+'</g>']
  def cad(bb,ly):
   x,y,X,Y=bb;polyline(ms,[((a-49)*S+u,(1055-b)*S-t) for u,t in [(x,y),(X,y),(X,Y),(x,Y)]],ly)
  cad(r['deck'],'IMPALCATI');cad(r['land'],'SBARCHI')
  if 'turn' in r:cad(r['turn'],'SBARCHI')
  for f in r['flights']:
   for q in walk(f):cad(q,'RAMPE')
  if not upper and v=='F' and k=='piazza':cad([.86,1.30,2.44,3.30],'ARREDI')
  if upper:
   x,y=r['bed'];cad([x-.45,y-1,x+.45,y+1],'ARREDI');cad(r['ward'],'ARREDI')
  ms.add_text(NAMES[k]+' '+it(calc(r)['net'])+' m2',dxfattribs={'insert':((a-49)*S+r['deck'][0],(1055-b)*S-r['deck'][1]-.2),'height':.12,'layer':'TESTI'})
 svg+=['</g>']
 for k,top in [('retro',91),('piazza',396)]:
  r=DATA[v][k];svg += [txt(349,top,NAMES[k]+' · '+it(calc(r)['net'])+' m² netti',20,'start'),'<g transform="translate(375,'+str(top+16)+') scale(43)">'+planpart(v,k,upper)+'</g>']
  svg.append(txt(633,top+55,'Piano a +'+it(LEVEL[v])+' m',14,'start'));svg.append(txt(633,top+79,'Letto 90 × 200 cm',14,'start'))
  svg.append(txt(633,top+103,'Scala '+str(sum(f[4] for f in r['flights']))+' alzate',14,'start'))
 svg.append(txt(349,669,'Ingrandimenti alla medesima scala · sbarco esterno alle camere.',14,'start'))
 svg+=['</svg>'];(o/f'{v}-{label}.svg').write_text(''.join(svg),encoding='utf8')
 doc.saveas(o/f'{v}-{label}.dxf')
def section(v):
 z=LEVEL[v];t=DEPTH[v];scale=63;x0=82;y0=428;ref=4.2;target=z+2.70;fy=lambda z:y0-scale*z;fx=lambda x:x0+scale*x
 svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 540"><rect width="850" height="540" fill="#faf8ee"/>',txt(28,38,'Sezione lungo la scala del retro · '+v,26,'start')]
 sub='Locale sotto e camera sopra' if v=='F' else 'Base chiusa e camera sopra';svg.append(txt(28,65,sub+' · riferimento a 4,20 m, profilo locale da rilevare.',16,'start'))
 # Developed section through the straight flight; deck drawn in projection next to the landing.
 f=DATA[v]['retro']['flights'][0];n=f[4];g=f[5];rise=z/n;run=(n-1)*g;land=.88
 doc=ezdxf.new('R2010');doc.units=6;ms=doc.modelspace();pts=[(0,0)]
 for i in range(n-1):pts.extend([(i*g,(i+1)*rise),((i+1)*g,(i+1)*rise)])
 pts.extend([(run,z),(run+land+2.98,z)])
 ms.add_lwpolyline(pts);ms.add_line((-.35,ref),(run+land+3.3,ref));ms.add_line((run+land,z-t),(run+land+2.98,z-t));ms.add_text('4.20 m riferimento medio',dxfattribs={'insert':(0,ref+.05),'height':.115})
 svg.append(line(54,y0,790,y0,w=2))
 for p,q in zip(pts,pts[1:]):svg.append(line(fx(p[0]),fy(p[1]),fx(q[0]),fy(q[1]),w=2.3))
 right=run+land+2.98;svg.append(rect([fx(run+land),fy(z),fx(right),fy(z-t)],'#b69265','#634b36',1))
 if v=='L':svg.append(rect([fx(run+land),fy(z-t),fx(right),fy(0)],'#d7bf9e','#796a58',1))
 svg.append(line(55,fy(ref),787,fy(ref),'#98543b',1.8,'8 4'));svg.append(txt(783,fy(ref)-7,'4,20 m · riferimento medio',15,'end','#89472b'))
 svg.append(line(65,fy(target),786,fy(target),'#477359',1.6,'3 4'));svg.append(txt(783,fy(target)-7,it(target)+' m · obiettivo con 2,70 m sopra',15,'end'))
 svg.append(txt(787,fy(z)+1,'Quota +'+it(z)+' m',15,'end'));svg.append(txt(784,(fy(z)+fy(ref))/2+8,it(ref-z)+' m sopra',18,'end'))
 svg.append(txt(785,(fy(0)+fy(z-t))/2,it(z-t)+' m sotto',17,'end'))
 # Standing figure at top is a gauge, crosses the dashed reference in F.
 xx=fx(run+land+.68);svg+= [line(xx,fy(z+.08),xx,fy(z+1.45),'#795344',3),'<circle cx="'+str(xx)+'" cy="'+str(fy(z+1.59))+'" r="7.2" fill="none" stroke="#795344" stroke-width="2"/>',line(xx,fy(z+.75),xx-9,fy(z),'#795344',2),line(xx,fy(z+.75),xx+8,fy(z),'#795344',2)]
 svg+=[txt(32,480,str(n)+' alzate × '+it(rise*100,1)+' cm · '+str(n-1)+' pedate × '+it(g*100,1)+' cm · sbarco esterno alla camera.',16,'start'),txt(32,510,'Impalcato proiettato accanto allo sbarco; la figura è un riferimento alto 1,70 m.',15,'start'),'</svg>'];(o/f'{v}-sezione.svg').write_text(''.join(svg),encoding='utf8');doc.saveas(o/f'{v}-sezione.dxf')
for v in DATA:draw(v,True);draw(v,False);section(v)
