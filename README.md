# GDP · Gestionale Lead & Audit v3
Gestionale personale Streamlit per lead, note, workflow, storico dei contatti e audit HTML preliminari.

Leggere [GUIDA_USO.md](GUIDA_USO.md) per utilizzo, migrazione, limiti della persistenza Cloud e istruzioni Git Bash su Windows.

## Installazione
Python 3.11 o successivo. `python -m pip install -r requirements.txt`, poi `python -m streamlit run App.py`.

## Test
`python -m pip install pytest` e `python -m pytest tests -q`.

## Dati e compatibilità
L’app conserva le colonne storiche del CSV. Migrazione in memoria senza riscrivere il file all’avvio; ID stabili anche con nomi omonimi. Salvataggio atomico, backup delle ultime 20 versioni e controllo dei conflitti nel singolo processo. Per più processi o conservazione permanente Cloud serve un database esterno. `GDP_LEAD_FILE` consente di selezionare un percorso alternativo per il CSV; non è una credenziale.

Non inserire credenziali in Git. Il CSV originario non è modificato da questa revisione del codice. Prima di aggiornare il deployment esportare i dati operativi correnti: potrebbero differire dal CSV nel repository.
