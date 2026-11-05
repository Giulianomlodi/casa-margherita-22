import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $ = selector => document.querySelector(selector);
const all = selector => Array.from(document.querySelectorAll(selector));
const catalog = JSON.parse($('#catalog').textContent);
const versions = Object.keys(catalog);
const initial = new URLSearchParams(location.search).get('versione') || (window.parent!==window ? window.parent.margheritaVersion : null);
const state = {id: versions.includes(initial) ? initial : 'P02', mode:'gallery', subject:'concept', other:'P00', time:'giorno'};
let showSource=false,dirty=true,lastPano='';
let revision=0, engine, activeModel, activeId, panorama, camera, controls, modelScene, panoScene, panoCamera;
let clip, sourceMaterials=[], yaw=0, pitch=0, fov=70, drag, clickStart;
const hidden = new Set(['Coperture','Contesto']);
const promiseCache = new Map();
const urls = new Map();
const openedFiles = new Map();
const online = window.parent !== window && typeof window.parent.margheritaAsset === 'function';
const localFolder = location.protocol === 'file:';
const stage = $('#stage');
const escapeHTML = s=>String(s).replace(/[&<>"]/g,k=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[k]));
function options(select,items,value) {
  select.replaceChildren(...items.map(([id,name])=>new Option(name,id)));
  select.value=value;
}
function loading(message) {$('#loading').textContent=message||'';$('#loading').hidden=!message;}
function sourceFile(path) {
  if(online) return window.parent.margheritaAsset(path);
  if(localFolder) {
    const file=openedFiles.get(path);
    if(!file){$('#pickFolder').hidden=false;throw new Error('Per aprire il 3D offline, seleziona la cartella Atlante_3D in fondo alla pagina.');}
    return file.arrayBuffer();
  }
  return fetch(path).then(r=>{if(!r.ok)throw Error('File non disponibile. Riprova.');return r.arrayBuffer();});
}
async function assetURL(path) {
  if(!online && (!localFolder || !openedFiles.size))return path;
  if(urls.has(path))return urls.get(path);
  if(!promiseCache.has(path)){
    const mime=path.endsWith('.webp')?'image/webp':path.endsWith('.glb')?'model/gltf-binary':'application/octet-stream';
    promiseCache.set(path,Promise.resolve().then(()=>sourceFile(path)).then(bytes=>{
      const url=URL.createObjectURL(new Blob([bytes],{type:mime}));urls.set(path,url);return url;
    }).finally(()=>promiseCache.delete(path)));
  }
  return promiseCache.get(path);
}
function geometryEntry(id,key){return catalog[id].items.find(v=>v.key===key);}
function matchingCamera(a,b){if(!a.camera || !b.camera)return !a.camera && !b.camera;return a.camera.every((v,i)=>Math.abs(v-b.camera[i])<.0001);}
function galleryItems(){
 const v=catalog[state.id];
 if(state.mode==='compare')return v.items.filter(i=>i.kind==='render' && geometryEntry(state.other,i.key)?.kind==='render' && matchingCamera(i,geometryEntry(state.other,i.key)));
 if(state.mode==='pano')return v.items.filter(i=>i.pano);
 return v.items;
}
function current(){return geometryEntry(state.id,state.subject);}
function resolveImage(item){return state.time==='sera'&&item.night?item.night:item.image;}
function imageName(id){return catalog[id].label;}
async function setPicture(element,path,tag) {
 const url=await assetURL(path);if(tag!==revision)return;
 element.src=url;await element.decode();if(tag!==revision)return;
}
function configurePanel(){
 const version=catalog[state.id],model=state.mode==='model',compare=state.mode==='compare',pano=state.mode==='pano';
 $('#versionName').textContent=version.label;$('#brief').textContent=version.brief;$('#stats').textContent=version.nodes+' elementi nella scena · unità in metri.';
 $('#scheme').value=state.id;
 for(const b of all('[data-mode]'))b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode));
 $('#modelControls').hidden=!model;$('#subjects').hidden=model;$('#mapBox').hidden=!pano;if(pano)drawPlan();$('#compareBox').hidden=!compare;
 const alternatives=versions.filter(id=>id!==state.id && id[0]===state.id[0]);
 if(!alternatives.includes(state.other))state.other=alternatives[0];
 options($('#other'),alternatives.map(id=>[id,catalog[id].label]),state.other);
 const mezz=version.mezzanine;
 $('#mezzPanel').hidden=!mezz;$('#isoMezz').hidden=!mezz||!model;
 if(mezz){
  const fmt=v=>v.toLocaleString('it-IT',{minimumFractionDigits:2,maximumFractionDigits:2});
  $('#mezzMetrics').textContent='Piano a +'+fmt(mezz.level)+' m. Con H locale di 4,20 m rimarrebbero '+fmt(4.2-mezz.level)+' m sopra.';
 }
 const entries=galleryItems();
 if(!entries.some(i=>i.key===state.subject))state.subject=entries[0]?.key;
 options($('#subject'),entries.map(i=>[i.key,i.name]),state.subject);
 const item=current();
 if(!item?.night || (compare && !geometryEntry(state.other,state.subject)?.night))state.time='giorno';
 $('#times').hidden=model||!item?.night;
 for(const b of all('[data-time]'))b.setAttribute('aria-pressed',String(b.dataset.time===state.time));
 $('#strip').hidden=model;$('#prev').hidden=model;$('#next').hidden=model;
 $('#saveImage').hidden=model||pano||compare;
 const paired=state.mode==='gallery' && !!item?.reference && showSource;
 $('#sourcePhoto').textContent=state.id==='P08'?'Modello di partenza':'Foto di partenza';$('#sourcePhoto').hidden=state.mode!=='gallery'||!item?.reference;$('#sourcePhoto').setAttribute('aria-pressed',String(paired));
 $('#plates').hidden=model||pano;$('#second').hidden=!(compare||paired);$('#plates').classList.toggle('compare',compare||paired);
 if(engine)engine.domElement.hidden=!model&&!pano;
 $('#title').textContent=model?'Modello esplorabile':(item?.name||'');
 $('#caption').textContent=model?'Trascina per ruotare, avvicina con lo zoom e seleziona un elemento per identificarlo.':pano?'Trascina per guardarti intorno. Usa la rotella o due dita per lo zoom.':compare?'Stessa posizione di ripresa nelle due versioni.':'';
 if(!model && !pano && !compare)$('#caption').textContent=item?.kind==='plan'?'Tavola di progetto in scala grafica. Apri il quaderno PDF per quote e programma completo.':item?.kind==='concept'?'Interpretazione d’atmosfera da fotografia o spaccato di riferimento.':item?.kind==='photo'?'Fotografia o fotogramma originale utilizzato per la ricostruzione.':'Vista calcolata dalla geometria del modello.';
 $('#badge').textContent=compare?imageName(state.id):item?.kind==='plan'?'Tavola quotata':item?.kind==='concept'?'Atmosfera':item?.kind==='photo'?'Riferimento originale':state.time==='sera'?'Dal modello · sera':'Dal modello · giorno';
 $('#badge2').textContent=paired?(state.id==='P08'?'Modello di partenza':'Foto di partenza'):imageName(state.other);
 return entries;
}
function drawPlan(){
 const map=$('#planMap'),data=catalog[state.id],garage=state.id[0]==='G',span=garage?365:1000;
 const scale=210/span;
 const xy=(x,y)=>[15+((garage?475:1060)-y)*scale,7+(x-(garage?65:49))*scale];
 const poly=data.plan.map(poly=>'<polygon points="'+poly.map(p=>xy(...p).join(',')).join(' ')+'" fill="#faf9f0" stroke="#697e6b" stroke-width="1"/>').join('');
 const pins=data.items.filter(i=>i.pano).map((i,n)=>{const [a,b]=i.camera;const [cx,cy]=xy(a/.0254+215,(garage?300:550)-b/.0254);return '<g data-key="'+i.key+'" role="button" tabindex="0" aria-label="'+escapeHTML(i.name)+'"><circle cx="'+cx+'" cy="'+cy+'" r="7" fill="'+(state.subject===i.key?'#ac5c38':'#2f624e')+'"/><text x="'+cx+'" y="'+(cy+3)+'" text-anchor="middle" fill="white" font-size="9">'+(n+1)+'</text></g>';}).join('');
 map.setAttribute('viewBox',garage?'0 0 235 194':'0 0 235 102');map.innerHTML=poly+pins;
 map.querySelectorAll('[data-key]').forEach(el=>{const go=()=>{state.subject=el.dataset.key;refresh();};el.onclick=go;el.onkeydown=e=>{if(e.key==='Enter')go();};});
}

