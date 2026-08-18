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

# --- FUNZIONE SCANSIONE SEO REALE ---
def scansione_seo_reale(url):
    if not url or pd.isna(url) or str(url).strip() in ['', 'nan', 'N/D']:
        return "❌ Nessun URL valido specificato per questa azienda.", []
    
    url_pulito = str(url).strip()
    if not url_pulito.startswith(('http://', 'https://')):
        url_pulito = 'https://' + url_pulito
        
    risultati = []
    criticita = []
    start_time = time.time()
    
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
                criticita.append("⏱️ Tempo di risposta del server elevato")
            
            # Tag Title
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match and title_match.group(1).strip():
                risultati.append(f"📌 **Tag Title:** {title_match.group(1).strip()}")
            else:
                risultati.append("⚠️ **Tag Title:** MANCANTE o vuoto")
                criticita.append("❌ Assenza o errore nel Tag Title")
                
            # Meta Description
            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if desc_match and desc_match.group(1).strip():
                risultati.append(f"📝 **Meta Description:** Presente ({len(desc_match.group(1))} caratteri)")
            else:
                risultati.append("⚠️ **Meta Description:** MANCANTE o non rilevata")
                criticita.append("❌ Assenza Meta Description")
                
            # Tag H1
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
            if h1_match:
                clean_h1 = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                risultati.append(f"🏷️ **Tag H1 Principale:** {clean_h1}")
            else:
                risultati.append("⚠️ **Tag H1 Principale:** MANCANTE")
                criticita.append("❌ Assenza Tag H1 principale")
                
    except urllib.error.HTTPError as e:
        if e.code == 403:
            risultati.append(f"⚠️ **Protezione Firewall (HTTP 403)**: Il server blocca gli script automatici.")
            criticita.append("🔒 Errore HTTP 403 (Blocco bot/firewall)")
        else:
            risultati.append(f"❌ **Errore HTTP {e.code}**")
            criticita.append(f"❌ Errore HTTP {e.code}")
    except Exception as e:
        risultati.append(f"❌ **Impossibile raggiungere il sito** ({url_pulito}).")
        criticita.append("❌ Sito non raggiungibile o offline")
        
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
    if 'Score Opportunità (%)' not in df.columns:
        df['Score Opportunità (%)'] = 0

    return df

df_lead = load_data()

# --- NAVIGAZIONE PRINCIPALE ---
tab_panoramica, tab_scheda = st.tabs([
    "📊 Panoramica Database & Filtri", 
    "🏢 Scheda Dettaglio Lead & Audit V2"
])

