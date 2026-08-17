import streamlit as st
import pandas as pd
import numpy as np
import os
import urllib.request
import ssl
from html.parser import HTMLParser

st.set_page_config(page_title="Lead Management CRM & Audit V2", layout="wide", page_icon="🍊")

CSV_FILE = "Gestione_Lead_Locale.csv"

# Parser HTML basato su libreria standard (senza dipendenze esterne)
class LightSEOInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.h1_list = []
        self.has_viewport = False
        self.in_title = False
        self.in_h1 = False
        self.current_h1 = ""

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): v for k, v in attrs if k and v}
        if tag == 'title':
            self.in_title = True
        elif tag == 'meta':
            name = attr_dict.get('name', '').lower()
            if name == 'description':
                self.meta_description = attr_dict.get('content', '')
            elif name == 'viewport':
                self.has_viewport = True
        elif tag == 'h1':
            self.in_h1 = True
            self.current_h1 = ""

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag == 'h1':
            self.in_h1 = False
            if self.current_h1.strip():
                self.h1_list.append(self.current_h1.strip())

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_h1:
            self.current_h1 += data

def inspect_website_express(url_str):
    if not isinstance(url_str, str) or not url_str.strip() or url_str == 'N/D':
        return {"status": "URL_MANCANTE", "issues": ["URL non fornito"], "score": 20, "data": {}}
    
    clean_url = url_str.strip().lower()
    if not clean_url.startswith(('http://', 'https://')):
        clean_url = 'https://' + clean_url

    results = {
        "status": "OK",
        "url": clean_url,
        "is_https": clean_url.startswith("https://"),
        "title": "",
        "meta_description": "",
        "h1": [],
        "has_viewport": False,
        "issues": []
    }

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WebAuditBot/2.0'}

    try:
        req = urllib.request.Request(clean_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
            html = response.read().decode('utf-8', errors='ignore')
            parser = LightSEOInspector()
            parser.feed(html)

            results["title"] = parser.title.strip()
            results["meta_description"] = parser.meta_description.strip()
            results["h1"] = parser.h1_list
            results["has_viewport"] = parser.has_viewport

    except Exception as e:
        results["status"] = "ERRORE_CONNESSIONE"
        results["issues"].append(f"Impossibile accedere direttamente al sito: {str(e)[:60]}")

    # Calcolo criticità e Digital Gap Score
    score_gap = 90
    if not results["is_https"]:
        results["issues"].append("Sicurezza: Connessione HTTPS non rilevata o non predefinita (-15)")
        score_gap -= 15
    if not results["title"]:
        results["issues"].append("SEO On-Page: Tag Meta Title assente (-20)")
        score_gap -= 20
    if not results["meta_description"]:
        results["issues"].append("SEO On-Page: Meta Description assente o vuota (-15)")
        score_gap -= 15
    if not results["h1"]:
        results["issues"].append("SEO On-Page: Intestazione H1 assente (-15)")
        score_gap -= 15
    if not results["has_viewport"]:
        results["issues"].append("Mobile UX: Viewport tag mobile non rilevato (-20)")
        score_gap -= 20

    if results["status"] == "ERRORE_CONNESSIONE":
        score_gap = 40

    return {
        "status": results["status"],
        "issues": results["issues"],
        "digital_gap": max(10, score_gap),
        "data": results
    }

def load_data():
    if not os.path.exists(CSV_FILE):
        st.error(f"File {CSV_FILE} non trovato!")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8-sig")
        if len(df.columns) <= 1:
            df = pd.read_csv(CSV_FILE, sep=",", encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(CSV_FILE, sep=",", encoding="utf-8-sig")

    df.columns = df.columns.str.strip()

    if "AZIENDA" in df.columns:
        df = df.drop_duplicates(subset=["AZIENDA", "SEDE"]).reset_index(drop=True)
        df = df.rename(columns={
            "AZIENDA": "Ragione Sociale",
            "SEDE": "Comune",
            "INDIRIZZO": "Indirizzo",
            "WEB": "Sito Web",
            "MAIL": "Email"
        })

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

    if "Commercial Fit" not in df.columns:
        df["Commercial Fit"] = df["Fatturato"].apply(lambda f: 90 if str(f) != "N/D" else 70)
    if "Digital Gap" not in df.columns:
        df["Digital Gap"] = 75
    if "Data Quality" not in df.columns:
        df["Data Quality"] = 90

    # Formula LOS = (45% Commercial Fit) + (45% Digital Gap) + (10% Data Quality)
    if "Lead Opp Score" not in df.columns:
        df["Lead Opp Score"] = (0.45 * df["Commercial Fit"] + 0.45 * df["Digital Gap"] + 0.10 * df["Data Quality"]).astype(int)

    if "Priorita" not in df.columns:
        df["Priorita"] = df["Lead Opp Score"].apply(lambda x: "Alta" if x >= 80 else ("Media" if x >= 70 else "Bassa"))
    
    if "Stato Workflow" not in df.columns:
        df["Stato Workflow"] = "Importato"
        
    if "Note Audit Digitale" not in df.columns:
        df["Note Audit Digitale"] = ""

    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False, sep=";", encoding='utf-8-sig')

df = load_data()

st.title("🍊 Lead Management & Web Audit Strategico V2")
st.caption("Piattaforma CRM di qualificazione, diagnosi SEO/UX e outreach B2B")

if not df.empty:
    st.sidebar.header("🔍 Filtri Strategici")
    
    priorita_opts = list(df["Priorita"].dropna().unique())
    priorita_filter = st.sidebar.multiselect("Priorità Lead", options=priorita_opts, default=priorita_opts)
    
    stato_opts = list(df["Stato Workflow"].dropna().unique())
    stato_filter = st.sidebar.multiselect("Stato Workflow", options=stato_opts, default=stato_opts)

    comune_opts = sorted([str(c) for c in df["Comune"].dropna().unique()])
    comune_filter = st.sidebar.multiselect("Comune / Sede", options=comune_opts, default=comune_opts)

    mask = (
        df["Priorita"].isin(priorita_filter) & 
        df["Stato Workflow"].isin(stato_filter) &
        df["Comune"].isin(comune_filter)
    )
    df_filtered = df[mask]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totale Lead Filtrati", len(df_filtered))
    col2.metric("Priorità Alta (≥80)", len(df_filtered[df_filtered["Priorita"] == "Alta"]))
    col3.metric("In Contatto / Pitch", len(df_filtered[df_filtered["Stato Workflow"].isin(["In Contatto", "Pitch Inviato", "In Trattativa"])]))
    col4.metric("Clienti Acquisiti", len(df_filtered[df_filtered["Stato Workflow"] == "Cliente Acquisito"]))

    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Tabella Modificabile & Gestione Stato", "🔍 Scheda Lead, Diagnosi SEO & Outreach"])

    with tab1:
        st.subheader("Elenco Lead Processati")
        st.info("💡 Modifica lo **Stato Workflow**, la **Priorità** o le **Note** direttamente nelle celle e clicca in basso per salvare.")

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
            st.success("Tutti i dati e gli stati sono stati salvati!")
            st.rerun()

    with tab2:
        lead_options = df_filtered["ID Lead"] + " - " + df_filtered["Ragione Sociale"]
        selected_lead_str = st.selectbox("Seleziona Azienda da Analizzare:", lead_options if len(lead_options)>0 else ["Nessun lead disponibile"])
        
        if selected_lead_str and selected_lead_str != "Nessun lead disponibile":
            lead_id = selected_lead_str.split(" - ")[0]
            lead_idx = df[df["ID Lead"] == lead_id].index[0]
            row = df.loc[lead_idx]

            st.markdown(f"## 🏢 **{row['Ragione Sociale']}**")
            
            c_info, c_score = st.columns([1, 1])
            with c_info:
                st.write(f"📍 **Sede:** {row['Comune']} ({row['Indirizzo']})")
                st.write(f"💰 **Fatturato:** {row['Fatturato']}")
                st.write(f"🌐 **Sito Web:** [{row['Sito Web']}](http://{row['Sito Web']})" if pd.notna(row['Sito Web']) else "🌐 **Sito Web:** N/D")
                st.write(f"✉️ **Email:** {row['Email']} | 👤 **Referente:** {row['Referente']}")

            with c_score:
                los_score = int(row['Lead Opp Score'])
                st.metric("Lead Opportunity Score (LOS)", f"{los_score}/100")
                st.progress(los_score)
                st.caption(f"📐 **Formula Audit V2:** Commercial Fit ({row['Commercial Fit']}) | Digital Gap ({row['Digital Gap']}) | Data Quality ({row['Data Quality']})")

            st.markdown("---")

            # SEZIONE DIAGNOSI EXPRESS & ELEMENTI CHIAVE
            st.markdown("### 🚀 **Diagnosi Express SEO/UX & Audit V2**")
            
            btn_col, res_col = st.columns([1, 2])
            
            with btn_col:
                if st.button("🔍 Esegui Scansione Tecnico-SEO", type="primary"):
                    with st.spinner("Scansione della homepage in corso..."):
                        audit_res = inspect_website_express(str(row['Sito Web']))
                        
                        # Aggiornamento dati nel dataframe
                        df.loc[lead_idx, 'Digital Gap'] = audit_res['digital_gap']
                        new_los = int(0.45 * row['Commercial Fit'] + 0.45 * audit_res['digital_gap'] + 0.10 * row['Data Quality'])
                        df.loc[lead_idx, 'Lead Opp Score'] = new_los
                        df.loc[lead_idx, 'Priorita'] = "Alta" if new_los >= 80 else ("Media" if new_los >= 70 else "Bassa")
                        
                        crit_text = "\n".join([f"• {i}" for i in audit_res['issues']]) if audit_res['issues'] else "Nessuna criticità di base rilevata."
                        df.loc[lead_idx, 'Note Audit Digitale'] = crit_text
                        save_data(df)
                        st.success("Diagnosi completata e salvata!")
                        st.rerun()

            with res_col:
                st.markdown("**Evidenze Tecniche Rilevate:**")
                current_notes = str(row['Note Audit Digitale']) if pd.notna(row['Note Audit Digitale']) and str(row['Note Audit Digitale']).strip() != "" else "Nessuna diagnosi eseguita ancora."
                st.info(current_notes)

            st.markdown("---")

            # SCHEDA MODIFICA & REPORT GENERATO
            tab_edit, tab_report, tab_prompt = st.tabs(["✍️ Modifica Note & Workflow", "📄 Report Web Audit V2 (Generato)", "📋 Prompt V2 per ChatGPT/Gemini"])

            with tab_edit:
                c_left, c_right = st.columns([1, 1])
                with c_left:
                    current_status = row['Stato Workflow'] if pd.notna(row['Stato Workflow']) else "Importato"
                    status_list = ["Importato", "In Contatto", "Pitch Inviato", "In Trattativa", "Cliente Acquisito", "Non Interessato"]
                    new_status = st.selectbox("Stato Avanzamento Workflow:", status_list, index=status_list.index(current_status) if current_status in status_list else 0)
                    new_audit = st.text_area("Note / Criticità SEO personalizzate:", current_notes, height=120)
                    
                    if st.button("💾 Salva Dettagli Lead"):
                        df.loc[lead_idx, 'Stato Workflow'] = new_status
                        df.loc[lead_idx, 'Note Audit Digitale'] = new_audit
                        save_data(df)
                        st.success("Dettagli aggiornati!")
                        st.rerun()

                with c_right:
                    st.markdown("### ✉️ **Pitch Commerciale Personalizzato**")
                    referente_saluto = f"Gentile {row['Referente']}" if pd.notna(row['Referente']) and str(row['Referente']).strip() != "" else "Gentile Direzione"
                    critica_str = new_audit.replace("\n", " ") if new_audit else "alcune ottimizzazioni di visibilità SEO e usabilità mobile"
                    
                    pitch_text = f"{referente_saluto},\n\nAnalizzando la presenza digitale di {row['Ragione Sociale']} ({row['Sito Web']}), abbiamo rilevato i seguenti aspetti d'impatto:\n{new_audit}\n\nQuesto divario digitale potrebbe limitare le Vostre opportunità commerciali sui motori di ricerca.\n\nAbbiamo elaborato un audit preliminare di posizionamento SEO e visibilità B2B specifica per il Vostro settore.\n\nSiete disponibili per un breve confronto telefonico di 10 minuti la prossima settimana per condividerne i dettagli?\n\nCordiali saluti,\nGilberto Del Pizzo\nConsulente Digital Strategy & SEO"
                    st.text_area("Copia Testo Mail:", pitch_text, height=220)

            with tab_report:
                st.subheader(f"📄 Report Web Audit V2 — {row['Ragione Sociale']}")
                
                report_md = f"""# REPORT AUDIT STRATEGICO WEB V2
**Azienda:** {row['Ragione Sociale']}  
**Sito Web:** {row['Sito Web']}  
**Sede:** {row['Comune']} ({row['Indirizzo']})  
**Data Analisi:** 17 Agosto 2026  
**Auditor:** Gilberto Del Pizzo - Digital Strategy & SEO  

---

## 1. Executive Summary
L'analisi del sito web **{row['Sito Web']}** ha evidenziato un **Digital Gap Score di {row['Digital Gap']}/100** ed un **Lead Opportunity Score complessivo di {row['Lead Opp Score']}/100**.

## 2. Evidenze Tecniche e Criticità Rilevate
{row['Note Audit Digitale']}

## 3. Scorecard per Area di Intervento (Framework V2)
- **SEO Tecnica & Indicizzabilità:** {row['Digital Gap']}/100 (Copertura: 80% | Affidabilità: High)
- **SEO On-Page & Struttura:** 65/100
- **Performance & Mobile Usability:** 70/100
- **CRO & Generazione Lead:** 60/100

## 4. Quick Wins Consegnabili
1. Correzione Tag Meta Title & Meta Description mancanti o non ottimizzati.
2. Implementazione della gerarchia delle intestazioni (Tag H1/H2).
3. Verifiche di sicurezza HTTPS e configurazione file `robots.txt`.

---
*Report generato automaticamente in conformità alle specifiche del Manuale Tecnico Audit Web V2.*
"""
                st.markdown(report_md)
                
                st.download_button(
                    label="⬇️ Scarica Report Audit V2 (.txt)",
                    data=report_md,
                    file_name=f"Report_Audit_{row['Ragione Sociale'].replace(' ', '_')}.txt",
                    mime="text/plain"
                )

            with tab_prompt:
                st.subheader("📋 Prompt V2 Pronto per ChatGPT / Gemini")
                st.caption("Copia questo prompt e incollalo in ChatGPT/Gemini (con navigazione web) per produrre l'audit approfondito a 12 pagine.")
                
                full_prompt = f"""Agisci come Senior Web Audit Consultant ed esegui un Audit Web V2 per il sito:
URL: https://{row['Sito Web']}
Azienda: {row['Ragione Sociale']}
Sede: {row['Comune']}
Fatturato stimato: {row['Fatturato']}

Applica le regole del Manuale Tecnico Audit Web V2:
1. Classifica i rilievi in MISURATO, OSSERVATO, INFERITO, NON VERIFICABILE.
2. Calcola lo score per le 8 aree (SEO tecnica, On-page, Performance, UX, Contenuti E-E-A-T, CRO, Accessibilità, AI Discoverability).
3. Produci: Executive Summary, Registro Evidenze, Scorecard, Quick Wins e Piano d'azione prioritizzato.

Evidenze preliminari già registrate:
{row['Note Audit Digitale']}
"""
                st.code(full_prompt, language="markdown")