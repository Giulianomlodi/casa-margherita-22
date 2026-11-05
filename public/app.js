"use strict";

const form = document.querySelector("#access");
const statusLine = document.querySelector("#status");
const viewer = document.querySelector("#viewer");
const notice = document.querySelector("#notice");
const fileInfo = {
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
      const plain = await decryptResource(name, projectKey);
      resources.set(name, URL.createObjectURL(new Blob([plain], {type})));
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

async function openProject(value) {
  const enter = document.querySelector("#enter");
  enter.disabled = true;
  statusLine.textContent = "Apertura del dossier…";
  try {
    const token = readKey(value);
    const bytes = Uint8Array.from(atob(token.replace(/-/g,"+").replace(/_/g,"/") + "="), c => c.charCodeAt(0));
    projectKey = await crypto.subtle.importKey("raw", bytes, "AES-GCM", false, ["decrypt"]);
    const html = new TextDecoder().decode(await decryptResource("dossier", projectKey));
    viewer.addEventListener("load", () => {
      const frameDoc = viewer.contentDocument;
      for (const button of frameDoc.querySelectorAll("[data-file]")) {
        button.addEventListener("click", () => download(button.dataset.file, button));
      }
      document.querySelector("main").hidden = true;
      document.querySelector("header").hidden = true;
      viewer.hidden = false;
      document.querySelector("#code").value = "";
      statusLine.textContent = "";
    }, {once:true});
    viewer.srcdoc = html;
    // The fragment stays on the device and makes the address reusable from bookmarks.
    history.replaceState(null, "", "#k=" + token);
  } catch (error) {
    statusLine.textContent = error.name === "OperationError" ? "La chiave non apre questo progetto. Ricopia il link ricevuto via email." : (error.message || "Impossibile aprire il dossier.");
  } finally {
    enter.disabled = false;
  }
}

form.addEventListener("submit", event => {
  event.preventDefault();
  openProject(document.querySelector("#code").value);
});
if (location.hash.startsWith("#k=")) openProject(location.hash);
