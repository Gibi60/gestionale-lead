import streamlit as st
import pandas as pd
import urllib.request
import urllib.error
import ssl
import time
import re

# Impostazione layout pagina
st.set_page_config(page_title="Gestionale Lead & Web Audit V2", layout="wide", page_icon="🚀")

st.title("💼 Dashboard Gestionale Lead & Audit V2")

# --- FUNZIONE SCANSIONE SEO REALE CON USER-AGENT COMPLETO ---
def scansione_seo_reale(url):
    if not url or pd.isna(url) or str(url).strip() in ['', 'nan', 'N/D']:
        return "❌ Nessun URL valido specificato per questa azienda.", []
    
    url_pulito = str(url).strip()
    if not url_pulito.startswith(('http://', 'https://')):
        url_pulito = 'https://' + url_pulito
        
    risultati = []
    criticita = []
    start_time = time.time()
    
    # Header estesi per simulare un browser reale ed evitare blocchi 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url_pulito, headers=headers)
        
        with urllib.request.urlopen(req, timeout=8, context=ctx) as response:
            load_time = round(time.time() - start_time, 2)
            status_code = response.getcode()
            html = response.read().decode('utf-8', errors='ignore')
            
            risultati.append(f"🌐 **URL Verificato:** {url_pulito}")
            risultati.append(f"✅ **Stato Server:** HTTP {status_code}")
            risultati.append(f"⏱️ **Tempo Risposta Server:** {load_time}s")
            
            if load_time > 2.5:
                criticita.append(f"- Tempo di risposta del server elevato ({load_time}s).")
            
            # Tag Title
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match and title_match.group(1).strip():
                risultati.append(f"📌 **Tag Title:** {title_match.group(1).strip()}")
            else:
                risultati.append("⚠️ **Tag Title:** MANCANTE o vuoto")
                criticita.append("- Tag Title mancante o non valorizzato correttamente.")
                
            # Meta Description
            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if desc_match and desc_match.group(1).strip():
                risultati.append(f"📝 **Meta Description:** Presente ({len(desc_match.group(1))} caratteri)")
            else:
                risultati.append("⚠️ **Meta Description:** MANCANTE o non rilevata")
                criticita.append("- Meta Description non impostata (impatto negativo sui CTR nei risultati di ricerca).")
                
            # Tag H1
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
            if h1_match:
                clean_h1 = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                risultati.append(f"🏷️ **Tag H1 Principale:** {clean_h1}")
            else:
                risultati.append("⚠️ **Tag H1 Principale:** MANCANTE")
                criticita.append("- Tag H1 principale mancante nella homepage.")
                
    except urllib.error.HTTPError as e:
        if e.code == 403:
            risultati.append(f"⚠️ **Sito Attivo ma Protezione Firewall Rilevata (HTTP 403)**: Il server blocca le richieste automatizzate diretta da IP cloud. Il sito è raggiungibile da browser.")
            criticita.append("- Presenza di protezione/firewall che blocca gli scansionatori automatici.")
        else:
            risultati.append(f"❌ **Errore HTTP {e.code}** raggiungendo {url_pulito}.")
            criticita.append(f"- Il server restituisce errore HTTP {e.code}.")
    except Exception as e:
        risultati.append(f"❌ **Impossibile raggiungere il sito web** ({url_pulito}). Errore: {e}")
        criticita.append("- Sito web temporaneamente o permanentemente irraggiungibile.")
        
    return "\n\n".join(risultati), criticita

