# Casa Margherita 22

Studio preliminare per l'appartamento di Palazzo Lombardo e il garage di Vico Piazza, San Gregorio di Catania. Il dossier comprende 26 tavole con cinque proposte di intervento, planimetrie, assonometrie e una stima dei lavori.

## Consultazione

In locale, aprire `Apri_il_progetto.html` o `Casa_Margherita_22.pdf`. Le cartelle `CAD/` e `tavole/` contengono rispettivamente 8 DXF e 17 SVG. Il [portale Netlify](https://casa-margherita-22.netlify.app/) apre lo stesso dossier con il link privato consegnato via email e permette di scaricare PDF, progetto completo e originali.

## Pubblicazione

Netlify serve esclusivamente `public/` dal ramo `main`. Il webhook del repository attiva il build hook privato del sito sulla versione corrente di `main`. Il portale decifra nel browser i materiali con AES-256-GCM. La chiave si trova nel frammento del link riservato. Chi riceve il link completo può aprire il progetto.

Per modificare testi, disegni o materiali, aggiornare i file sorgente. Per cambiare la pagina di accesso o i pulsanti aggiornare `web/`. Dalla copia di lavoro che contiene la chiave installare `cryptography` per Python 3 e lanciare `python scripts/publish.py`. Verificare e committare anche `public/`, quindi inviare il commit a `main`.

La chiave di lavoro è in `.accesso/chiave`, esclusa da Git. Per ricreare il pacchetto fonti, la copia di lavoro conserva i due allegati in `fonti_private/` e cerca i due video originali nella cartella superiore, come nell'archivio ARCHAI. Una nuova macchina deve recuperare la chiave da un titolare prima di rigenerare la release. Il sito già preparato può essere distribuito direttamente da Git.
