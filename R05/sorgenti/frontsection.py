from design import *
from plates import txt,line,rect,it
import ezdxf
out=Path(__file__).resolve().parents[1]/'due-camere'
for v in DATA:
 z=LEVEL[v];r=DATA[v]['piazza'];n=sum(f[4] for f in r['flights']);step=z/n;ptr=0.;h=0.;pts=[(0,0)];mark=None
 for i,f in enumerate(r['flights']):
  for j in range(f[4]-1):
   h+=step;pts.append((ptr,h));ptr+=f[5];pts.append((ptr,h))
  h+=step;pts.append((ptr,h))
  if i<len(r['flights'])-1:mark=(ptr,h);ptr+=.90;pts.append((ptr,h))
  else:ptr+=.90 if v=='F' else .85;pts.append((ptr,h))
 end=ptr+2.15;pts.append((end,z));scale=68;xx=lambda x:64+x*scale;yy=lambda h:426-h*scale
 svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 535"><rect width="850" height="535" fill="#faf8ee"/>',txt(30,38,'Sezione sviluppata della scala sul fronte · '+v,26,'start'),txt(30,66,'Sviluppo lungo le rampe; parte del piano camera in proiezione.',16,'start'),line(41,426,800,426,w=2)]
 doc=ezdxf.new('R2010');doc.units=6;m=doc.modelspace();m.add_lwpolyline(pts);m.add_line((-.30,4.2),(end+.5,4.2));m.add_line((ptr,z-DEPTH[v]),(end,z-DEPTH[v]))
 for a,b in zip(pts,pts[1:]):svg.append(line(xx(a[0]),yy(a[1]),xx(b[0]),yy(b[1]),w=2.3))
 svg.append(rect([xx(ptr),yy(z),xx(end),yy(z-DEPTH[v])],'#bb9974',lw=1.3))
 if v=='L':svg.append(rect([xx(ptr),yy(z-DEPTH[v]),xx(end),yy(0)],'#dfc6a6',lw=1))
 for h,label,col in [(4.2,'4,20 m · riferimento medio','#975236'),(z+2.70,it(z+2.70)+' m · obiettivo con 2,70 m sopra','#397052')]:
  svg.extend([line(42,yy(h),805,yy(h),col,1.6,'7 5'),txt(799,yy(h)-7,label,14,'end',col)])
 svg+= [txt(795,yy(z)-5,'Piano camere +'+it(z)+' m',16,'end'),txt(795,(yy(z)+yy(4.2))/2+8,it(4.2-z)+' m sopra',18,'end'),txt(795,(yy(z)+yy(0))/2,it(z-DEPTH[v])+' m sotto',16,'end')]
 if mark:svg.append(txt(xx(mark[0])+.45*scale,yy(mark[1])-10,'Svolta +'+it(mark[1]),14))
 msg='12 + 5 alzate da 17,2 cm · pedate 26,5 cm · rampa 90 cm · ripiano intermedio 90 × 90 cm.' if v=='F' else '6 alzate da 18 cm · 5 pedate da 26 cm · rampa 85 cm · sbarco 85 × 85 cm.'
 svg.extend([txt(30,472,msg,15,'start'),txt(30,501,'Verificare l’accesso dal disimpegno e il passaggio verso il balcone al piano basso.',15,'start'),'</svg>'])
 (out/(v+'-sezione-piazza.svg')).write_text(''.join(svg),encoding='utf8');doc.saveas(out/(v+'-sezione-piazza.dxf'))