# --- CARICAMENTO DATI ---
@st.cache_data
def load_data():
    file_path = "Gestione_Lead_Locale.csv" 
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
    except Exception:
        try:
            df = pd.read_csv(file_path, sep=';', on_bad_lines='skip')
        except Exception as e:
            st.error(f"Errore nel caricamento del file {file_path}: {e}")
            df = pd.DataFrame({
                'Azienda': ['Plan 1 Health Srl'],
                'WEB': ['https://www.p1h.it'],
                'SEDE': ['Amaro (UD)'],
                'Stato Workflow': ['Importato'],
                'Note Audit Digitale': ['Nessuna criticità di base rilevata.']
            })

    df.columns = [str(col).strip() for col in df.columns]

    col_map = {}
    for col in df.columns:
        c_lower = col.lower()
        if c_lower in ['azienda', 'ragione sociale', 'ragionesociale', 'nome', 'company']:
            col_map[col] = 'Ragione Sociale'
        elif c_lower in ['web', 'sito', 'sito web', 'sitoweb', 'url', 'website', 'link', 'dominio']:
            col_map[col] = 'Sito Web'
        elif c_lower in ['sede', 'città', 'citta', 'location']:
            col_map[col] = 'Sede'
            
    df = df.rename(columns=col_map)

    if 'Ragione Sociale' not in df.columns:
        df['Ragione Sociale'] = df.iloc[:, 0]
    if 'Sito Web' not in df.columns:
        df['Sito Web'] = 'N/D'
    if 'Sede' not in df.columns:
        df['Sede'] = 'N/D'
    if 'Stato Workflow' not in df.columns:
        df['Stato Workflow'] = 'Importato'
    if 'Report Audit Completo' not in df.columns:
        df['Report Audit Completo'] = ''
    if 'Note Audit Digitale' not in df.columns:
        df['Note Audit Digitale'] = 'Nessuna criticità di base rilevata.'

    return df

df_lead = load_data()

# --- TAB DI NAVIGAZIONE PRINCIPALE ---
tab_panoramica, tab_scheda = st.tabs([
    "📊 Panoramica Database & Filtri", 
    "🏢 Scheda Dettaglio Lead & Audit V2"
])

# TAB 1: PANORAMICA DATABASE
with tab_panoramica:
    st.subheader("📊 Tabella Generale Lead & Filtri Avanzati")
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Totale Lead nel Database", len(df_lead))
    counts = df_lead['Stato Workflow'].value_counts()
    col_k2.metric("In Analisi / Audit", counts.get("In Analisi", 0) + counts.get("Audit Generato", 0))
    col_k3.metric("Contattati / Trattativa", counts.get("Contattato", 0) + counts.get("In Trattativa", 0))
    st.markdown("---")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        ricerca_nome = st.text_input("🔍 Cerca Azienda per Ragione Sociale / Nome:")
    with col_f2:
        stati_disponibili = ["Tutti"] + df_lead['Stato Workflow'].dropna().unique().tolist()
        filtro_stato = st.selectbox("🎯 Filtra per Stato Workflow:", stati_disponibili)
    
    df_filtrato = df_lead.copy()
    if ricerca_nome:
        df_filtrato = df_filtrato[df_filtrato['Ragione Sociale'].astype(str).str.contains(ricerca_nome, case=False, na=False)]
    if filtro_stato != "Tutti":
        df_filtrato = df_filtrato[df_filtrato['Stato Workflow'] == filtro_stato]
        
    st.dataframe(df_filtrato, use_container_width=True, height=420)

