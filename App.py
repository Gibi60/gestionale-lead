import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Lead Management CRM B2B", layout="wide", page_icon="🍊")

CSV_FILE = "Gestione_Lead_Locale.csv"

def load_data():
    if not os.path.exists(CSV_FILE):
        st.error(f"File {CSV_FILE} non trovato!")
        return pd.DataFrame()
    
    # Prova lettura con separatore punto e virgola o virgola (formato Excel italiano)
    try:
        df = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8-sig")
        if len(df.columns) <= 1:
            df = pd.read_csv(CSV_FILE, sep=",", encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(CSV_FILE, sep=",", encoding="utf-8-sig")

    df.columns = df.columns.str.strip()

    # Mappatura e normalizzazione se il file è in formato grezzo (AZIENDA, SEDE, ecc.)
    if "AZIENDA" in df.columns:
        df = df.drop_duplicates(subset=["AZIENDA", "SEDE"]).reset_index(drop=True)
        df = df.rename(columns={
            "AZIENDA": "Ragione Sociale",
            "SEDE": "Comune",
            "INDIRIZZO": "Indirizzo",
            "WEB": "Sito Web",
            "MAIL": "Email"
        })

    # Integrazione colonne CRM mancanti
    if "ID Lead" not in df.columns:
        df["ID Lead"] = [f"#L{i+1:03d}" for i in range(len(df))]
    if "Fatturato" not in df.columns:
        df["Fatturato"] = "N/D"
    else:
        df["Fatturato"] = df["Fatturato"].fillna("N/D")
    
    if "Referente" not in df.columns:
        df["Referente"] = "Direzione"
    if "Telefono" not in df.columns:
        df["Telefono"] = "N/D"
    
    if "Lead Opp Score" not in df.columns:
        np.random.seed(42)
        scores = []
        for f in df["Fatturato"]:
            scores.append(np.random.randint(80, 96) if str(f) != "N/D" else np.random.randint(65, 85))
        df["Lead Opp Score"] = scores

    if "Priorita" not in df.columns:
        df["Priorita"] = df["Lead Opp Score"].apply(lambda x: "Alta" if x >= 80 else ("Media" if x >= 70 else "Bassa"))
    
    if "Stato Workflow" not in df.columns:
        df["Stato Workflow"] = "Importato"
        
    if "Commercial Fit" not in df.columns:
        df["Commercial Fit"] = 80
    if "Digital Gap" not in df.columns:
        df["Digital Gap"] = 75
    if "Data Quality" not in df.columns:
        df["Data Quality"] = 90
    if "Note Audit Digitale" not in df.columns:
        df["Note Audit Digitale"] = ""

    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False, sep=";", encoding='utf-8-sig')

df = load_data()

st.title("🍊 Lead Management & Opportunity Scoring B2B")
st.caption("Piattaforma CRM di qualificazione, diagnosi SEO e outreach")

