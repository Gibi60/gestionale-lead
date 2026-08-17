import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lead Management CRM B2B", layout="wide", page_icon="🍊")

CSV_FILE = "Gestione_Lead_Locale.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        st.error(f"File {CSV_FILE} non trovato!")
        return pd.DataFrame()

def save_data(df):
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

df = load_data()

st.title("🍊 Lead Management & Opportunity Scoring B2B")
st.caption("Piattaforma CRM di qualificazione, diagnosi SEO e outreach")

if not df.empty:
    st.sidebar.header("🔍 Filtri Strategici")
    
    priorita_opts = list(df["Priorita"].dropna().unique())
    priorita_filter = st.sidebar.multiselect("Priorità Lead", options=priorita_opts, default=priorita_opts)
    
    stato_opts = list(df["Stato Workflow"].dropna().unique())
    stato_filter = st.sidebar.multiselect("Stato Workflow", options=stato_opts, default=stato_opts)

    comune_opts = sorted(list(df["Comune"].dropna().unique()))
    comune_filter = st.sidebar.multiselect("Comune / Sede", options=comune_opts, default=comune_opts)

    df_filtered = df[
        df["Priorita"].isin(priorita_filter) & 
        df["Stato Workflow"].isin(stato_filter) &
        df["Comune"].isin(comune_filter)
    ]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Totale Lead Filtrati", len(df_filtered))
    col2.metric("Priorità Alta (≥75)", len(df_filtered[df_filtered["Priorita"] == "Alta"]))
    col3.metric("In Contatto / Pitch", len(df_filtered[df_filtered["Stato Workflow"].isin(["Pitch Inviato", "In Trattativa"])]))
    col4.metric("Chiuso / Cliente", len(df_filtered[df_filtered["Stato Workflow"] == "Cliente Acquisito"]))
    col5.metric("Fatturato Medio", "€ 4.7M" if len(df_filtered)>0 else "N/D")

    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Dashboard Tabelle", "🔍 Scheda Lead & Outreach Operator"])

    with tab1:
        st.subheader("Elenco Lead Processati & Scoring LOS")
        st.dataframe(
            df_filtered[["ID Lead", "Ragione Sociale", "Comune", "Fatturato", "Lead Opp Score", "Priorita", "Stato Workflow", "Referente", "Sito Web"]],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.subheader("Scheda di Dettaglio & Sales Engine")
        
        lead_options = df_filtered["ID Lead"] + " - " + df_filtered["Ragione Sociale"]
        selected_lead_str = st.selectbox("Seleziona Azienda su cui operare:", lead_options if len(lead_options)>0 else ["Nessun lead disponibile"])
        
        if selected_lead_str and selected_lead_str != "Nessun lead disponibile":
            lead_id = selected_lead_str.split(" - ")[0]
            lead_idx = df[df["ID Lead"] == lead_id].index[0]
            row = df.loc[lead_idx]

            col_a, col_b = st.columns([1, 1])
            
            with col_a:
                st.markdown(f"### 🏢 **{row['Ragione Sociale']}**")
                st.write(f"📍 **Sede:** {row['Comune']} ({row['Indirizzo'] if pd.notna(row['Indirizzo']) else 'N/D'})")
                st.write(f"💰 **Fatturato:** {row['Fatturato']}")
                st.write(f"🌐 **Sito Web:** [{row['Sito Web']}](http://{row['Sito Web']})" if pd.notna(row['Sito Web']) else "🌐 **Sito Web:** N/D")
                st.write(f"📞 **Telefono:** {row['Telefono'] if pd.notna(row['Telefono']) else 'N/D'}")
                st.write(f"✉️ **Email:** {row['Email'] if pd.notna(row['Email']) else 'N/D'}")
                st.write(f"👤 **Referente:** {row['Referente'] if pd.notna(row['Referente']) else 'Direzione Generica'}")

            with col_b:
                st.markdown("### 📊 **Punteggi Algoritmo LOS**")
                los_score = int(row['Lead Opp Score'])
                st.metric("Lead Opportunity Score", f"{los_score}/100")
                st.progress(los_score)
                
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Fit Commerciale:** {row['Commercial Fit']}/100")
                c2.write(f"**Digital Gap:** {row['Digital Gap']}/100")
                c3.write(f"**Data Quality:** {row['Data Quality']}/100")

            st.markdown("---")
            
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.markdown("### 🔄 **Aggiorna Stato e Note CRM**")
                
                current_status = row['Stato Workflow'] if pd.notna(row['Stato Workflow']) else "Importato"
                status_list = ["Importato", "In Contatto", "Pitch Inviato", "In Trattativa", "Cliente Acquisito", "Non Interessato"]
                
                new_status = st.selectbox("Stato Avanzamento Lead:", status_list, index=status_list.index(current_status) if current_status in status_list else 0)
                
                current_audit = str(row['Note Audit Digitale']) if pd.notna(row['Note Audit Digitale']) else ""
                new_audit = st.text_area("Note Audit / Criticità SEO:", current_audit, height=100)
                
                if st.button("💾 Salva Modifiche Lead"):
                    df.loc[lead_idx, 'Stato Workflow'] = new_status
                    df.loc[lead_idx, 'Note Audit Digitale'] = new_audit
                    save_data(df)
                    st.success(f"Modifiche per {row['Ragione Sociale']} salvate con successo!")
                    st.rerun()

            with col_right:
                st.markdown("### ✉️ **Pitch Commerciale Personalizzato**")
                
                referente_saluto = f"Gentile {row['Referente']}" if pd.notna(row['Referente']) and str(row['Referente']).strip() != "" else "Gentile Direzione"
                critica_str = new_audit if new_audit else "alcune ottimizzazioni sulla visibilità SEO"
                
                pitch_text = f"{referente_saluto},\n\nAnalizzando la presenza digitale di {row['Ragione Sociale']} ({row['Sito Web']}), abbiamo rilevato che {critica_str}. Questo sta limitando le Vostre opportunità commerciali sui motori di ricerca.\n\nAbbiamo elaborato un'analisi preliminare di posizionamento SEO e visibilità B2B specifica per il Vostro settore.\n\nSiete disponibili per un breve confronto telefonico di 10 minuti la prossima settimana per condividerne i dettagli?\n\nCordiali saluti,\nGilberto Del Pizzo\nConsulente Digital Strategy & SEO"
                st.text_area("Copia il Testo della Mail/Pitch:", pitch_text, height=220)