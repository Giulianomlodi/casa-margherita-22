from PIL import Image,ImageDraw
from pathlib import Path
import random,numpy as np,math
p=Path(__file__).resolve().parents[1]/'cache'
for name,color,stones in [('graniglia',(123,90,78),[(187,156,133),(222,203,175),(95,71,62),(170,116,93),(211,177,158)]),('scaglie',(170,151,127),[(205,185,156),(150,125,104),(223,211,189),(118,103,89),(184,156,130)]),('basalto',(83,84,79),[(93,92,84),(70,72,66),(107,104,93)])]:
 rng=random.Random(45);side=768;noise=np.random.default_rng(24).normal(0,3,(side,side,1))
 im=Image.fromarray(np.clip(np.array(color)[None,None,:]+noise,0,255).astype('uint8'));d=ImageDraw.Draw(im)
 for j in range(6800):
  x,y=rng.randrange(side),rng.randrange(side);radius=rng.triangular(.6,8,1.1);N=rng.randint(3,6);phase=rng.random()*6.3
  pts=[(x+math.cos(phase+i*6.28/N)*radius*rng.uniform(.6,1.2),y+math.sin(phase+i*6.28/N)*radius*rng.uniform(.42,1.1)) for i in range(N)];d.polygon(pts,fill=rng.choice(stones))
 for i in (0,384):d.line((i,0,i,768),fill=tuple(max(0,v-26) for v in color),width=1);d.line((0,i,768,i),fill=tuple(max(0,v-26) for v in color),width=1)
 im.save(p/(name+'.jpg'),quality=86)
