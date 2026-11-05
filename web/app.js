"use strict";

const form = document.querySelector("#access");
const statusLine = document.querySelector("#status");
const viewer = document.querySelector("#viewer");
const notice = document.querySelector("#notice");
const fileInfo = {
  album: ["Casa_Margherita_22_Album_render.pdf", "application/pdf"],
  pdf: ["Casa_Margherita_22.pdf", "application/pdf"],
  progetto: ["Casa_Margherita_22_Progetto.zip", "application/zip"],
  originali: ["Casa_Margherita_22_Fonti_originali.zip", "application/zip"]
};
let projectKey;
const resources = new Map();

function readKey(value) {
  const raw = value.trim();
  const fragment = raw.includes("#") ? raw.slice(raw.indexOf("#") + 1) : raw;
  const token = new URLSearchParams(fragment).get("k") || fragment;
  if (!/^[A-Za-z0-9_-]{43}$/.test(token)) throw new Error("Controlla di aver copiato tutto il link ricevuto.");
  return token;
}

async function decryptResource(name, key) {
  const response = await fetch("/archivio/" + name + ".bin");
  if (!response.ok) throw new Error("Download interrotto. Riprova tra poco.");
  const data = new Uint8Array(await response.arrayBuffer());
  return crypto.subtle.decrypt({name:"AES-GCM", iv:data.subarray(0,12)}, key, data.subarray(12));
}

async function download(name, button) {
  button.disabled = true;
  notice.hidden = false;
  notice.textContent = "Preparazione del file…";
  try {
    const [filename, type] = fileInfo[name];
    if (!resources.has(name)) {
      let content;
      if (name === "progetto") {
        const manifest = JSON.parse(new TextDecoder().decode(await decryptResource("progetto-indice", projectKey)));
        if (!Array.isArray(manifest.parts) || manifest.parts.length > 20) throw Error("Indice non valido");
        const pieces = [];
        for (const [i, part] of manifest.parts.entries()) {
          if (!/^progetto(?:-parte-\d+)?$/.test(part)) throw Error("Parte non valida");
          notice.textContent = "Preparazione del progetto " + (i+1) + "/" + manifest.parts.length + "…";
          pieces.push(await decryptResource(part, projectKey));
        }
        content = new Blob(pieces, {type});
        if(content.size !== manifest.size) throw Error("Download incompleto");
      } else {
        content = new Blob([await decryptResource(name, projectKey)], {type});
      }
      resources.set(name, URL.createObjectURL(content));
    }
    const anchor = document.createElement("a");
    anchor.href = resources.get(name);
    anchor.download = filename;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    notice.hidden = true;
  } catch {
    notice.textContent = "Download interrotto. Premi di nuovo il pulsante per riprovare.";
  } finally {
    button.disabled = false;
  }
}

let dossierHtml = "";
let atlasHtml = "";
let accessToken = "";
let savedScroll = 0;
let route = 0;

window.margheritaAsset = async function(relative) {
  if (!projectKey || !/^(?:render|atmosfere|panorami|miniature|modelli)\/[A-Za-z0-9_-]+\.(?:webp|ifc|glb|blend)$/.test(relative)) throw new Error("Percorso non disponibile");
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode("3d/"+relative)));
  const key = Array.from(digest, b=>b.toString(16).padStart(2,"0")).join("").slice(0,32);
  return decryptResource("v3/"+key, projectKey);
};

function mount(html, onLoad) {
  const currentRoute=++route;
  viewer.onload=()=>{
    if(currentRoute!==route)return;
    document.querySelector("main").hidden=true;
    document.querySelector("header").hidden=true;
    viewer.hidden=false;
    onLoad();
  };
  viewer.srcdoc=html;
}

function showDossier() {
  history.replaceState(null, "", "#k="+accessToken);
  mount(dossierHtml, ()=>{
    const doc=viewer.contentDocument;
    for(const button of doc.querySelectorAll("[data-file]")) {
      button.addEventListener("click",()=>download(button.dataset.file,button));
    }
    for(const link of doc.querySelectorAll("[data-atlante]")){
      link.addEventListener("click",e=>{e.preventDefault();savedScroll=viewer.contentWindow.scrollY;showAtlas(link.dataset.atlante);});
    }
    for(const link of doc.querySelectorAll("[data-album]")){
      link.addEventListener("click",e=>{e.preventDefault();download("album",link);});
    }
    viewer.contentWindow.scrollTo({top:savedScroll,behavior:"instant"});
  });
}
window.margheritaBack=showDossier;

async function showAtlas(id) {
  try {
    notice.hidden=false;notice.textContent="Apertura dell’atlante 3D…";
    if(!atlasHtml)atlasHtml=new TextDecoder().decode(await decryptResource("atlante",projectKey));
    window.margheritaVersion=/^(?:P0[0-5]|G00|G01|GA|GB)$/.test(id)?id:"P02";
    history.replaceState(null, "", "#k="+accessToken+"&view=3d&versione="+window.margheritaVersion);
    mount(atlasHtml,()=>{notice.hidden=true;});
  } catch {notice.textContent="Impossibile aprire l’atlante. Riprova.";}
}
async function openProject(value) {
  const enter=document.querySelector("#enter");enter.disabled=true;statusLine.textContent="Apertura del progetto…";
  try {
    const token=readKey(value);
    const requested=new URLSearchParams(value.includes("#")?value.split("#").pop():"");
    const bytes=Uint8Array.from(atob(token.replace(/-/g,"+").replace(/_/g,"/")+"="),c=>c.charCodeAt(0));
    projectKey=await crypto.subtle.importKey("raw",bytes,"AES-GCM",false,["decrypt"]);
    dossierHtml=new TextDecoder().decode(await decryptResource("dossier",projectKey));accessToken=token;
    document.querySelector("#code").value="";statusLine.textContent="";
    if(requested.get("view")==="3d")await showAtlas(requested.get("versione"));
    else showDossier();
  } catch(error){statusLine.textContent=error.name==="OperationError"?"La chiave non apre questo progetto. Ricopia il link ricevuto via email.":(error.message||"Impossibile aprire il dossier.");}
  finally {enter.disabled=false;}
}

form.addEventListener("submit", event => {
  event.preventDefault();
  openProject(document.querySelector("#code").value);
});
if (location.hash.startsWith("#k=")) openProject(location.hash);
