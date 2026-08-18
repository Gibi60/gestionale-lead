import streamlit as st
import pandas as pd
import urllib.request
import urllib.error
import ssl
import time
import re
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gestionale Lead & Web Audit V2", layout="wide", page_icon="🚀")

# --- GESTIONE DATI PERSISTENTI & MAPPATURA INTESTAZIONI ---
FILE_CSV = "Gestione_Lead_Locale.csv"

def load_data():
    if not os.path.exists(FILE_CSV):
        df = pd.DataFrame(columns=[
            'Ragione Sociale', 'Sito Web', 'Sede', 'Stato Workflow', 
            'Report Audit Completo', 'Note Audit Digitale', 'Score Opportunità (%)',
            'Chk_Https', 'Chk_Title', 'Chk_Desc', 'Chk_H1', 'Chk_Sitemap', 'Chk_Robots',
            'Chk_Nav', 'Chk_Cta', 'Chk_Form', 'Chk_Pop', 'Chk_Eeat', 'Chk_Faq', 'Chk_Nap',
            'Chk_Piva', 'Chk_Gdpr', 'Chk_Cookie'
        ])
        df.to_csv(FILE_CSV, index=False)
        return df
    
    try:
        # Tenta la lettura automatica del separatore
        df = pd.read_csv(FILE_CSV, sep=None, engine='python', on_bad_lines='skip')
    except Exception:
        try:
            # Fallback forzato sul punto e virgola
            df = pd.read_csv(FILE_CSV, sep=';', on_bad_lines='skip')
        except Exception:
            # Fallback estremo se il file è corrotto
            df = pd.DataFrame(columns=[
                'Ragione Sociale', 'Sito Web', 'Sede', 'Stato Workflow', 
                'Report Audit Completo', 'Note Audit Digitale', 'Score Opportunità (%)',
                'Chk_Https', 'Chk_Title', 'Chk_Desc', 'Chk_H1', 'Chk_Sitemap', 'Chk_Robots',
                'Chk_Nav', 'Chk_Cta', 'Chk_Form', 'Chk_Pop', 'Chk_Eeat', 'Chk_Faq', 'Chk_Nap',
                'Chk_Piva', 'Chk_Gdpr', 'Chk_Cookie'
            ])
            df.to_csv(FILE_CSV, index=False)
            return df

    # Pulizia nomi colonne
    df.columns = [str(col).strip() for col in df.columns]

    # Mappatura semantica delle colonne
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

    # Assicuriamo la presenza delle colonne chiave
    if 'Ragione Sociale' not in df.columns:
        df['Ragione Sociale'] = df.iloc[:, 0]
    if 'Sito Web' not in df.columns:
        df['Sito Web'] = 'N/D'
    if 'Sede' not in df.columns:
        df['Sede'] = 'N/D'

    # Inizializzazione colonne standard mancanti
    colonne_standard = [
        'Stato Workflow', 'Report Audit Completo', 'Note Audit Digitale', 'Score Opportunità (%)',
        'Chk_Https', 'Chk_Title', 'Chk_Desc', 'Chk_H1', 'Chk_Sitemap', 'Chk_Robots',
        'Chk_Nav', 'Chk_Cta', 'Chk_Form', 'Chk_Pop', 'Chk_Eeat', 'Chk_Faq', 'Chk_Nap',
        'Chk_Piva', 'Chk_Gdpr', 'Chk_Cookie'
    ]
    for col in colonne_standard:
        if col not in df.columns:
            df[col] = False if col.startswith('Chk_') else ''
            
    return df

def save_data(df):
    df.to_csv(FILE_CSV, index=False)

df_lead = load_data()

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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
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
            
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match and title_match.group(1).strip():
                risultati.append(f"📌 **Tag Title:** {title_match.group(1).strip()}")
            else:
                risultati.append("⚠️ **Tag Title:** MANCANTE o vuoto")
                criticita.append("❌ Assenza o errore nel Tag Title")
                
            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
            if desc_match and desc_match.group(1).strip():
                risultati.append(f"📝 **Meta Description:** Presente")
            else:
                risultati.append("⚠️ **Meta Description:** MANCANTE")
                criticita.append("❌ Assenza Meta Description")
                
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
            if h1_match:
                clean_h1 = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                risultati.append(f"🏷️ **Tag H1 Principale:** {clean_h1}")
            else:
                risultati.append("⚠️ **Tag H1 Principale:** MANCANTE")
                criticita.append("❌ Assenza Tag H1 principale")
                
    except urllib.error.HTTPError as e:
        risultati.append(f"⚠️ **Protezione Firewall o Errore HTTP {e.code}**")
        criticita.append(f"🔒 Errore HTTP {e.code}")
    except Exception:
        risultati.append(f"❌ **Impossibile raggiungere il sito** ({url_pulito}).")
        criticita.append("❌ Sito non raggiungibile o offline")
        
    return "\n\n".join(risultati), criticita

