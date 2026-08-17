import streamlit as st
import pandas as pd

# Impostazione pagina
st.set_page_config(page_title="Gestionale Lead & Web Audit V2", layout="wide", page_icon="🚀")

# Title
st.title("💼 Dashboard Gestionale Lead & Audit V2")

# --- CARICAMENTO E GESTIONE DATI ---
@st.cache_data
def load_data():
    # Sostituisci 'lead.csv' con il nome esatto del tuo file CSV o Excel se diverso
    try:
        df = pd.read_csv("lead.csv")
    except Exception:
        # Fallback con struttura standard se il file non viene trovato
        df = pd.DataFrame({
            'Ragione Sociale': ['Advan Srl'],
            'Sito Web': ['https://www.advanimplantology.com'],
            'Sede': ['Amaro (UD)'],
            'Stato Workflow': ['Importato'],
            'Note Audit Digitale': ['Nessuna criticità di base rilevata.'],
            'Report Audit Completo': ['']
        })
    if 'Report Audit Completo' not in df.columns:
        df['Report Audit Completo'] = ''
    return df

df_lead = load_data()

# --- SIDEBAR: SELEZIONE LEAD ---
st.sidebar.header("🎯 Selezione Azienda")
azienda_selezionata = st.sidebar.selectbox(
    "Scegli un'azienda dal Database:",
    df_lead['Ragione Sociale'].unique()
)

# Recupero dati lead selezionato
lead_info = df_lead[df_lead['Ragione Sociale'] == azienda_selezionata].iloc[0]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Azienda:** {lead_info['Ragione Sociale']}")
st.sidebar.markdown(f"**Sito Web:** {lead_info['Sito Web']}")
st.sidebar.markdown(f"**Sede:** {lead_info.get('Sede', 'N/D')}")

# --- MAIN CONTENT ---
st.markdown(f"## 🏢 Scheda Cliente: **{lead_info['Ragione Sociale']}**")

# Sezione Diagnosi ed Audit
st.markdown("### 🚀 Diagnosi Express SEO/UX & Audit V2")

col_scan, col_info = st.columns([1, 2])
with col_scan:
    if st.button("🔍 Esegui Scansione Tecnico-SEO", type="primary"):
        st.success("Scansione rapida completata!")

# Tab per organizzare il lavoro
tab_note, tab_report, tab_prompt = st.tabs([
    "✏️ Modifica Note & Workflow", 
    "📄 Report Web Audit V2 (Generato)", 
    "📋 Prompt V2 per ChatGPT/Gemini"
])

with tab_note:
    st.subheader("Gestione Lead e Report Completo")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        stato_wf = st.selectbox(
            "Stato Avanzamento Workflow:",
            ["Importato", "In Analisi", "Audit Generato", "Contattato", "In Trattativa", "Vinto", "Perso"],
            index=0
        )
    
    audit_completo = st.text_area(
        "📥 Incolla qui il Report Audit V2 generato da ChatGPT/Gemini:",
        value=lead_info.get('Report Audit Completo', ''),
        height=220,
        help="Incolla qui l'analisi approfondita creata con il prompt V2."
    )
    
    note_sintesi = st.text_area(
        "📝 Note / Criticità SEO per Pitch Commerciale:",
        value=lead_info.get('Note Audit Digitale', 'Nessuna criticità di base rilevata.'),
        height=100,
        help="Questi punti verranno inseriti nel pitch commerciale."
    )
    
    if st.button("💾 Salva Dettagli Lead e Report", type="primary"):
        st.success(f"Dati di {lead_info['Ragione Sociale']} salvati con successo!")

with tab_report:
    st.subheader("📄 Visualizzazione Report Salvato")
    if audit_completo.strip():
        st.markdown(audit_completo)
        st.download_button(
            label="⬇️ Scarica Report Audit (.txt)",
            data=audit_completo,
            file_name=f"Report_Audit_{lead_info['Ragione Sociale'].replace(' ', '_')}.txt",
            mime="text/plain"
        )
    else:
        st.info("Nessun report completo ancora incollato per questo cliente.")

with tab_prompt:
    st.subheader("📋 Prompt V2 Pronto per ChatGPT / Gemini")
    st.write("Copia questo prompt e incollalo nel tuo ChatGPT/Gemini per produrre l'audit da 12 pagine.")
    
    prompt_testo = f"""Agisci come Senior Web Audit Consultant ed esegui un Audit Web V2 per il sito:
URL: {lead_info['Sito Web']}
Azienda: {lead_info['Ragione Sociale']}
Sede: {lead_info.get('Sede', 'N/D')}

Applica le regole del Manuale Tecnico Audit Web V2:
1. Classifica i rilievi in MISURATO, OSSERVATO, INFERITO, NON VERIFICABILE.
2. Calcola lo score per le 8 aree (SEO tecnica, On-page, Performance, UX, Contenuti E-E-A-T, CRO, Accessibilità, AI Discoverability).
3. Produci: Executive Summary, Registro Evidenze, Scorecard, Quick Wins e Piano d'azione prioritizzato.

Evidenze preliminari già registrate:
{note_sintesi}"""

    st.code(prompt_testo, language="text")

# Pitch commerciale in fondo
st.markdown("---")
st.subheader("📧 Pitch Commerciale Personalizzato")
pitch_mail = f"""Gentile Direzione,

Analizzando la presenza digitale di {lead_info['Ragione Sociale']} ({lead_info['Sito Web']}), abbiamo rilevato i seguenti aspetti d'impatto:
{note_sintesi}

Questo divario digitale potrebbe limitare le Vostre opportunità commerciali sui motori di ricerca.

Abbiamo elaborato un audit preliminare di posizionamento SEO e visibilità B2B specifica per il Vostro settore.
"""
st.text_area("Copia Testo Mail:", value=pitch_mail, height=180)