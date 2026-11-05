"""Build the public site from the project deliverables and the web assets."""
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
RELEASE = "https://github.com/Giulianomlodi/casa-margherita-22/releases/download/r03-pubblica/Casa_Margherita_22_Progetto.zip"
ASSETS = {
    "CAD": {".dxf"},
    "tavole": {".svg"},
    "materiali": {".jpg", ".png"},
    "Atlante_3D": {".html", ".pdf", ".json", ".webp", ".blend", ".glb", ".ifc", ".txt"},
}


def copy_site(staging):
    for directory, extensions in ASSETS.items():
        for source in (ROOT / directory).rglob("*"):
            if not source.is_file() or source.is_symlink() or source.suffix.lower() not in extensions:
                continue
            relative = source.relative_to(ROOT)
            if any(part.startswith(".") for part in relative.parts):
                continue
            dest = staging / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
    shutil.copyfile(ROOT / "Casa_Margherita_22.pdf", staging / "Casa_Margherita_22.pdf")
    for name in ("app.js", "_headers", "robots.txt"):
        shutil.copyfile(ROOT / "web" / name, staging / name)
    # Historical invitation links retain access to their AES-GCM protected attachments.
    (staging / "archivio").mkdir()
    shutil.copyfile(ROOT / "public/archivio/originali.bin", staging / "archivio/originali.bin")

    html = (ROOT / "Apri_il_progetto.html").read_text(encoding="utf-8")
    button = '<a href="Casa_Margherita_22.pdf">Apri il PDF</a>'
    assert html.count(button) == 1
    html = html.replace(button, button + '<a href="' + RELEASE + '">Progetto e CAD ↓</a>'
                        '<button id="originali" hidden>Fonti originali</button>')
    head = '<meta name="description" content="Casa Margherita a Palazzo Lombardo. Tavole, proposte di ristrutturazione, modelli 3D, soppalchi e garage a San Gregorio di Catania.">'
    html = html.replace("<title>", head + '<meta name="referrer" content="no-referrer"><title>', 1)
    html = html.replace("</style>", ".tools{flex-wrap:wrap}.tools [hidden]{display:none!important}@media screen and (max-width:760px){.tools{position:static}}</style>", 1)
    html = html.replace("</body>", '<script src="/app.js"></script></body>')
    for filename in ("index.html", "Apri_il_progetto.html"):
        (staging / filename).write_text(html, encoding="utf-8")


def main():
    # Build into a fresh directory so previously generated assets cannot leak into a release.
    with tempfile.TemporaryDirectory(prefix=".site-", dir=ROOT) as folder:
        path = Path(folder)
        staging = path / "site"
        staging.mkdir()
        copy_site(staging)
        if OUT.is_symlink():
            raise RuntimeError("La cartella dist deve essere una directory locale.")
        if OUT.exists():
            OUT.rename(path / "previous")
        staging.rename(OUT)
    print("Sito pubblico preparato in dist.")


if __name__ == "__main__":
    main()
