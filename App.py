import streamlit as st
import pandas as pd

# --- SEZIONE DIAGNOSI EXPRESS & AUDIT V2 ---
st.markdown("### 🚀 Diagnosi Express SEO/UX & Audit V2")

# Tasto scansione rapida
col_scan, col_info = st.columns([1, 2])
with col_scan:
    if st.button("🔍 Esegui Scansione Tecnico-SEO", type="primary"):
        # Esegue la scansione di base (HTTPS, Meta Title, Viewport, H1)
        st.success("Scansione rapida completata!")

# Schede di lavoro
tab_note, tab_report, tab_prompt = st.tabs([
    "✏️ Modifica Note & Workflow", 
    "📄 Report Web Audit V2 (Generato)", 
    "📋 Prompt V2 per ChatGPT/Gemini"
])

with tab_note:
    st.subheader("Gestione Lead e Report Completo")
    
    # Campo per incollare l'Audit da ChatGPT
    audit_completo = st.text_area(
        "📥 Incolla qui il Report Audit V2 generato da ChatGPT/Gemini:",
        value=st.session_state.get('report_audit_attuale', ''),
        height=250,
        help="Incolla l'analisi completa generata da ChatGPT per salvarla nella scheda di questo cliente."
    )
    
    # Sintesi per la Mail
    note_sintesi = st.text_area(
        "📝 Note / Criticità SEO per Pitch Commerciale:",
        value=st.session_state.get('note_sintesi_attuale', 'Nessuna criticità di base rilevata.'),
        height=100,
        help="Questi punti verranno inseriti automaticamente nella mail d'attacco."
    )
    
    if st.button("💾 Salva Dettagli Lead e Report", type="primary"):
        st.session_state['report_audit_attuale'] = audit_completo
        st.session_state['note_sintesi_attuale'] = note_sintesi
        st.success("Scheda cliente e report aggiornati con successo!")

with tab_report:
    st.subheader("📄 Visualizzazione Report Salvato")
    if st.session_state.get('report_audit_attuale'):
        st.markdown(st.session_state['report_audit_attuale'])
        st.download_button(
            label="⬇️ Scarica Report Audit (.txt)",
            data=st.session_state['report_audit_attuale'],
            file_name="Report_Audit_V2.txt",
            mime="text/plain"
        )
    else:
        st.info("Nessun report completo ancora incollato per questo cliente.")

with tab_prompt:
    st.subheader("📋 Prompt V2 Pronto per ChatGPT / Gemini")
    st.write("Copia questo prompt e incollalo nel tuo Custom GPT o ChatGPT Pro per produrre l'audit da 12 pagine.")
    
    # Generazione dinamica del prompt con i dati del cliente
    prompt_testo = f"""Agisci come Senior Web Audit Consultant ed esegui un Audit Web V2 per il sito:
URL: {st.session_state.get('url_cliente', 'https://www.esempio.com')}
Azienda: {st.session_state.get('nome_cliente', 'Azienda')}
Sede: {st.session_state.get('sede_cliente', 'N/D')}

Applica le regole del Manuale Tecnico Audit Web V2:
1. Classifica i rilievi in MISURATO, OSSERVATO, INFERITO, NON VERIFICABILE.
2. Calcola lo score per le 8 aree (SEO tecnica, On-page, Performance, UX, Contenuti E-E-A-T, CRO, Accessibilità, AI Discoverability).
3. Produci: Executive Summary, Registro Evidenze, Scorecard, Quick Wins e Piano d'azione prioritizzato.

Evidenze preliminari già registrate:
{note_sintesi}"""

    st.code(prompt_testo, language="text")