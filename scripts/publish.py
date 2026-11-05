from pathlib import Path
from io import BytesIO
import base64
import hashlib
import json
import mimetypes
import os
import re
import shutil
import zipfile
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ARCHIVE = PUBLIC / "archivio"
KEYFILE = ROOT / ".accesso" / "chiave"
PUBLIC.mkdir(exist_ok=True)
ARCHIVE.mkdir(exist_ok=True)
KEYFILE.parent.mkdir(mode=0o700, exist_ok=True)
if not KEYFILE.exists():
    if any(ARCHIVE.glob("*.bin")):
        raise RuntimeError("Recuperare la chiave della release prima di rigenerare i materiali.")
    with KEYFILE.open("xb") as out:
        out.write(AESGCM.generate_key(bit_length=256))
    KEYFILE.chmod(0o600)
key = AESGCM(KEYFILE.read_bytes())

def seal(name, plain):
    # Reuse an existing ciphertext only when the same key decrypts it to the same bytes.
    target = ARCHIVE / (name + ".bin")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        old = target.read_bytes()
        try:
            if hashlib.sha256(key.decrypt(old[:12], old[12:], None)).digest() == hashlib.sha256(plain).digest():
                return
        except (ValueError, InvalidTag):
            pass
    nonce = os.urandom(12)
    temp = target.with_suffix(".tmp")
    temp.write_bytes(nonce + key.encrypt(nonce, plain, None))
    temp.replace(target)

def pack(entries):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as archive:
        for path, name in sorted(entries, key=lambda entry: entry[1]):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return output.getvalue()

def embed_image(match):
    filename = match.group(1)
    encoded = base64.b64encode((ROOT / filename).read_bytes()).decode("ascii")
    mime = mimetypes.guess_type(filename)[0]
    return 'src="data:' + mime + ';base64,' + encoded + '"'

html = (ROOT / "Apri_il_progetto.html").read_text(encoding="utf-8")
html = re.sub(r'src="((?:tavole|materiali)/[^"]+)"', embed_image, html)
html = html.replace("if(this.value) location.hash=this.value", "document.getElementById(this.value)?.scrollIntoView()")
buttons = '<button data-file="pdf">Scarica PDF</button><button data-file="progetto">Progetto e CAD</button><button data-file="originali">Fonti originali</button>'
html, count = re.subn(r'<a href="Casa_Margherita_22.pdf">[^<]+</a>', buttons, html)
if count != 1:
    raise RuntimeError("Collegamento PDF del dossier da verificare")
html = html.replace("</style>", ".tools [data-file]{display:inline-block}.tools{flex-wrap:wrap}@media screen and (max-width:760px){.tools [data-file]{font-size:12px;padding:6px}.sheet{scroll-margin-top:105px}}@media print{.tools{display:none!important}}</style>")
seal("dossier", html.encode("utf-8"))
seal("pdf", (ROOT / "Casa_Margherita_22.pdf").read_bytes())
atlas = ROOT / "Atlante_3D"
seal("atlante", (atlas / "index.html").read_bytes())
seal("album", (atlas / "Album_render.pdf").read_bytes())
seal("soppalchi", (atlas / "Case_e_soppalchi.pdf").read_bytes())
for asset in sorted(atlas.rglob("*")):
    if asset.is_file() and asset.suffix.lower() in {".webp", ".ifc", ".glb", ".blend"}:
        relative_name = asset.relative_to(atlas).as_posix()
        key_name = hashlib.sha256(("3d/"+relative_name).encode("utf-8")).hexdigest()[:32]
        seal("v3/" + key_name, asset.read_bytes())
files = [ROOT / s for s in ["Apri_il_progetto.html", "Casa_Margherita_22.pdf", "LEGGIMI.txt"]]
for folder in ["CAD", "tavole", "materiali", "Atlante_3D"]:
    files.extend(p for p in (ROOT / folder).rglob("*") if p.is_file())
complete = pack([(p, "Casa_Margherita_22/" + p.relative_to(ROOT).as_posix()) for p in files])
# Each new Git blob stays well below the GitHub per-file cap.
part_size = 40 * 1024 * 1024
if len(complete) <= 80 * 1024 * 1024:
    part_names = ["progetto"]
    seal("progetto", complete)
else:
    part_names = []
    for offset in range(0, len(complete), part_size):
        part_name = "progetto-parte-" + str(len(part_names)+1)
        seal(part_name, complete[offset:offset + part_size])
        part_names.append(part_name)
seal("progetto-indice", json.dumps({"parts": part_names, "size": len(complete)}).encode("utf-8"))
videos = [ROOT.parent / ("WhatsApp Video 2026-11-05 at " + t + ".mp4") for t in ("13.55.29", "13.55.42")]
sources = [ROOT / "fonti_private" / f for f in ("1-NCV364.pdf", "2-Photo-2.jpg")]
if all(p.is_file() for p in videos + sources):
    seal("originali", pack([(p, "Fonti/" + p.name) for p in sources + videos]))
elif not (ARCHIVE / "originali.bin").exists():
    raise RuntimeError("Servono i quattro originali o il pacchetto già cifrato")
for name in ["index.html","app.js","_headers","robots.txt"]:
    shutil.copyfile(ROOT / "web" / name, PUBLIC / name)
print("Pubblicazione preparata:", len(list(ARCHIVE.glob("*.bin"))), "risorse cifrate.")
