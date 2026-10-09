# Gestionale Lead & Audit · Guida v3.0

## Parti dalla Panoramica
Cerca per azienda, dominio o sede. Filtra per stato e località. La tabella mostra il prossimo passo e la scadenza. “Aggiungi un nuovo lead” registra una nuova azienda senza modificare le altre.

## Apri la Scheda lead
Il selettore distingue anche aziende omonime tramite sede e identificativo. Ogni scheda contiene:

- **Note e contatti:** stato commerciale, note, prossima azione e scadenza (AAAA-MM-GG). Salva con il pulsante del modulo. Registra telefonate, email e incontri nello storico; il programma non invia messaggi.
- **Audit preliminare:** controlla l’HTML della pagina, HTTP, HTTPS con certificato verificato, title, description e H1. Premi “Conserva questa scansione” per archiviarla. “Riporta i risultati automatici” sostituisce soltanto le verifiche coperte dalla scansione; le altre restano invariate.
- **Checklist:** scegli Non verificato, Nessuna criticità, Criticità o Non applicabile per ciascun controllo. Salva la checklist. La barra mostra quante verifiche hai eseguito.
- **Report e allegati:** scrivi il report o carica TXT, Markdown, PDF o Word (10 MB massimo). Controlla l’anteprima, seleziona “Aggiungi al report” e salva. Si conserva il testo estratto, non il file originale. I PDF scansionati non sono supportati; conserva l’originale nella cartella del progetto. Puoi scaricare la scheda in Markdown.
- **Anagrafica:** modifica nome, sito, sede, email e telefono.

## Leggi correttamente l’indice
L’indice criticità è il numero di criticità diviso per i controlli verificati applicabili. Non è una probabilità di vendita e non rende confrontabili audit con coperture diverse. Guarda sempre anche quante verifiche sono state eseguite. I vecchi checkbox True diventano criticità; i False diventano Non verificato perché non dimostrano un controllo positivo. I vecchi score nella tabella sono provvisori finché non salvi la nuova checklist.

L’assenza di FAQ, blog o breadcrumbs non è automaticamente un difetto. Le voci informative e amministrative non costituiscono una certificazione di conformità. I risultati automatici riguardano solo la pagina richiesta, senza eseguire JavaScript; niente giudizi automatici su mobile, cookie, Core Web Vitals o strategia.

## Importa ed esporta
Scarica regolarmente **Archivio completo · CSV**: contiene tutti i dati, compresi checklist e storico. La copia per foglio di calcolo protegge i valori che potrebbero essere interpretati come formule ed è destinata alla consultazione.

L’importazione legge CSV UTF-8, anche con BOM, separati da virgola, punto e virgola o tabulazione. Aggiunge nuove aziende; le combinazioni nome+sito già presenti sono ignorate. Non è un ripristino completo di backup.

## Conservazione e accesso
Ogni modifica crea una copia precedente nella cartella locale `backups/` (ultime 20). I salvataggi sono atomici e controllano la versione della scheda, così due sessioni non si sovrascrivono silenziosamente. Non cancellare gli ID dal CSV.

**Streamlit Community Cloud non garantisce la persistenza dei file locali.** CSV e backup locali possono scomparire con riavvii o ridistribuzioni. Per conservazione definitiva serve un archivio esterno; questa versione non ne configura uno implicitamente. Scarica il backup prima di aggiornare. In locale il CSV resta sul tuo disco.

Limita l’accesso alla tua app dalle impostazioni Streamlit. L’accesso GitHub dell’amministratore non è una protezione automatica per i visitatori. Il repository originario è pubblico e contiene già il CSV: valuta separatamente accesso al repository e accesso all’app.

## Avvio sul PC con Git Bash
Apri Git Bash nella cartella del progetto:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m streamlit run App.py
```

Se Windows non trova `python`, usa `py` per creare l’ambiente: `py -m venv .venv`. Dopo l’attivazione usa `python`. Arresta il gestionale con Ctrl+C. Per salvare il lavoro trasferisci il CSV su una cartella di backup privata, non su un repository pubblico.


## Analisi completa con Analisi Sito Web V2 – Audit Strategico
Nella scheda lead, apri **Audit preliminare**. La sezione **Analisi completa con il tuo Plugin** prepara una richiesta per l’azienda selezionata, con URL, ragione sociale e sede, impostando Audit completo.

1. Copia la richiesta dal riquadro, oppure scaricala come testo.
2. Premi **Avvia analisi completa del sito**: si apre la pagina del Plugin in ChatGPT. Avvia una chat con il Plugin e incolla la richiesta.
3. Scarica il report e caricalo in **Report e allegati** della stessa azienda; conferma il salvataggio.

Il collegamento apre il Plugin, ma non invia automaticamente il testo e non recupera automaticamente il report. Il gestionale conserva il testo estratto dal documento caricato; conserva anche il documento originale sul tuo PC. Se manca il sito, inseriscilo prima in Anagrafica.
