"""Add the three two-level briefs to the shared survey shell. Plan coordinates in source pixels."""
from math import ceil,dist
from mathutils import Vector
import bpy

def build_mezzanine(ctx,spec):
    group,block,cube,bar,asset,point=[ctx[k] for k in ('group','block','cube','bar','asset','point')]
    zone,deck,flight=spec['short'],spec['deck'],spec['flight']
    n=ctx['SCHEME'];scale=ctx['S'];x,y,w,h=deck
    sx,top,direction,risers,going,width=flight;right=sx+width/scale
    level,depth=spec['level'],spec['depth'];run=(risers-1)*going;foot=top-direction*run/scale
    # Remove just the borrowed daylight furniture and old high cupboards. The rest of the dwelling is retained.
    for ob in list(ctx['objects']):
        room,layer=ob['ambiente'],ob['strato']
        obsolete=layer=='Quota alta' or (room in ('Sala sul giardino','Atelier') and layer in ('Arredi','Finiture') and not ob.name.startswith(('Cornice','Battiscopa')))
        obsolete|=room=='Sala sul giardino' and layer=='Serramenti' and n!='P06'
        if layer=='Illuminazione':
            px=215+ob.location.x/scale;py=550-ob.location.y/scale
            obsolete|=150<px<342 and 245<py<622
        if obsolete:
            ctx['objects'].remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    for ob in list(ctx['scene'].objects):
        if ob.type=='LIGHT' and ob.name.startswith('Lampada serale') and 150<215+ob.location.x/scale<342 and 245<550-ob.location.y/scale<622:bpy.data.objects.remove(ob,do_unlink=True)
    group('Zona giorno','Arredi');ctx['table'](*spec['dining'])
    if spec['couch']:
        X,Y,rot=spec['couch'];asset('sofa','Divano al piano principale',X,Y,angle=rot,s=(.65,.70,.85))
    if spec['office']:
        for xx in [218,260]:
            block('Scrivania atelier',xx,256,39,22,.74,.045,'Castagno',.018)
            for X in [xx+2,xx+37]:
                for Y in [258,276]:cube('Gamba scrivania',X,Y,.37,.038,.038,.74,'Ferro')
            asset('dining_chair','Seduta atelier',xx+19,289,s=(.86,)*3)
        block('Archivio al piano principale',320,333,13,82,.08,1.92,'Salvia',.018)
    if n!='P06':
        group('Zona giorno','Serramenti');sy=325 if n=='P07' else 411
        ctx['opening']('Quinta restaurata parziale',(185,sy),(242,sy),.01,3.58,3,walk=True,mat='Castagno',transom=True)
    group(zone,'Quota alta');block('Impalcato soppalco',x,y,w,h,level-depth,depth-.038,'Castagno',.008)
    block('Pavimento soppalco',x,y,w,h,level-.038,.038,'Castagno',.005)
    if n=='P06':
        block('Corpo contenitore chiuso',x+.7,y+.7,w-1.4,h-1.4,.02,level-depth-.02,'Lino')
        for j in range(4):
            block('Cassetto estraibile laterale',x-.4,y+1+j*(h-2)/4,1.1,(h-2)/4-1,.12,.84,'Castagno',.009)
            cube('Presa incassata',x-.52,y+11+j*(h-2)/4,.77,.022,.17,.026,'Ferro')
    else:
        for X in [x+2,x+w-2]:
            for Y in [y+2,y+h-2]:cube('Montante di studio',X,Y,(level-depth)/2,.075,.075,level-depth,'Ferro',.006)
    def inclined(label,a,b,side,thick,mat):
        start,end=Vector(point(*a)),Vector(point(*b));v=end-start
        ob=ctx['instance'](label,ctx['cube_shape'](side,thick,v.length,mat,.003),tuple((start+end)/2))
        ob.rotation_euler=v.to_track_quat('Z','Y').to_euler()
    rise=level/risers
    for j in range(risers-1):
        y0=foot+direction*j*going/scale
        block('Gradino nuova scala',sx,min(y0,y0+direction*going/scale),width/scale,going/scale,(j+1)*rise-.045,.045,'Castagno',.008)
        block('Alzata scala',sx,y0-.4,width/scale,.8,j*rise,rise-.01,'Lino')
    for X in [sx+.75,right-.75]:
        inclined('Cosciale inclinato',(X,foot,.04),(X,top,level-.04),.045,.095,'Ferro')
        inclined('Corrimano scala',(X,foot,1.0+rise),(X,top,level+1.05),.040,.040,'Bronzo')
        count=ceil(run/.11)
        for j in range(count+1):
            f=j/count;z=rise+f*(level-rise);cube('Montante parapetto scala',X,foot+(top-foot)*f,z+.50,.018,.018,1.0,'Ferro')
    def guard(a,b):
        d=dist(a,b)*scale
        if d<.04:return
        bar('Corrimano soppalco',a,b,.047,.045,level+1.05,'Bronzo')
        bar('Traverso soppalco',a,b,.025,.025,level+.11,'Ferro')
        steps=ceil(d/.11)
        for j in range(steps+1):
            f=j/steps;cube('Montante parapetto soppalco',a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,level+.53,.018,.018,1.02,'Ferro')
    other=y+h if direction==1 else y
    for a,b in [((x,top),(sx,top)),((right,top),(x+w,top)),((x,y),(x,y+h)),((x+w,y),(x+w,y+h)),((x,other),(x+w,other))]:guard(a,b)
    if spec['upperSeat']:
        X,Y=spec['upperSeat'];asset('lounge_chair','Poltrona sul salotto rialzato',X,Y,level,angle=30,s=(.86,)*3)
        asset('lounge_chair','Seconda seduta rialzata',244,563,level,angle=-26,s=(.84,)*3)
        asset('side_table','Tavolino sulla pedana',266,577,level,s=(.72,)*3)
    if spec['office']:
        for j in range(3):block('Cassettiera bassa per modelli',x+3,y+3+j*19,14,17,level+.06,.58,'Salvia',.012)
    if spec['upperDesk']:
        block('Piano studio ipotetico',168,504,52,25,level+.74,.045,'Castagno',.016)
        for X in [170,218]:
            for Y in [506,526]:cube('Gamba tavolo studio',X,Y,level+.37,.04,.04,.74,'Ferro')
        asset('dining_chair','Seduta dello studio ipotetico',198,539,level,s=(.90,)*3)
    group('Zona giorno','Illuminazione');ctx['lamp'](222,295,2.86)
    if n!='P08':ctx['lamp'](188,573,2.94)
    else:
        cube('Plafoniera sottoballatoio',227,543,level-depth-.035,.55,.18,.04,'Vetro opalino')
        ctx['light']('Luce pranzo','POINT',227,543,level-depth-.1,65,(1,.78,.56),.20)
