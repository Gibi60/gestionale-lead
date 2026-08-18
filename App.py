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

# --- GESTIONE DATI PERSISTENTI (ROBUSTA) ---
FILE_CSV = "Gestione_Lead_Locale.csv"

def load_data():
    if not os.path.exists(FILE_CSV):
        df = pd.DataFrame(columns=['Ragione Sociale', 'Sito Web', 'Sede', 'Stato Workflow', 'Report Audit Completo', 'Note Audit Digitale', 'Score Opportunità (%)'])
        df.to_csv(FILE_CSV, index=False)
        return df
    
    # Prova a leggere il file gestendo automaticamente i separatori e gli errori di formattazione
    try:
        df = pd.read_csv(FILE_CSV, sep=None, engine='python', on_bad_lines='skip')
    except Exception:
        try:
            df = pd.read_csv(FILE_CSV, sep=';', on_bad_lines='skip')
        except Exception:
            # Se il file è totalmente illeggibile, ne ricrea uno pulito per evitare il crash
            df = pd.DataFrame(columns=['Ragione Sociale', 'Sito Web', 'Sede', 'Stato Workflow', 'Report Audit Completo', 'Note Audit Digitale', 'Score Opportunità (%)'])
            df.to_csv(FILE_CSV, index=False)
            
    # Pulisce i nomi delle colonne da spazi superflui
    df.columns = [str(col).strip() for col in df.columns]
    
    # Assicura la presenza di tutte le colonne necessarie
    colonne_necessarie = ['Ragione Sociale', 'Sito Web', 'Sede', 'Stato Workflow', 'Report Audit Completo', 'Note Audit Digitale', 'Score Opportunità (%)']
    for col in colonne_necessarie:
        if col not in df.columns:
            df[col] = ''
            
    return df

def save_data(df):
    df.to_csv(FILE_CSV, index=False)

df_lead = load_data()

# --- FUNZIONE SCANSIONE SEO REALE ---
def scansione_seo_reale(url):
    if not url or pd.isna(url) or str(url).strip() in ['', 'nan', 'N/D']:
        return "❌ Nessun URL valido specificato.", []
    
    url_pulito = str(url).strip() if url.startswith('http') else 'https://' + str(url).strip()
    risultati = []
    criticita = []
    start_time = time.time()
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url_pulito, headers=headers)
        with urllib.request.urlopen(req, timeout=8, context=ctx) as response:
            load_time = round(time.time() - start_time, 2)
            html = response.read().decode('utf-8', errors='ignore')
            risultati.append(f"✅ Sito raggiungibile in {load_time}s")
            if load_time > 2.5: criticita.append("⏱️ Tempo di risposta elevato")
            if not re.search(r'<title>(.*?)</title>', html, re.IGNORECASE): criticita.append("❌ Tag Title mancante")
            if not re.search(r'<h1[^>]*>', html, re.IGNORECASE): criticita.append("❌ Tag H1 mancante")
    except Exception:
        risultati.append("❌ Errore durante la scansione.")
        
    return "\n".join(risultati), criticita

# --- INTERFACCIA ---
st.title("💼 Dashboard Gestionale Lead & Audit V2")

tab_panoramica, tab_scheda = st.tabs(["📊 Panoramica Database", "🏢 Scheda Dettaglio Lead & Audit V2"])

with tab_panoramica:
    st.dataframe(df_lead, use_container_width=True)

with tab_scheda:
    if df_lead.empty:
        st.warning("Il database è vuoto. Carica o inserisci dei dati.")
    else:
        elenco_aziende = df_lead['Ragione Sociale'].dropna().unique().tolist()
        azienda_selezionata = st.selectbox("🎯 Seleziona Azienda:", elenco_aziende, key="sel_az")
        
        idx_row = df_lead.index[df_lead['Ragione Sociale'] == azienda_selezionata][0]
        lead_info = df_lead.loc[idx_row]
        
        st.markdown(f"### 🏢 {lead_info['Ragione Sociale']}")
        
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
                df_lead.at[idx_row, 'Note Audit Digitale'] = note_sintesi
                df_lead.at[idx_row, 'Stato Workflow'] = stato_wf
                save_data(df_lead)
                st.success("Dati salvati nel file CSV!")

        with tab_validazione:
            st.write("#### ⚙️ 1. SEO Tecnica")
            c1, c2, c3 = st.columns(3)
            chk_https = c1.checkbox("HTTPS / SSL", key="chk_https")
            chk_title = c1.checkbox("Tag Title", key="chk_title")
            chk_desc = c2.checkbox("Meta Description", key="chk_desc")
            chk_h1 = c2.checkbox("Tag H1", key="chk_h1")
            chk_sitemap = c3.checkbox("Sitemap.xml", key="chk_sitemap")
            chk_robots = c3.checkbox("Robots.txt", key="chk_robots")
            
            st.write("#### 🎨 2. UX / UI")
            u1, u2 = st.columns(2)
            chk_nav = u1.checkbox("Navigazione", key="chk_nav")
            chk_cta = u1.checkbox("CTA", key="chk_cta")
            chk_form = u2.checkbox("Form Contatti", key="chk_form")
            chk_pop = u2.checkbox("Popup Invasivi", key="chk_pop")

            st.write("#### ✍️ 3. Contenuti e GEO")
            g1, g2 = st.columns(2)
            chk_eeat = g1.checkbox("Contenuti EEAT", key="chk_eeat")
            chk_faq = g1.checkbox("Sezione FAQ", key="chk_faq")
            chk_nap = g2.checkbox("Coerenza NAP", key="chk_nap")

            st.write("#### ⚖️ 4. Legali e Amministrativi")
            l1, l2 = st.columns(2)
            chk_piva = l1.checkbox("Partita IVA", key="chk_piva")
            chk_gdpr = l1.checkbox("GDPR", key="chk_gdpr")
            chk_cookie = l2.checkbox("Cookie Banner", key="chk_cookie")

            if st.button("💾 Salva Validazione"):
                df_lead.at[idx_row, 'Score Opportunità (%)'] = 100
                save_data(df_lead)
                st.success("Validazione salvata!")

        with tab_report:
            audit_completo = st.text_area("Report:", value=str(lead_info.get('Report Audit Completo', '')), height=250)
            if st.button("💾 Salva Report"):
                df_lead.at[idx_row, 'Report Audit Completo'] = audit_completo
                save_data(df_lead)
                st.success("Report salvato!")
                
        with tab_prompt:
            st.code(f"Agisci come consulente SEO per {lead_info['Ragione Sociale']}...")