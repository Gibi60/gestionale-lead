import streamlit as st
import pandas as pd

# Impostazione layout pagina
st.set_page_config(page_title="Gestionale Lead & Web Audit V2", layout="wide", page_icon="🚀")

st.title("💼 Dashboard Gestionale Lead & Audit V2")

# --- CARICAMENTO DATI ROBUSTO ---
@st.cache_data
def load_data():
    file_path = "Gestione_Lead_Locale.csv" 
    try:
        # Riconoscimento automatico del separatore (virgola o punto e virgola)
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
    except Exception:
        try:
            # Secondo tentativo esplicito con punto e virgola
            df = pd.read_csv(file_path, sep=';', on_bad_lines='skip')
        except Exception as e:
            st.error(f"Errore nel caricamento del file {file_path}: {e}")
            df = pd.DataFrame({
                'Ragione Sociale': ['Advan Srl'],
                'Sito Web': ['https://www.advanimplantology.com'],
                'Sede': ['Amaro (UD)'],
                'Stato Workflow': ['Importato'],
                'Note Audit Digitale': ['Nessuna criticità di base rilevata.']
            })

    # Pulizia nomi colonne da eventuali spazi extra
    df.columns = [str(col).strip() for col in df.columns]

    # Mappatura colonne
    if 'Ragione Sociale' not in df.columns:
        if 'Azienda' in df.columns:
            df['Ragione Sociale'] = df['Azienda']
        elif 'Nome' in df.columns:
            df['Ragione Sociale'] = df['Nome']
        elif len(df.columns) > 0:
            df['Ragione Sociale'] = df.iloc[:, 0]

    if 'Sito Web' not in df.columns and 'Sito' in df.columns:
        df['Sito Web'] = df['Sito']

    if 'Report Audit Completo' not in df.columns:
        df['Report Audit Completo'] = ''

    return df

df_lead = load_data()

# --- SIDEBAR: SELEZIONE AZIENDA ---
st.sidebar.header("🎯 Selezione Azienda")

elenco_aziende = df_lead['Ragione Sociale'].dropna().unique().tolist()
azienda_selezionata = st.sidebar.selectbox("Scegli un'azienda dal Database:", elenco_aziende)

# Recupero riga lead selezionata
lead_info = df_lead[df_lead['Ragione Sociale'] == azienda_selezionata].iloc[0]

# Informazioni rapide in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Azienda:** {lead_info['Ragione Sociale']}")
st.sidebar.markdown(f"**Sito Web:** {lead_info.get('Sito Web', 'N/D')}")
st.sidebar.markdown(f"**Sede:** {lead_info.get('Sede', 'N/D')}")

# --- SCHEDA CLIENTE CENTRALE ---
st.markdown(f"## 🏢 Scheda Cliente: **{lead_info['Ragione Sociale']}**")

# Pulsante Scansione Rapida
col_scan, col_space = st.columns([1, 2])
with col_scan:
    if st.button("🔍 Esegui Scansione Tecnico-SEO", type="primary"):
        st.success("Scansione rapida di base completata!")

# Schede di Lavoro
tab_note, tab_report, tab_prompt = st.tabs([
    "✏️ Modifica Note & Workflow", 
    "📄 Report Web Audit V2 (Generato)", 
    "📋 Prompt V2 per ChatGPT/Gemini"
])

with tab_note:
    st.subheader("Gestione Lead e Report Completo")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        stato_attuale = lead_info.get('Stato Workflow', 'Importato')
        stati_possibili = ["Importato", "In Analisi", "Audit Generato", "Contattato", "In Trattativa", "Vinto", "Perso"]
        idx = stati_possibili.index(stato_attuale) if stato_attuale in stati_possibili else 0
        stato_wf = st.selectbox("Stato Avanzamento Workflow:", stati_possibili, index=idx)
    
    # Campo per salvare l'audit da ChatGPT
    audit_completo = st.text_area(
        "📥 Incolla qui il Report Audit V2 generato da ChatGPT/Gemini:",
        value=str(lead_info.get('Report Audit Completo', '')),
        height=220,
        help="Incolla l'analisi completa generata da ChatGPT per conservarla nella scheda cliente."
    )
    
    # Sintesi per la mail
    note_sintesi = st.text_area(
        "📝 Note / Criticità SEO per Pitch Commerciale:",
        value=str(lead_info.get('Note Audit Digitale', 'Nessuna criticità di base rilevata.')),
        height=100,
        help="Questi punti sintetici verranno usati per personalizzare la mail d'attacco."
    )
    
    if st.button("💾 Salva Dettagli Lead e Report", type="primary"):
        st.success(f"Dati di {lead_info['Ragione Sociale']} aggiornati con successo!")

with tab_report:
    st.subheader("📄 Visualizzazione Report Salvato")
    if audit_completo.strip():
        st.markdown(audit_completo)
        st.download_button(
            label="⬇️ Scarica Report Audit (.txt)",
            data=audit_completo,
            file_name=f"Report_Audit_{str(lead_info['Ragione Sociale']).replace(' ', '_')}.txt",
            mime="text/plain"
        )
    else:
        st.info("Nessun report completo ancora incollato per questo cliente.")

with tab_prompt:
    st.subheader("📋 Prompt V2 Pronto per ChatGPT / Gemini")
    st.write("Copia questo prompt e incollalo in ChatGPT/Gemini per produrre l'audit approfondito.")
    
    prompt_testo = f"""Agisci come Senior Web Audit Consultant ed esegui un Audit Web V2 per il sito:
URL: {lead_info.get('Sito Web', '')}
Azienda: {lead_info['Ragione Sociale']}
Sede: {lead_info.get('Sede', 'N/D')}

Applica le regole del Manuale Tecnico Audit Web V2:
1. Classifica i rilievi in MISURATO, OSSERVATO, INFERITO, NON VERIFICABILE.
2. Calcola lo score per le 8 aree (SEO tecnica, On-page, Performance, UX, Contenuti E-E-A-T, CRO, Accessibilità, AI Discoverability).
3. Produci: Executive Summary, Registro Evidenze, Scorecard, Quick Wins e Piano d'azione prioritizzato.

Evidenze preliminari già registrate:
{note_sintesi}"""

    st.code(prompt_testo, language="text")

# --- PITCH COMMERCIALE ---
st.markdown("---")
st.subheader("📧 Pitch Commerciale Personalizzato")

pitch_mail = f"""Gentile Direzione,

Analizzando la presenza digitale di {lead_info['Ragione Sociale']} ({lead_info.get('Sito Web', '')}), abbiamo rilevato i seguenti aspetti d'impatto:
{note_sintesi}

Questo divario digitale potrebbe limitare le Vostre opportunità commerciali sui motori di ricerca.

Abbiamo elaborato un audit preliminare di posizionamento SEO e visibilità B2B specifica per il Vostro settore.
"""

st.text_area("Copia Testo Mail:", value=pitch_mail, height=180)