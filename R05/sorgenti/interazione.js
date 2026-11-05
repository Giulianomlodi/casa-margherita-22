import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const $ = s => document.querySelector(s);
const all = s => [...document.querySelectorAll(s)];
const query = new URLSearchParams(location.search);
let version = query.get('variante') === 'L' ? 'L' : 'F';
let focus = 'alte', sheet = 'L1', roof = false, text, scene, camera, controls, renderer, actual, loading, ticket=0, frame=0;
const models=new Map();
function redraw() {
  if (!frame) frame=requestAnimationFrame(()=>{frame=0;if(renderer)renderer.render(scene,camera)});
}
function resize(){
  if(!renderer)return;
  const box=$('#webgl'), w=box.clientWidth, h=box.clientHeight;
  renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();redraw();
}
function start(){
  if(renderer)return;
  const container=$('#webgl');
  renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(2,devicePixelRatio));renderer.toneMapping=THREE.ACESFilmicToneMapping;
  scene=new THREE.Scene();scene.background=new THREE.Color(0xe8e4d8);
  const pm=new THREE.PMREMGenerator(renderer), env=new RoomEnvironment();
  scene.environment=pm.fromScene(env,.05).texture;pm.dispose();env.dispose();
  scene.add(new THREE.HemisphereLight(0xfff8ec,0x898578,1.55));
  const sun=new THREE.DirectionalLight(0xfff5df,2.2);sun.position.set(-5,14,9);scene.add(sun);
  camera=new THREE.PerspectiveCamera(39,1,.04,200);controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=false;controls.maxPolarAngle=Math.PI*.515;controls.addEventListener('change',redraw);
  container.append(renderer.domElement);new ResizeObserver(resize).observe(container);resize();
}
function applyFocus(){
  const bounds=new THREE.Box3();
  if(!actual)return;
  actual.updateMatrixWorld(true);
  actual.traverse(o=>{
    if(!o.isMesh)return;
    let source=o; while(source.parent && !source.userData.strato && !source.userData.camera_alta)source=source.parent;
    const p=source.userData,k=p.camera_alta,part=p.elemento_R05;
    let visible=true;
    if(focus!=='tutte')visible=Boolean(k)&&(focus==='alte'||k===focus)&&part!=='arredo basso';
    if(p.strato==='Coperture')visible=roof&&focus==='tutte';
    if(p.strato==='Contesto')visible=false;
    if(!roof&&focus==='tutte'&&!k&&o.name.startsWith('Murature_DOCFA')&&!/^Murature_DOCFA$/.test(o.name))visible=false;
    if(!roof&&k&&part==='pareti alte'&&['W','S'].includes(p.lato))visible=false;
    if(!roof&&k&&part==='porta')visible=false;
    o.visible=visible;
    if(visible){o.geometry.computeBoundingBox();bounds.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));}
  });
  if(!bounds.isEmpty()){
    const center=bounds.getCenter(new THREE.Vector3()),sz=bounds.getSize(new THREE.Vector3());
    const radius=bounds.getBoundingSphere(new THREE.Sphere()).radius;
    const vfov=THREE.MathUtils.degToRad(camera.fov), aspect=Math.min(1,camera.aspect);
    const dist=radius/Math.sin(Math.atan(Math.tan(vfov*.5)*aspect))*1.02;
    const dir=new THREE.Vector3(-.57,focus==='tutte'||focus==='alte'?1.25:.97,.55).normalize();
    controls.target.copy(center);camera.position.copy(center).addScaledVector(dir,dist);controls.minDistance=.45;controls.maxDistance=Math.max(40,sz.length()*4);controls.update();
  }
  all('[data-focus]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.focus===focus)));
  $('#roof').textContent=roof?'Seziona la casa':'Mostra la copertura';redraw();
}
async function loadModel(){
  if(!renderer)return;
  const tag=++ticket,key=version;
  $('#load').hidden=false;$('#load').textContent='Apertura del modello…';
  try{
    if(!models.has(key))models.set(key,new GLTFLoader().loadAsync(key+'.glb').then(g=>g.scene));
    const next=await models.get(key);if(tag!==ticket)return;
    if(actual)scene.remove(actual);actual=next;scene.add(actual);applyFocus();$('#load').hidden=true;
  }catch(e){models.delete(key);if(tag===ticket)$('#load').textContent='Il modello non si è aperto. Puoi scaricare il GLB o consultare le viste sezionate.';}
}
function sheets(){
  const name=version+'-'+sheet;
  $('#sheet').src=name+'.svg';$('#sheetLink').href=name+'.svg';$('#dxf').href=name+'.dxf';$('#svg').href=name+'.svg';
  all('[data-sheet]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sheet===sheet)));
}
function select(v){
  version=v;
  for(const a of all('[data-v]'))a.setAttribute('aria-current',String(a.dataset.v===v));
  all('[data-version]').forEach(el=>el.hidden=el.dataset.version!==v);
  for(const ext of ['blend','glb','ifc'])$('#'+ext).href=v+'.'+ext;
  $('#fullRender').href=v+'-insieme.webp';
  $('#inside1').href=v+'-piazza-interno.webp';$('#inside2').href=v+'-retro-interno.webp';
  if(text){$('#prog').textContent=text.programma[v];$('#obstacles').textContent=text.passaggi[v];}
  sheets();history.replaceState(null,'','?variante='+v+location.hash);loadModel();
}
all('[data-v]').forEach(a=>a.onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();select(a.dataset.v)});
all('[data-sheet]').forEach(b=>b.onclick=()=>{sheet=b.dataset.sheet;sheets()});
all('[data-focus]').forEach(b=>b.onclick=()=>{focus=b.dataset.focus;roof=false;applyFocus()});
$('#roof').onclick=()=>{roof=!roof;focus='tutte';applyFocus()};
const zoom=$('#zoom');all('[data-zoom]').forEach(b=>b.onclick=()=>{zoom.querySelector('img').src=b.dataset.zoom;zoom.showModal()});
$('#close').onclick=()=>zoom.close();zoom.onclick=e=>{if(e.target===zoom)zoom.close()};
fetch('testi.json').then(r=>r.json()).then(d=>{text=d;$('#prog').textContent=text.programma[version];$('#obstacles').textContent=text.passaggi[version]});
select(version);
new IntersectionObserver((entries,watcher)=>{
  if(!entries.some(e=>e.isIntersecting))return;watcher.disconnect();
  try{start();loadModel()}catch(e){$('#load').textContent='WebGL non disponibile. Le viste e i disegni sono consultabili qui sopra e qui sotto.'}
},{rootMargin:'150px'}).observe($('#webgl'));
