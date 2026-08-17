import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lead Management CRM Local", layout="wide", page_icon="📊")

CSV_FILE = "Gestione_Lead_Locale.csv"

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        st.error(f"File {CSV_FILE} non trovato!")
        return pd.DataFrame()

df = load_data()

st.title("🍊 Lead Management & Opportunity Scoring (Locale)")
st.caption("Piattaforma locale di qualificazione e diagnosi B2B")

if not df.empty:
    st.sidebar.header("🔍 Filtri")
    priorita_filter = st.sidebar.multiselect("Priorità Lead", options=df["Priorita"].unique(), default=df["Priorita"].unique())
    
    df_filtered = df[df["Priorita"].isin(priorita_filter)]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totale Lead", len(df_filtered))
    col2.metric("Priorità Alta (≥75)", len(df_filtered[df_filtered["Priorita"] == "Alta"]))
    col3.metric("Priorità Media", len(df_filtered[df_filtered["Priorita"] == "Media"]))
    col4.metric("Priorità Bassa", len(df_filtered[df_filtered["Priorita"] == "Bassa"]))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Tabella Dashboard", "🔍 Scheda Dettaglio Lead"])

    with tab1:
        st.subheader("Elenco Lead Processati")
        st.dataframe(
            df_filtered[["ID Lead", "Ragione Sociale", "Comune", "Fatturato", "Lead Opp Score", "Priorita", "Sito Web"]],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.subheader("Scheda di Dettaglio & Audit V2")
        selected_lead_id = st.selectbox("Seleziona Azienda:", df_filtered["ID Lead"] + " - " + df_filtered["Ragione Sociale"])
        
        if selected_lead_id:
            lead_id = selected_lead_id.split(" - ")[0]
            row = df[df["ID Lead"] == lead_id].iloc[0]

            col_a, col_b = st.columns([1, 1])
            
            with col_a:
                st.markdown(f"### **{row['Ragione Sociale']}**")
                st.write(f"📍 **Sede:** {row['Comune']} ({row['Indirizzo']})")
                st.write(f"💰 **Fatturato:** {row['Fatturato']}")
                st.write(f"🌐 **Sito Web:** {row['Sito Web']}")
                st.write(f"📞 **Telefono:** {row['Telefono']}")
                st.write(f"✉️ **Email:** {row['Email']}")

            with col_b:
                st.markdown("### **Punteggi Algoritmo LOS**")
                st.metric("Lead Opportunity Score", f"{row['Lead Opp Score']}/100")
                st.progress(int(row['Lead Opp Score']))
                
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Fit:** {row['Commercial Fit']}/100")
                c2.write(f"**Gap:** {row['Digital Gap']}/100")
                c3.write(f"**Quality:** {row['Data Quality']}/100")

            st.markdown("---")
            st.markdown("### 📝 **Note Audit & Pitch**")
            st.info(f"**Criticità Rilevata:** {row['Note Audit Digitale']}")
            
            st.text_area("Bozza Pitch Commerciale", 
                f"Gentile Direzione,\n\nAnalizzando la presenza online di {row['Ragione Sociale']} ({row['Sito Web']}), abbiamo riscontrato alcune criticità tecniche ({row['Note Audit Digitale']}) che stanno limitando la Vostra visibilità SEO.\n\nSiete disponibili per un breve confronto di 10 minuti?",
                height=150
            )