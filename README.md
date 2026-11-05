# Casa Margherita 22

## Revisione R04

[Decisione e confronto tra le case](https://casa-margherita-archai.netlify.app/) · [Quaderno metrico R04](https://casa-margherita-archai.netlify.app/decisioni/Verifica_R04.pdf) · [Visita 3D ricalcolata](https://casa-margherita-archai.netlify.app/decisioni/atlante.html?variante=A) · [Scarica la release R04](https://github.com/Giulianomlodi/casa-margherita-22/releases/tag/r04-verificata)

Cinque proposte senza camera a cuneo, due ricostruzioni di stato, sovrapposizioni catastali, misure dichiarate e ricalcolate, CAD, IFC, Blender e render. Il confronto con altre case e le planimetrie allegate sono salvati nel browser del visitatore. Per i file di questa edizione entrare in `R04/`.

## Archivio R01–R03

Studio preliminare per l’appartamento di Palazzo Lombardo e il garage di Vico Piazza, San Gregorio di Catania.

[Consulta il dossier storico](https://casa-margherita-archai.netlify.app/archivio-progetto/) · [Visita le proposte in 3D](https://casa-margherita-archai.netlify.app/Atlante_3D/?versione=P06) · [Scarica il progetto e i CAD](https://github.com/Giulianomlodi/casa-margherita-22/releases/download/r03-pubblica/Casa_Margherita_22_Progetto.zip)

Il dossier di 26 tavole descrive l’immobile, l’analisi territoriale e cinque ipotesi di intervento. Il quaderno *Tre case, due quote* aggiunge tre proposte per tutta la casa, con piante principali, piante alte, sezioni e viste delle scale. Nell’atlante si possono esplorare nove versioni dell’appartamento e quattro del garage.

## Elaborati

- `Casa_Margherita_22.pdf` e `Apri_il_progetto.html` — dossier stampabile e navigabile.
- `Atlante_3D/Case_e_soppalchi.pdf` e `Atlante_3D/Album_render.pdf` — quaderno soppalchi e album delle viste.
- `Atlante_3D/` — visite panoramiche giorno e sera, galleria e confronti, modelli GLB, IFC4 e Blender.
- `CAD/` e `tavole/` — disegni DXF in metri e tavole SVG modificabili.
- `Sorgenti_3D/` — istruzioni e sorgenti per i modelli.

Per consultare lo ZIP, estrarre l’intera cartella e aprire `Apri_il_progetto.html`. Per il modello 3D locale, seguire le indicazioni del visualizzatore per selezionare la cartella dell’atlante. Le fonti e i crediti delle immagini sono indicati negli elaborati.

## Pubblicazione

Netlify esegue `python3 scripts/publish.py` sul ramo `main` e serve `dist/`. La compilazione usa Python 3 e la libreria standard. Per provare il sito in locale eseguire lo stesso comando e poi `python3 -m http.server --directory dist`. La release `r03-pubblica` contiene lo ZIP offline associato a questa edizione.

I visitatori possono aprire il sito e scaricare gli elaborati direttamente. Gli allegati integrali forniti dal committente sono disponibili ai titolari del precedente invito riservato. La chiave rimane fuori da Git.