# TAB 1: PANORAMICA CON ORDINAMENTO OPPORTUNITÀ
with tab_panoramica:
    st.subheader("📊 Tabella Generale Lead & Classifica Opportunità")
    
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Totale Lead nel Database", len(df_lead))
    counts = df_lead['Stato Workflow'].value_counts()
    col_k2.metric("In Analisi / Audit", counts.get("In Analisi", 0) + counts.get("Audit Generato", 0))
    col_k3.metric("Contattati / Trattativa", counts.get("Contattato", 0) + counts.get("In Trattativa", 0))
    st.markdown("---")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        ricerca_nome = st.text_input("🔍 Cerca Azienda:")
    with col_f2:
        stati_disponibili = ["Tutti"] + df_lead['Stato Workflow'].dropna().unique().tolist()
        filtro_stato = st.selectbox("🎯 Filtra per Stato Workflow:", stati_disponibili)
    with col_f3:
        ordina_score = st.checkbox("🔥 Ordina per % Opportunità (Dalla più alta)")
    
    # Sincronizza lo score corrente dal session_state nel dataframe di visualizzazione
    for idx, row in df_lead.iterrows():
        azi = row['Ragione Sociale']
        if f'score_{azi}' in st.session_state:
            df_lead.loc[idx, 'Score Opportunità (%)'] = st.session_state[f'score_{azi}']

    df_filtrato = df_lead.copy()
    if ricerca_nome:
        df_filtrato = df_filtrato[df_filtrato['Ragione Sociale'].astype(str).str.contains(ricerca_nome, case=False, na=False)]
    if filtro_stato != "Tutti":
        df_filtrato = df_filtrato[df_filtrato['Stato Workflow'] == filtro_stato]
    
    if ordina_score:
        df_filtrato = df_filtrato.sort_values(by='Score Opportunità (%)', ascending=False)
        
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

        if 'ultimo_report_scansione' in st.session_state:
            st.info(st.session_state['ultimo_report_scansione'])

    st.markdown("---")

    # --- CHECKLIST STRUTTURATA A 4 BLOCCHI ---
    st.subheader("✅ Validazione Criticità SEO & Score Opportunità Lead")
    st.write("Seleziona gli elementi critici emersi dall'analisi suddivisi per area di competenza:")

    # BLOCCO 1: SEO TECNICA
    st.markdown("#### ⚙️ 1. SEO Tecnica")
    c1, c2, c3 = st.columns(3)
    with c1:
        chk_https = st.checkbox("Mancanza HTTPS / SSL sicuro", key=f"chk_https_{azienda_selezionata}")
        chk_403 = st.checkbox("Errore HTTP 403 / Blocco Bot", key=f"chk_403_{azienda_selezionata}")
        chk_title = st.checkbox("Assenza o Errore Tag Title", key=f"chk_title_{azienda_selezionata}")
    with c2:
        chk_desc = st.checkbox("Assenza Meta Description", key=f"chk_desc_{azienda_selezionata}")
        chk_h1 = st.checkbox("Assenza Tag H1 principale", key=f"chk_h1_{azienda_selezionata}")
        chk_sitemap = st.checkbox("Assenza Sitemap.XML", key=f"chk_sitemap_{azienda_selezionata}")
    with c3:
        chk_robots = st.checkbox("Assenza / errato Robots.txt", key=f"chk_robots_{azienda_selezionata}")
        chk_speed = st.checkbox("Tempi alti risposta server", key=f"chk_speed_{azienda_selezionata}")
        chk_mobile = st.checkbox("Mobile non corretto", key=f"chk_mobile_{azienda_selezionata}")
        chk_hreflang = st.checkbox("Hreflang non corretto", key=f"chk_hreflang_{azienda_selezionata}")

    st.markdown("---")

    # BLOCCO 2: UX / UI
    st.markdown("#### 🎨 2. UX / UI (User Experience & Interface)")
    u1, u2, u3 = st.columns(3)
    with u1:
        chk_nav = st.checkbox("Navigazione non chiara", key=f"chk_nav_{azienda_selezionata}")
        chk_cta = st.checkbox("CTA non visibili o coerenti", key=f"chk_cta_{azienda_selezionata}")
    with u2:
        chk_form = st.checkbox("Form di contatto non brevi", key=f"chk_form_{azienda_selezionata}")
        chk_pop = st.checkbox("Elementi invasivi (popup)", key=f"chk_pop_{azienda_selezionata}")
    with u3:
        chk_brand = st.checkbox("Non coerenza visiva", key=f"chk_brand_{azienda_selezionata}")
        chk_bread = st.checkbox("Assenza breadcrumbs", key=f"chk_bread_{azienda_selezionata}")

    st.markdown("---")

    # BLOCCO 3: CONTENUTI E GEO
    st.markdown("#### ✍️ 3. Contenuti e GEO (Local SEO & E-E-A-T)")
    g1, g2, g3 = st.columns(3)
    with g1:
        chk_eeat = st.checkbox("Assenza contenuti originali EEAT", key=f"chk_eeat_{azienda_selezionata}")
    with g2:
        chk_faq = st.checkbox("Assenza sezione FAQ", key=f"chk_faq_{azienda_selezionata}")
        chk_blog = st.checkbox("Assenza Blog / News", key=f"chk_blog_{azienda_selezionata}")
    with g3:
        chk_nap = st.checkbox("Non coerenza NAP", key=f"chk_nap_{azienda_selezionata}")

    st.markdown("---")

    # BLOCCO 4: LEGALI E AMMINISTRATIVI
    st.markdown("#### ⚖️ 4. Legali e Amministrativi (Compliance)")
    l1, l2, l3 = st.columns(3)
    with l1:
        chk_piva = st.checkbox("Assenza Partita IVA in Home", key=f"chk_piva_{azienda_selezionata}")
        chk_gdpr = st.checkbox("Assenza GDPR Privacy", key=f"chk_gdpr_{azienda_selezionata}")
    with l2:
        chk_cookielaw = st.checkbox("Assenza Cookie Law", key=f"chk_cookielaw_{azienda_selezionata}")
        chk_banner = st.checkbox("Assenza Cookie Banner conforme", key=f"chk_banner_{azienda_selezionata}")
    with l3:
        chk_srl = st.checkbox("Assenza Informativa per SRL / SPA", key=f"chk_srl_{azienda_selezionata}")

    # Calcolo totale e score percentuale su 23 elementi totali
    elementi_totali = 23
    elementi_critici = sum([
        chk_https, chk_403, chk_title, chk_desc, chk_h1, chk_sitemap, chk_robots, chk_speed, chk_mobile, chk_hreflang,
        chk_nav, chk_cta, chk_form, chk_pop, chk_brand, chk_bread,
        chk_eeat, chk_faq, chk_blog, chk_nap,
        chk_piva, chk_gdpr, chk_cookielaw, chk_banner, chk_srl
    ])
    
    score_opportunita = int((elementi_critici / elementi_totali) * 100)
    
    # Salva nello state per la tabella generale
    st.session_state[f'score_{azienda_selezionata}'] = score_opportunita

    st.markdown("---")
    col_score1, col_score2 = st.columns([1, 3])
    with col_score1:
        st.metric(label="🎯 Potenziale di Contatto", value=f"{score_opportunita}%", delta=f"{elementi_critici}/23 Criticità")
    with col_score2:
        if score_opportunita >= 50:
            st.error("🔥 **Alta Priorità di Contatto**: Il sito presenta importanti lacune digitali. Ottimo margine per proporre un intervento correttivo immediato.")
        elif score_opportunita >= 25:
            st.warning("⚠️ **Media Priorità**: Presenta diverse aree di miglioramento strategico e tecnico.")
        else:
            st.success("✅ **Bassa Priorità / Ottimo stato**: Il sito ha una buona conformità generale.")

    st.markdown("---")

    # TAB DI LAVORO SU SCHEDA
    tab_note, tab_report, tab_prompt = st.tabs([
        "✏️ Note, Workflow & Pitch", 
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
        
        critiche_attive = []
        # Area Tecnica
        if chk_https: critiche_attive.append("- Mancanza di un protocollo HTTPS/SSL sicuro.")
        if chk_403: critiche_attive.append("- Presenza di restrizioni o errori HTTP (es. 403) che bloccano l'indicizzazione.")
        if chk_title: critiche_attive.append("- Tag Title assente o non ottimizzato.")
        if chk_desc: critiche_attive.append("- Assenza di Meta Description.")
        if chk_h1: critiche_attive.append("- Assenza della gerarchia con tag H1 principale.")
        if chk_sitemap: critiche_attive.append("- Sitemap XML non rilevata.")
        if chk_robots: critiche_attive.append("- File Robots.txt assente o errato.")
        if chk_speed: critiche_attive.append("- Tempi di risposta del server elevati.")
        if chk_mobile: critiche_attive.append("- Ottimizzazione mobile non corretta.")
        if chk_hreflang: critiche_attive.append("- Tag Hreflang non corretti o mancanti.")
        # Area UX/UI
        if chk_nav: critiche_attive.append("- Navigazione del sito non chiara.")
        if chk_cta: critiche_attive.append("- Call to Action (CTA) non visibili o coerenti.")
        if chk_form: critiche_attive.append("- Form di contatto troppo lunghi o macchinosi.")
        if chk_pop: critiche_attive.append("- Presenza di elementi invasivi (popup aggressivi).")
        if chk_brand: critiche_attive.append("- Non coerenza visiva e di brand.")
        if chk_bread: critiche_attive.append("- Assenza di breadcrumbs di navigazione.")
        # Area Contenuti & GEO
        if chk_eeat: critiche_attive.append("- Assenza di contenuti originali e segnali E-E-A-T.")
        if chk_faq: critiche_attive.append("- Assenza di una sezione FAQ.")
        if chk_blog: critiche_attive.append("- Assenza di una sezione Blog o News.")
        if chk_nap: critiche_attive.append("- Non coerenza NAP (Nome, Indirizzo, Telefono).")
        # Area Legale & Amministrativa
        if chk_piva: critiche_attive.append("- Assenza Partita IVA / Dati societari in chiaro.")
        if chk_gdpr: critiche_attive.append("- Assenza o inadeguatezza della GDPR Privacy Policy.")
        if chk_cookielaw: critiche_attive.append("- Assenza conformità Cookie Law.")
        if chk_banner: critiche_attive.append("- Assenza di un Cookie Banner conforme (blocco preventivo).")
        if chk_srl: critiche_attive.append("- Assenza informative societarie obbligatorie per SRL/SPA.")

        testo_critiche_automatico = "\n".join(critiche_attive) if critiche_attive else "Nessuna criticità di base rilevata."

        note_sintesi = st.text_area(
            "📝 Note / Criticità SEO (Auto-compilate dai checkbox):",
            value=testo_critiche_automatico,
            height=120
        )
        
        if st.button("💾 Salva Dettagli Lead", type="primary"):
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
        st.info("💡 **Nota:** Se usi già il tuo **Custom GPT dedicato**, puoi ignorare questo tab.")
        
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

Analizzando la presenza digitale del Vostro sito ({sito_url}), abbiamo riscontrato alcune aree di miglioramento strategico:
{note_sintesi}

Questo divario digitale potrebbe limitare le Vostre opportunità commerciali sui motori di ricerca rispetto ai vostri competitor.

Abbiamo elaborato un audit preliminare di posizionamento SEO, conformità e visibilità B2B specifica per il Vostro settore.
"""

    st.text_area("Copia Testo Mail:", value=pitch_mail, height=180)