# TAB 2: SCHEDA DETTAGLIO LEAD
with tab_scheda:
    elenco_aziende = df_lead['Ragione Sociale'].dropna().unique().tolist()
    azienda_selezionata = st.selectbox("🎯 Seleziona l'Azienda da analizzare:", elenco_aziende, key="select_azienda_tab2")
    
    lead_info = df_lead[df_lead['Ragione Sociale'] == azienda_selezionata].iloc[0]
    sito_url = str(lead_info.get('Sito Web', 'N/D')).strip()
    sede_info = str(lead_info.get('Sede', 'N/D')).strip()
    
    st.markdown(f"### 🏢 Scheda Cliente: **{lead_info['Ragione Sociale']}**")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.markdown(f"**Sito Web:** [{sito_url}]({sito_url if sito_url.startswith('http') else 'https://' + sito_url})" if sito_url != 'N/D' else "**Sito Web:** N/D")
    col_info2.markdown(f"**Sede:** {sede_info}")
    col_info3.markdown(f"**Stato Attuale:** `{lead_info.get('Stato Workflow', 'Importato')}`")
    
    st.markdown("---")
    
    # SCANNER SEO
    col_btn, col_res = st.columns([1, 2])
    with col_btn:
        st.write("### 🔍 Diagnosi Rapida")
        lancia_scansione = st.button("🚀 Esegui Scansione Tecnico-SEO Reale", type="primary")
        
    with col_res:
        if lancia_scansione:
            with st.spinner("Scansione del sito in corso..."):
                report_scansione, lista_crit = scansione_seo_reale(sito_url)
                st.session_state['ultimo_report_scansione'] = report_scansione
                
                if lista_crit:
                    st.session_state[f'note_{azienda_selezionata}'] = "\n".join(lista_crit)
                else:
                    st.session_state[f'note_{azienda_selezionata}'] = "Nessuna criticità di base rilevata."
        
        if 'ultimo_report_scansione' in st.session_state:
            st.info(st.session_state['ultimo_report_scansione'])

    st.markdown("---")

    # TAB DI LAVORO
    tab_note, tab_report, tab_prompt = st.tabs([
        "✏️ Modifica Note & Workflow", 
        "📄 Report Web Audit V2 (Generato / Caricato)", 
        "📋 Prompt V2 (Opzionale per IA)"
    ])
    
    with tab_note:
        st.subheader("Gestione Lead e Impostazioni")
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            stato_attuale = lead_info.get('Stato Workflow', 'Importato')
            stati_possibili = ["Importato", "In Analisi", "Audit Generato", "Contattato", "In Trattativa", "Vinto", "Perso"]
            idx = stati_possibili.index(stato_attuale) if stato_attuale in stati_possibili else 0
            stato_wf = st.selectbox("Stato Avanzamento Workflow:", stati_possibili, index=idx)
        
        valore_default_note = st.session_state.get(
            f'note_{azienda_selezionata}', 
            str(lead_info.get('Note Audit Digitale', 'Nessuna criticità di base rilevata.'))
        )
        
        note_sintesi = st.text_area(
            "📝 Note / Criticità SEO per Pitch Commerciale:",
            value=valore_default_note,
            height=120,
            help="Questi punti verranno usati per personalizzare la mail di contatto."
        )
        
        if st.button("💾 Salva Dettagli Lead", type="primary"):
            st.session_state[f'note_{azienda_selezionata}'] = note_sintesi
            st.success(f"Dati di {lead_info['Ragione Sociale']} aggiornati con successo!")

    with tab_report:
        st.subheader("📄 Gestione Report Audit Completo")
        file_caricato = st.file_uploader("📂 Carica File Report (.txt, .md):", type=["txt", "md"])
        
        testo_iniziale = str(lead_info.get('Report Audit Completo', ''))
        if file_caricato is not None:
            testo_iniziale = file_caricato.read().decode("utf-8", errors="ignore")
            st.success("File caricato con successo!")
            
        audit_completo = st.text_area(
            "📥 Incolla qui (o modifica) il Report Audit V2:",
            value=testo_iniziale,
            height=250
        )
        
        if audit_completo.strip():
            st.markdown("---")
            st.markdown("### Anteprima Report Salvato:")
            st.markdown(audit_completo)
            st.download_button(
                label="⬇️ Scarica Report Audit (.txt)",
                data=audit_completo,
                file_name=f"Report_Audit_{str(lead_info['Ragione Sociale']).replace(' ', '_')}.txt",
                mime="text/plain"
            )

    with tab_prompt:
        st.subheader("📋 Prompt V2 Pronto per Chat IA generiche")
        st.info("💡 **Nota:** Se usi già il tuo **Custom GPT dedicato**, puoi ignorare questo prompt e inviargli direttamente solo l'URL.")
        
        prompt_testo = f"""Agisci come Senior Web Audit Consultant ed esegui un Audit Web V2 per il sito:
URL: {sito_url}
Azienda: {lead_info['Ragione Sociale']}
Sede: {sede_info}

Evidenze rilevate da integrare:
{note_sintesi}"""

        st.code(prompt_testo, language="text")

    st.markdown("---")
    st.subheader("📧 Pitch Commerciale Personalizzato")

    pitch_mail = f"""Gentile Direzione di {lead_info['Ragione Sociale']},

Analizzando la presenza digitale del Vostro sito ({sito_url}), abbiamo rilevato i seguenti aspetti su cui intervenire:
{note_sintesi}

Questo divario digitale potrebbe limitare le Vostre opportunità commerciali sui motori di ricerca.

Abbiamo elaborato un audit preliminare di posizionamento SEO e visibilità B2B specifica per il Vostro settore.
"""

    st.text_area("Copia Testo Mail:", value=pitch_mail, height=180)