# --- INTERFACCIA ---
st.title("💼 Dashboard Gestionale Lead & Audit V2")

tab_panoramica, tab_scheda = st.tabs(["📊 Panoramica Database", "🏢 Scheda Dettaglio Lead & Audit V2"])

with tab_panoramica:
    st.subheader("📊 Tabella Generale Lead")
    st.dataframe(df_lead, use_container_width=True)

with tab_scheda:
    if df_lead.empty:
        st.warning("Il database è vuoto.")
    else:
        elenco_aziende = df_lead['Ragione Sociale'].dropna().unique().tolist()
        azienda_selezionata = st.selectbox("🎯 Seleziona Azienda:", elenco_aziende, key="sel_az")
        
        idx_row = df_lead[df_lead['Ragione Sociale'] == azienda_selezionata].index[0]
        lead_info = df_lead.loc[idx_row]
        
        sito_url = str(lead_info.get('Sito Web', 'N/D')).strip()
        sede_info = str(lead_info.get('Sede', 'N/D')).strip()
        
        st.markdown(f"### 🏢 Scheda Cliente: **{lead_info['Ragione Sociale']}**")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        col_info1.markdown(f"**Sito Web:** [{sito_url}]({sito_url if sito_url.startswith('http') else 'https://' + sito_url})" if sito_url != 'N/D' else "**Sito Web:** N/D")
        col_info2.markdown(f"**Sede:** {sede_info}")
        col_info3.markdown(f"**Stato Attuale:** `{lead_info.get('Stato Workflow', 'Importato')}`")
        
        st.markdown("---")
        
        # --- DIAGNOSI RAPIDA ---
        col_btn, col_res = st.columns([1, 2])
        with col_btn:
            st.write("### 🔍 Diagnosi Rapida")
            lancia_scansione = st.button("🚀 Esegui Scansione Tecnico-SEO Reale", type="primary")
            
        with col_res:
            if lancia_scansione:
                with st.spinner("Scansione del sito in corso..."):
                    report_scansione, lista_crit = scansione_seo_reale(sito_url)
                    st.session_state[f'ultimo_report_{azienda_selezionata}'] = report_scansione

            if f'ultimo_report_{azienda_selezionata}' in st.session_state:
                st.info(st.session_state[f'ultimo_report_{azienda_selezionata}'])

        st.markdown("---")
        
        # --- TAB INTERNE ---
        tab_note, tab_validazione, tab_report, tab_prompt = st.tabs([
            "✏️ Note & Workflow", "✅ Validazione Criticità", "📄 Report Audit", "📋 Prompt"
        ])
        
        with tab_note:
            stati_possibili = ["Importato", "In Analisi", "Audit Generato", "Contattato", "In Trattativa", "Vinto", "Perso"]
            stato_corrente = str(lead_info.get('Stato Workflow', 'Importato'))
            idx_stato = stati_possibili.index(stato_corrente) if stato_corrente in stati_possibili else 0
            
            stato_wf = st.selectbox("Stato Workflow:", stati_possibili, index=idx_stato)
            note_sintesi = st.text_area("Note SEO:", value=str(lead_info.get('Note Audit Digitale', '')), height=150)
            
            if st.button("💾 Salva Note & Stato"):
                df_lead.loc[idx_row, 'Note Audit Digitale'] = str(note_sintesi)
                df_lead.loc[idx_row, 'Stato Workflow'] = str(stato_wf)
                save_data(df_lead)
                st.success("Dati salvati nel file CSV!")

        with tab_validazione:
            st.write("#### ⚙️ 1. SEO Tecnica")
            c1, c2, c3 = st.columns(3)
            chk_https = c1.checkbox("HTTPS / SSL", value=bool(lead_info.get('Chk_Https', False)))
            chk_title = c1.checkbox("Tag Title", value=bool(lead_info.get('Chk_Title', False)))
            chk_desc = c2.checkbox("Meta Description", value=bool(lead_info.get('Chk_Desc', False)))
            chk_h1 = c2.checkbox("Tag H1", value=bool(lead_info.get('Chk_H1', False)))
            chk_sitemap = c3.checkbox("Sitemap.xml", value=bool(lead_info.get('Chk_Sitemap', False)))
            chk_robots = c3.checkbox("Robots.txt", value=bool(lead_info.get('Chk_Robots', False)))
            
            st.write("#### 🎨 2. UX / UI")
            u1, u2 = st.columns(2)
            chk_nav = u1.checkbox("Navigazione", value=bool(lead_info.get('Chk_Nav', False)))
            chk_cta = u1.checkbox("CTA", value=bool(lead_info.get('Chk_Cta', False)))
            chk_form = u2.checkbox("Form Contatti", value=bool(lead_info.get('Chk_Form', False)))
            chk_pop = u2.checkbox("Popup Invasivi", value=bool(lead_info.get('Chk_Pop', False)))

            st.write("#### ✍️ 3. Contenuti e GEO")
            g1, g2 = st.columns(2)
            chk_eeat = g1.checkbox("Contenuti EEAT", value=bool(lead_info.get('Chk_Eeat', False)))
            chk_faq = g1.checkbox("Sezione FAQ", value=bool(lead_info.get('Chk_Faq', False)))
            chk_nap = g2.checkbox("Coerenza NAP", value=bool(lead_info.get('Chk_Nap', False)))

            st.write("#### ⚖️ 4. Legali e Amministrativi")
            l1, l2 = st.columns(2)
            chk_piva = l1.checkbox("Partita IVA", value=bool(lead_info.get('Chk_Piva', False)))
            chk_gdpr = l1.checkbox("GDPR", value=bool(lead_info.get('Chk_Gdpr', False)))
            chk_cookie = l2.checkbox("Cookie Banner", value=bool(lead_info.get('Chk_Cookie', False)))

            if st.button("💾 Salva Validazione e Calcola Score"):
                df_lead.loc[idx_row, 'Chk_Https'] = bool(chk_https)
                df_lead.loc[idx_row, 'Chk_Title'] = bool(chk_title)
                df_lead.loc[idx_row, 'Chk_Desc'] = bool(chk_desc)
                df_lead.loc[idx_row, 'Chk_H1'] = bool(chk_h1)
                df_lead.loc[idx_row, 'Chk_Sitemap'] = bool(chk_sitemap)
                df_lead.loc[idx_row, 'Chk_Robots'] = bool(chk_robots)
                df_lead.loc[idx_row, 'Chk_Nav'] = bool(chk_nav)
                df_lead.loc[idx_row, 'Chk_Cta'] = bool(chk_cta)
                df_lead.loc[idx_row, 'Chk_Form'] = bool(chk_form)
                df_lead.loc[idx_row, 'Chk_Pop'] = bool(chk_pop)
                df_lead.loc[idx_row, 'Chk_Eeat'] = bool(chk_eeat)
                df_lead.loc[idx_row, 'Chk_Faq'] = bool(chk_faq)
                df_lead.loc[idx_row, 'Chk_Nap'] = bool(chk_nap)
                df_lead.loc[idx_row, 'Chk_Piva'] = bool(chk_piva)
                df_lead.loc[idx_row, 'Chk_Gdpr'] = bool(chk_gdpr)
                df_lead.loc[idx_row, 'Chk_Cookie'] = bool(chk_cookie)
                
                tot_check = sum([chk_https, chk_title, chk_desc, chk_h1, chk_sitemap, chk_robots, chk_nav, chk_cta, chk_form, chk_pop, chk_eeat, chk_faq, chk_nap, chk_piva, chk_gdpr, chk_cookie])
                score_calc = round((tot_check / 16) * 100)
                df_lead.loc[idx_row, 'Score Opportunità (%)'] = int(score_calc)
                
                save_data(df_lead)
                st.success(f"Validazione salvata con successo! Score opportunità calcolato: {score_calc}%")

        with tab_report:
            st.write("#### 📄 Report e Sintesi Audit")
            
            # --- UPLOADER FILE ---
            uploaded_file = st.file_uploader("📎 Carica file Audit (formati ammessi: TXT, MD):", type=["txt", "md"])
            
            testo_base = str(lead_info.get('Report Audit Completo', ''))
            # Pulizia preventiva in caso di campi vuoti riconosciuti come 'nan' da pandas
            if testo_base.lower() == 'nan':
                testo_base = ''
            
            # Se viene caricato un file, appendiamo il suo contenuto al testo esistente
            if uploaded_file is not None:
                string_data = uploaded_file.getvalue().decode("utf-8")
                st.info("File letto correttamente. Il contenuto è visibile qui sotto pronto per essere salvato.")
                # Unisce il testo già presente con il nuovo caricato
                testo_base = f"{testo_base}\n\n--- NUOVO AUDIT CARICATO ---\n{string_data}" if testo_base.strip() else string_data
            
            audit_completo = st.text_area("Testo Report / Sintesi:", value=testo_base, height=300)
            
            if st.button("💾 Salva Report Finale"):
                # Utilizziamo loc per evitare TypeError in fase di inserimento testo
                df_lead.loc[idx_row, 'Report Audit Completo'] = str(audit_completo)
                save_data(df_lead)
                st.success("Report e allegati testuali salvati nel database!")
                
        with tab_prompt:
            st.code(f"Agisci come consulente SEO ed esperto di digital marketing per l'azienda {lead_info['Ragione Sociale']} con sito {sito_url}. Analizza le criticità rilevate e prepara una strategia mirata alla lead generation.")