function renderStrip(entries,tag){
 const strip=$('#strip');strip.replaceChildren();
 if(state.mode==='model')return;
 for(const item of entries){
  const btn=document.createElement('button');btn.className='thumb';btn.setAttribute('aria-pressed',String(item.key===state.subject));
  btn.onclick=()=>{state.subject=item.key;refresh();};
  const img=new Image();img.alt='';img.loading='lazy';
  const label=document.createElement('span');label.textContent=item.name;
  btn.append(img,label);strip.append(btn);
  assetURL(item.thumb).then(url=>{if(tag===revision)img.src=url;}).catch(()=>{});
 }
}
function initEngine(){
 if(engine)return;
 engine=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});
 engine.shadowMap.enabled=true;engine.shadowMap.autoUpdate=false;engine.shadowMap.type=THREE.PCFSoftShadowMap;engine.setPixelRatio(Math.min(devicePixelRatio,1.75));engine.localClippingEnabled=true;engine.toneMapping=THREE.ACESFilmicToneMapping;engine.outputColorSpace=THREE.SRGBColorSpace;
 stage.prepend(engine.domElement);
 camera=new THREE.PerspectiveCamera(39,1,.035,300);modelScene=new THREE.Scene();modelScene.background=new THREE.Color(0xe8e9df);
 const env=new RoomEnvironment(),pmrem=new THREE.PMREMGenerator(engine);
 modelScene.environment=pmrem.fromScene(env,.04).texture;env.dispose();pmrem.dispose();modelScene.environmentIntensity=.80;
 modelScene.add(new THREE.HemisphereLight(0xfff1d9,0xc8c6b9,.96));
 const sun=new THREE.DirectionalLight(0xffe3b7,1.8);sun.position.set(-9,18,10);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-17,right:17,top:17,bottom:-17,near:.1,far:60});sun.shadow.bias=-.00022;sun.shadow.normalBias=.018;modelScene.add(sun);
 controls=new OrbitControls(camera,engine.domElement);controls.enableDamping=true;controls.minDistance=.3;controls.maxDistance=75;controls.maxPolarAngle=Math.PI*.51;controls.addEventListener('change',()=>{dirty=true;});
 clip=new THREE.Plane(new THREE.Vector3(0,-1,0),1.55);
 panoScene=new THREE.Scene();panoCamera=new THREE.PerspectiveCamera(70,1,.01,3);panoCamera.rotation.order='YXZ';
 engine.domElement.addEventListener('pointerdown',e=>{clickStart=[e.clientX,e.clientY];if(state.mode==='pano'){drag={x:e.clientX,y:e.clientY,yaw,pitch};engine.domElement.setPointerCapture(e.pointerId);}});
 engine.domElement.addEventListener('pointermove',e=>{if(drag&&state.mode==='pano'){yaw=drag.yaw-(e.clientX-drag.x)*.004;pitch=THREE.MathUtils.clamp(drag.pitch+(e.clientY-drag.y)*.004,-1.48,1.48);}});
 engine.domElement.addEventListener('pointerup',e=>{drag=null;if(state.mode==='model' && clickStart && Math.hypot(clickStart[0]-e.clientX,clickStart[1]-e.clientY)<5)identify(e);clickStart=null;});
 engine.domElement.addEventListener('pointercancel',()=>{drag=null;clickStart=null;});
 engine.domElement.addEventListener('wheel',e=>{if(state.mode==='pano'){e.preventDefault();fov=THREE.MathUtils.clamp(fov+Math.sign(e.deltaY)*4,36,99);panoCamera.fov=fov;panoCamera.updateProjectionMatrix();}},{passive:false});
 let pinch;
 engine.domElement.addEventListener('touchstart',e=>{if(state.mode==='pano'&&e.touches.length===2){const [a,b]=e.touches;pinch={distance:Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY),fov};drag=null;}},{passive:true});
 engine.domElement.addEventListener('touchmove',e=>{if(state.mode==='pano'&&pinch&&e.touches.length===2){const [a,b]=e.touches;fov=THREE.MathUtils.clamp(pinch.fov*pinch.distance/Math.max(1,Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY)),36,99);panoCamera.fov=fov;panoCamera.updateProjectionMatrix();e.preventDefault();}},{passive:false});
 engine.domElement.addEventListener('touchend',()=>{pinch=null;},{passive:true});
 new ResizeObserver(resize).observe(stage);resize();
 engine.setAnimationLoop(()=>{if(document.hidden||engine.domElement.hidden)return;
  if(state.mode==='model'){controls.update();if(dirty){engine.render(modelScene,camera);dirty=false;}}
  if(state.mode==='pano'){const view=yaw+'|'+pitch+'|'+fov;if(dirty||view!==lastPano){panoCamera.rotation.set(pitch,yaw,0,'YXZ');engine.render(panoScene,panoCamera);dirty=false;lastPano=view;}}
 });
}
function resize(){
 dirty=true;if(!engine)return;const w=stage.clientWidth,h=stage.clientHeight;engine.setSize(w,h,false);
 for(const c of [camera,panoCamera]){c.aspect=w/h;c.updateProjectionMatrix();}
}
function identify(e){
 if(!activeModel)return;const r=stage.getBoundingClientRect(),ray=new THREE.Raycaster();
 ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);
 const hit=ray.intersectObjects(activeModel.children,true).find(h=>h.object.isMesh&&h.object.visible&&!hidden.has(h.object.userData.layer)&&(!h.object.userData.cuttable||h.point.y<=clip.constant+.01));
 if(hit){$('#picked').textContent=hit.object.userData.display+' · '+hit.object.userData.room;}
}
function resetView(top=false){
 if(!camera||!activeModel)return;
 const box=new THREE.Box3();activeModel.updateMatrixWorld(true);
 activeModel.traverse(obj=>{if(!obj.isMesh||obj.userData.layer==='Contesto')return;obj.geometry.computeBoundingBox();box.union(obj.geometry.boundingBox.clone().applyMatrix4(obj.matrixWorld));});
 const centre=box.getCenter(new THREE.Vector3()),direction=new THREE.Vector3(...(top?[.0001,1,.0001]:[1.15,1.22,.49])).normalize();
 const right=new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),direction).normalize(),up=new THREE.Vector3().crossVectors(direction,right);
 const tan=Math.tan(THREE.MathUtils.degToRad(camera.fov/2));let distance=1;
 for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
   const v=new THREE.Vector3(x,y,z).sub(centre),depth=v.dot(direction);
   distance=Math.max(distance,depth+1.04*Math.abs(v.dot(right))/(tan*camera.aspect),depth+1.05*Math.abs(v.dot(up))/tan);
 }
 controls.target.copy(centre);camera.position.copy(centre).addScaledVector(direction,distance);controls.update();
}
function changeStyle(){
 if(!activeModel)return;dirty=true;engine.shadowMap.needsUpdate=true;
 const updated=new Set();const style=$('#appearance').value;clip.constant=Number($('#cut').value);$('#cutValue').value=(clip.constant>=4.9?'intere':clip.constant.toLocaleString('it-IT',{minimumFractionDigits:2})+' m');
 modelScene.background.set(style==='evening'?0x323a40:0xe8e9df);modelScene.environmentIntensity=style==='evening'?.38:.86;
 engine.toneMappingExposure=style==='evening'?.74:1.03;
 for(const entry of sourceMaterials){
  const {object,mats,colors}=entry;object.visible=!hidden.has(object.userData.layer);
  mats.forEach((m,i)=>{if(updated.has(m))return;updated.add(m);m.wireframe=style==='line';if(m.color)m.color.copy(style==='clay'?new THREE.Color(0xe2d6bd):colors[i]);m.map=style==='clay'?null:entry.maps[i];m.clippingPlanes=object.userData.cuttable?[clip]:[];m.needsUpdate=true;});
 }
}
function dropModel(){
 if(!activeModel)return;modelScene.remove(activeModel);
 const shapes=new Set(),mats=new Set(),textures=new Set();
 activeModel.traverse(o=>{if(!o.isMesh)return;shapes.add(o.geometry);for(const m of (Array.isArray(o.material)?o.material:[o.material])){mats.add(m);for(const val of Object.values(m))if(val?.isTexture)textures.add(val);}});
 for(const s of shapes)s.dispose();for(const m of mats)m.dispose();for(const t of textures)t.dispose();sourceMaterials=[];activeModel=null;
}
async function showModel(tag){
 initEngine();controls.enabled=true;engine.domElement.hidden=false;
 if(activeId!==state.id||!activeModel){
  const id=state.id,bytes=await sourceFile('modelli/'+id+'.glb');if(tag!==revision)return;
  const {scene:loaded}=await new GLTFLoader().parseAsync(new Uint8Array(bytes).slice().buffer,'');if(tag!==revision)return;
  dropModel();activeModel=loaded;activeId=id;modelScene.add(loaded);
  const byLayer=new Map();
  loaded.traverse(o=>{
   if(!o.isMesh)return;
   let obj=o;while(obj.parent&&!obj.userData.strato)obj=obj.parent;
   const layer=obj.userData.strato||'Struttura';o.userData.layer=layer;o.userData.room=obj.userData.ambiente||'';o.userData.display=obj.name.replace(/[._]?[0-9]{3}$/,'').replaceAll('_',' ');
   o.userData.cuttable=['Struttura','Serramenti','Finiture','Coperture'].includes(layer);
   const raw=Array.isArray(o.material)?o.material:[o.material];const mats=raw.map(m=>{
    const key=m.uuid+layer;if(!byLayer.has(key)){const c=m.clone();c.side=THREE.DoubleSide;c.clipShadows=true;byLayer.set(key,c);}return byLayer.get(key);
   });
   o.material=Array.isArray(o.material)?mats:mats[0];o.receiveShadow=true;o.castShadow=mats.every(m=>!m.transparent && m.opacity>.97);sourceMaterials.push({object:o,mats,colors:mats.map(m=>m.color?.clone()||new THREE.Color()),maps:mats.map(m=>m.map)});
  });resetView();$('#picked').textContent='';
 }
 const holder=$('#layers');holder.replaceChildren();
 for(const layer of catalog[state.id].layers){
  const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=!hidden.has(layer);
  check.onchange=()=>{check.checked?hidden.delete(layer):hidden.add(layer);changeStyle();};label.append(check,document.createTextNode(layer));holder.append(label);
 }
 options($('#cameraStop'),[['','Vista complessiva'],...catalog[state.id].items.filter(i=>i.camera).map(i=>[i.key,i.name])],'');
 changeStyle();
}
async function showPano(item,tag){
 initEngine();controls.enabled=false;engine.domElement.hidden=false;
 const path=state.time==='sera'?item.panoNight:item.pano;
 const url=await assetURL(path);if(tag!==revision)return;
 const tex=await new THREE.TextureLoader().loadAsync(url);if(tag!==revision){tex.dispose();return;}
 if(panorama){panorama.material.map.dispose();panorama.geometry.dispose();panorama.material.dispose();panoScene.remove(panorama);}
 tex.colorSpace=THREE.SRGBColorSpace;
 // Standard sphere seam points toward -X. Rotate so the camera initially sees the frame centre.
 const geom=new THREE.SphereGeometry(1,80,48);geom.scale(-1,1,1);
 panorama=new THREE.Mesh(geom,new THREE.MeshBasicMaterial({map:tex,toneMapped:false}));panorama.rotation.y=-Math.PI/2;panoScene.add(panorama);
 dirty=true;yaw=0;pitch=0;panoCamera.fov=fov;panoCamera.updateProjectionMatrix();
}
async function refresh(){
 const tag=++revision,entries=configurePanel();
 renderStrip(entries,tag);loading(state.mode==='model'?'Apertura del modello…':'Caricamento…');
 try{
  if(state.mode==='model')await showModel(tag);
  else if(state.mode==='pano')await showPano(current(),tag);
  else{
   const a=current();$('#picture').alt=a.name;
   const tasks=[setPicture($('#picture'),resolveImage(a),tag)];
   if(state.mode==='compare'){const b=geometryEntry(state.other,state.subject);$('#picture2').alt=b.name;tasks.push(setPicture($('#picture2'),resolveImage(b),tag));}
   if(state.mode==='gallery' && showSource && a.reference){$('#picture2').alt='Fotografia o fotogramma originale';tasks.push(setPicture($('#picture2'),a.reference,tag));}
   await Promise.all(tasks);
  }
  if(tag===revision)loading('');
 }catch(err){if(tag===revision)loading(err.message?.includes('WebGL')?'WebGL non disponibile. Puoi usare la galleria e scaricare il modello.':err.message||'Impossibile caricare la vista.');}
}
function step(delta){const list=galleryItems();if(!list.length)return;state.subject=list[(list.findIndex(x=>x.key===state.subject)+delta+list.length)%list.length].key;refresh();}
async function download(path,button){
 try{button.disabled=true;const url=await assetURL(path);const a=document.createElement('a');a.href=url;a.download=path.split('/').pop();document.body.append(a);a.click();a.remove();}
 catch(err){loading(err.message);}finally{button.disabled=false;}
}
options($('#scheme'),versions.map(id=>[id,catalog[id].label]),state.id);
$('#scheme').onchange=e=>{hidden.clear();hidden.add('Contesto');hidden.add('Coperture');state.id=e.target.value;if(!geometryEntry(state.id,state.subject))state.subject=catalog[state.id].items[0].key;refresh();};
$('#subject').onchange=e=>{state.subject=e.target.value;refresh();};$('#other').onchange=e=>{state.other=e.target.value;refresh();};
for(const b of all('[data-mode]'))b.onclick=()=>{state.mode=b.dataset.mode;refresh();};
for(const b of all('[data-time]'))b.onclick=()=>{state.time=b.dataset.time;refresh();};
$('#prev').onclick=()=>step(-1);$('#next').onclick=()=>step(1);$('#cut').oninput=changeStyle;$('#appearance').onchange=changeStyle;
$('#cameraStop').onchange=e=>{
 const item=geometryEntry(state.id,e.target.value);
 if(!item?.camera){resetView();return;}
 const [x,y,z,X,Y,Z]=item.camera;camera.position.set(x,z,-y);controls.target.set(X,Z,-Y);
 hidden.delete('Coperture');hidden.delete('Contesto');$('#cut').value=5;
 for(const label of $('#layers').querySelectorAll('label'))label.querySelector('input').checked=!hidden.has(label.textContent);
 controls.update();changeStyle();
};
function overall(top=false){hidden.clear();$('#cameraStop').value='';hidden.add('Coperture');hidden.add('Contesto');$('#cut').value=1.55;for(const label of $('#layers').querySelectorAll('label'))label.querySelector('input').checked=!hidden.has(label.textContent);resetView(top);changeStyle();}
$('#reset').onclick=()=>overall();$('#top').onclick=()=>overall(true);$('#spin').onclick=e=>{controls.autoRotate=!controls.autoRotate;e.target.setAttribute('aria-pressed',String(controls.autoRotate));};
$('#getBlend').onclick=e=>download('modelli/'+state.id+'.blend',e.target);
$('#getGLB').onclick=e=>download('modelli/'+state.id+'.glb',e.target);$('#getIFC').onclick=e=>download('modelli/'+state.id+'.ifc',e.target);
for(const [id,key] of [['see0','L0'],['see1','L1'],['seeSection','AA']])$('#'+id).onclick=()=>{state.mode='gallery';state.subject=key;showSource=false;refresh();};
$('#mezzBook').onclick=e=>{if(online)window.parent.margheritaMezzBook(e.currentTarget);else window.open('Case_e_soppalchi.pdf','_blank','noopener');};
$('#isoMezz').onclick=()=>{hidden.clear();for(const layer of catalog[state.id].layers)if(layer!=='Quota alta')hidden.add(layer);$('#cut').value=5;for(const label of $('#layers').querySelectorAll('label'))label.querySelector('input').checked=!hidden.has(label.textContent);changeStyle();};
$('#sourcePhoto').onclick=()=>{showSource=!showSource;refresh();};
$('#saveImage').onclick=e=>download(resolveImage(current()),e.target);
$('#expand').onclick=async()=>{try{document.fullscreenElement?await document.exitFullscreen():await stage.requestFullscreen();}catch{stage.classList.toggle('maximized');}};
$('#back').onclick=()=>{if(online)window.parent.margheritaBack();else location.href='../Apri_il_progetto.html';};
$('#pickFolder').onclick=()=>$('#directory').click();
$('#directory').onchange=e=>{openedFiles.clear();for(const file of e.target.files)openedFiles.set(file.webkitRelativePath.split('/').slice(1).join('/'),file);$('#pickFolder').hidden=true;refresh();};
document.addEventListener('keydown',e=>{if(['SELECT','INPUT'].includes(e.target.tagName)||state.mode==='model')return;if(e.key==='ArrowRight')step(1);if(e.key==='ArrowLeft')step(-1);});
refresh();
