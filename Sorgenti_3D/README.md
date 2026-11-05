# Sorgenti della ricostruzione 3D

I file di consegna si trovano nella cartella accanto, `Atlante_3D/`. Le scene Blender contengono geometria, arredi, camere e texture incorporate. Per intervenire manualmente si può aprire direttamente il file della variante.

## Ricostruzione parametrica

`scripts/geometry.json` conserva contorni, porte, aperture e sezioni in altezza. L'unità nel ricalco è il pixel della planimetria sorgente a 0,0254 metri per pixel. `scripts/trace.py` può rigenerare la base con Shapely 2.1, leggendo le costanti grafiche di `scripts/planimetria.py`.
`scripts/scene.py` crea la scena da quella base con Blender 5.2 e Cycles. La variabile di ambiente `CM_SCHEME` sceglie P00–P05, G00, GA, GB o G01. Impostare `CM_NATIVE=1` e `CM_BUILD_ONLY=1` per rigenerare GLB, metadati e scena Blender. Per ricalcolare i render impostare `CM_BUILD_ONLY=0`, `CM_NATIVE=0`, `CM_PANO=4096`, `CM_WIDTH=1552`. Il generatore riprende i file mancanti. Spostare i render precedenti prima di ricalcolare una variante cambiata.

```sh
blender -b --factory-startup --python-exit-code 11 -P scripts/scene.py
```

`scripts/cutaways.py` apre le scene native e calcola gli spaccati di presentazione. `python scripts/exchange.py P02` costruisce l'IFC4 della versione scelta usando IfcOpenShell, NumPy e SciPy. I componenti edilizi sono classificati e gli arredi principali hanno ingombri semplificati.

## Consultazione e pubblicazione

`npm install` e `npm run build:viewer` ricostruiscono il visualizzatore Three.js. `python scripts/catalog.py` genera il catalogo, le miniature, le prospettive estratte dai panorami e l'HTML offline, usando OpenCV, Pillow e NumPy. Le immagini d'atmosfera approvate si trovano in `Atlante_3D/atmosfere/`. `python scripts/album.py` impagina il PDF con ReportLab e i caratteri Georgia e Segoe UI installati su Windows.

La libreria locale `cache/archai.blend` contiene le sedici mesh di arredo e vegetazione riutilizzate da ARCHAI. I crediti delle texture e del motore grafico sono in `Atlante_3D/LEGGIMI.txt`. Per cifrare i materiali con la chiave del progetto e aggiornare Netlify, usare il comando di pubblicazione indicato nel README principale.

### Proposte con soppalchi

Per P06–P08 il file `scripts/mezzanines.json` definisce posizione, scala, quota finita, spessore e arredi del piano alto. `scripts/mezzanine.py` li integra nella scena dell’intero appartamento. Per rigenerare SVG e DXF usare `python soppalchi/plates.py` con ezdxf. `python soppalchi/book.py` genera l’impaginato HTML del quaderno per stampa A3 orizzontale.