if not df.empty:
    st.sidebar.header("🔍 Filtri Strategici")
    
    priorita_opts = list(df["Priorita"].dropna().unique())
    priorita_filter = st.sidebar.multiselect("Priorità Lead", options=priorita_opts, default=priorita_opts)
    
    stato_opts = list(df["Stato Workflow"].dropna().unique())
    stato_filter = st.sidebar.multiselect("Stato Workflow", options=stato_opts, default=stato_opts)

    comune_opts = sorted([str(c) for c in df["Comune"].dropna().unique()])
    comune_filter = st.sidebar.multiselect("Comune / Sede", options=comune_opts, default=comune_opts)

    # Filtraggio
    mask = (
        df["Priorita"].isin(priorita_filter) & 
        df["Stato Workflow"].isin(stato_filter) &
        df["Comune"].isin(comune_filter)
    )
    df_filtered = df[mask]

    # KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totale Lead Filtrati", len(df_filtered))
    col2.metric("Priorità Alta (≥80)", len(df_filtered[df_filtered["Priorita"] == "Alta"]))
    col3.metric("In Contatto / Pitch", len(df_filtered[df_filtered["Stato Workflow"].isin(["In Contatto", "Pitch Inviato", "In Trattativa"])]))
    col4.metric("Clienti Acquisiti", len(df_filtered[df_filtered["Stato Workflow"] == "Cliente Acquisito"]))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Tabella Modificabile & Gestione Stato", "🔍 Scheda Lead & Outreach Operator"])

    with tab1:
        st.subheader("Elenco Lead Processati")
        st.info("💡 Modifica lo **Stato Workflow**, il **Referente** o le **Note** direttamente nelle celle e clicca sul pulsante in basso per salvare.")

        edited_df = st.data_editor(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Stato Workflow": st.column_config.SelectboxColumn(
                    "Stato Workflow",
                    options=["Importato", "In Contatto", "Pitch Inviato", "In Trattativa", "Cliente Acquisito", "Non Interessato"],
                    required=True,
                ),
                "Priorita": st.column_config.SelectboxColumn(
                    "Priorità",
                    options=["Alta", "Media", "Bassa"],
                ),
                "Sito Web": st.column_config.LinkColumn("Sito Web"),
            },
            disabled=["ID Lead", "Ragione Sociale", "Lead Opp Score"]
        )

        if st.button("💾 Salva Modifiche della Tabella", type="primary"):
            df.update(edited_df)
            save_data(df)
            st.success("Tutti i dati e gli stati aggiornati sono stati salvati correttamente!")
            st.rerun()

    with tab2:
        st.subheader("Scheda Dettaglio Lead & Generator Pitch")
        
        lead_options = df_filtered["ID Lead"] + " - " + df_filtered["Ragione Sociale"]
        selected_lead_str = st.selectbox("Seleziona Azienda:", lead_options if len(lead_options)>0 else ["Nessun lead disponibile"])
        
        if selected_lead_str and selected_lead_str != "Nessun lead disponibile":
            lead_id = selected_lead_str.split(" - ")[0]
            lead_idx = df[df["ID Lead"] == lead_id].index[0]
            row = df.loc[lead_idx]

            col_a, col_b = st.columns([1, 1])
            
            with col_a:
                st.markdown(f"### 🏢 **{row['Ragione Sociale']}**")
                st.write(f"📍 **Sede:** {row['Comune']} ({row['Indirizzo']})")
                st.write(f"💰 **Fatturato:** {row['Fatturato']}")
                st.write(f"🌐 **Sito Web:** [{row['Sito Web']}](http://{row['Sito Web']})" if pd.notna(row['Sito Web']) else "🌐 **Sito Web:** N/D")
                st.write(f"✉️ **Email:** {row['Email']}")
                st.write(f"👤 **Referente:** {row['Referente']}")

            with col_b:
                st.markdown("### 📊 **Punteggio Algoritmo LOS**")
                los_score = int(row['Lead Opp Score'])
                st.metric("Lead Opportunity Score", f"{los_score}/100")
                st.progress(los_score)

            st.markdown("---")
            
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.markdown("### 🔄 **Aggiorna Stato Lead**")
                
                current_status = row['Stato Workflow'] if pd.notna(row['Stato Workflow']) else "Importato"
                status_list = ["Importato", "In Contatto", "Pitch Inviato", "In Trattativa", "Cliente Acquisito", "Non Interessato"]
                
                new_status = st.selectbox("Stato Avanzamento:", status_list, index=status_list.index(current_status) if current_status in status_list else 0)
                current_audit = str(row['Note Audit Digitale']) if pd.notna(row['Note Audit Digitale']) else ""
                new_audit = st.text_area("Note Audit / Criticità SEO:", current_audit, height=100)
                
                if st.button("💾 Salva Modifica Singola"):
                    df.loc[lead_idx, 'Stato Workflow'] = new_status
                    df.loc[lead_idx, 'Note Audit Digitale'] = new_audit
                    save_data(df)
                    st.success(f"Modifiche salvate per {row['Ragione Sociale']}!")
                    st.rerun()

            with col_right:
                st.markdown("### ✉️ **Pitch Commerciale**")
                
                referente_saluto = f"Gentile {row['Referente']}" if pd.notna(row['Referente']) and str(row['Referente']).strip() != "" else "Gentile Direzione"
                critica_str = new_audit if new_audit else "alcune ottimizzazioni sulla visibilità SEO"
                
                pitch_text = f"{referente_saluto},\n\nAnalizzando la presenza digitale di {row['Ragione Sociale']} ({row['Sito Web']}), abbiamo rilevato che {critica_str}. Questo sta limitando le Vostre opportunità commerciali sui motori di ricerca.\n\nAbbiamo elaborato un'analisi preliminare di posizionamento SEO e visibilità B2B specifica per il Vostro settore.\n\nSiete disponibili per un breve confronto telefonico di 10 minuti la prossima settimana per condividerne i dettagli?\n\nCordiali saluti,\nGilberto Del Pizzo\nConsulente Digital Strategy & SEO"
                st.text_area("Copia Testo Mail:", pitch_text, height=220)