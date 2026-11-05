"use strict";

const params = new URLSearchParams(location.hash.slice(1));
const historicalKey = params.get("k");
const originalsButton = document.querySelector("#originali");
const storageKey = "casa-margherita-originali";
let sourceKey;
if (historicalKey && /^[A-Za-z0-9_-]{43}$/.test(historicalKey)) {
  sourceKey = historicalKey;
  try { sessionStorage.setItem(storageKey, sourceKey); } catch {}
} else {
  try { sourceKey = sessionStorage.getItem(storageKey); } catch {}
}
if (params.has("k") || params.get("view") === "3d") {
  history.replaceState(null, "", location.pathname + location.search);
  const version = params.get("versione") || "P02";
  if (params.get("view") === "3d" && /^(P0[0-8]|G00|G01|GA|GB)$/.test(version)) {
    location.replace("/Atlante_3D/?versione=" + version);
  }
}

if (sourceKey) {
  originalsButton.hidden = false;
  originalsButton.addEventListener("click", async () => {
    originalsButton.disabled = true;
    originalsButton.textContent = "Preparazione originali…";
    try {
      const bytes = Uint8Array.from(atob(sourceKey.replace(/-/g, "+").replace(/_/g, "/") + "="), c => c.charCodeAt(0));
      const key = await crypto.subtle.importKey("raw", bytes, "AES-GCM", false, ["decrypt"]);
      const response = await fetch("/archivio/originali.bin");
      if (!response.ok) throw Error("Download interrotto");
      const sealed = new Uint8Array(await response.arrayBuffer());
      const data = await crypto.subtle.decrypt({name:"AES-GCM", iv:sealed.subarray(0,12)}, key, sealed.subarray(12));
      const url = URL.createObjectURL(new Blob([data], {type:"application/zip"}));
      const link = document.createElement("a");
      link.href = url;
      link.download = "Casa_Margherita_22_Fonti_originali.zip";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      originalsButton.textContent = "Fonti originali";
    } catch {
      originalsButton.textContent = "Ricontrolla il link privato e riprova";
    } finally {
      originalsButton.disabled = false;
    }
  });
}
