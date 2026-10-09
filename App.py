from pathlib import Path
import os, json, html, datetime
import pandas as pd
import streamlit as st
from lead_core import Store,DataError,STATES,OPTIONS,CHECKS,KEYS,checklist,metrics,history,now,parse_csv,encode_csv,scan,report_markdown

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Lead & Audit · Gilberto Del Pizzo',page_icon='📋',layout='wide')
store=Store(os.environ.get('GDP_LEAD_FILE',str(ROOT/'Gestione_Lead_Locale.csv')))
st.markdown('''<style>
.stApp{background:#f7f7f4;color:#202530}h1{letter-spacing:-1.4px!important}h2,h3{letter-spacing:-.5px!important}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e4e4df}
[data-testid="stMetric"]{background:#fff;padding:20px 24px;border:1px solid #e5e5df;border-radius:14px}
[data-testid="stMetricLabel"]{color:#7c8189}[data-testid="stMetricValue"]{color:#b94b1d}
.stButton button[kind="primary"]{background:#b94b1d;border-color:#b94b1d;border-radius:8px}
.stTabs [data-baseweb="tab-list"]{gap:20px}.stTabs [aria-selected="true"]{color:#b94b1d}
.gdp-kicker{color:#b94b1d;letter-spacing:2px;font-size:11px;font-weight:700}.gdp-subtitle{color:#7d838b;font-size:15px;margin-bottom:28px}
.lead-banner{padding:24px 27px;background:#fff;border:1px solid #e3e3dc;border-left:4px solid #b94b1d;border-radius:12px;margin:20px 0}
.lead-banner h2{margin:0 0 8px}.lead-banner p{color:#737b83;margin:0}.gdp-pill{display:inline-block;background:#faeee4;color:#9b4b23;padding:4px 10px;border-radius:5px;font-size:12px;margin-left:12px}
</style>''',unsafe_allow_html=True)
with st.sidebar:
 if (ROOT/'assets/logo-gdp.png').exists():st.image(str(ROOT/'assets/logo-gdp.png'),width=90)
 st.subheader('Gilberto Del Pizzo')
 st.caption('LEAD · AUDIT · PROSSIMI PASSI')
 st.divider()
 page=st.radio('Navigazione',['Panoramica','Scheda lead','Importa ed esporta','Guida'],label_visibility='collapsed')
 st.divider()
 st.caption('I file locali di Streamlit Cloud non garantiscono conservazione dopo riavvii o ridistribuzioni. Esporta periodicamente l’archivio completo.')
 st.caption('Uso personale: limita l’accesso dall’amministrazione Streamlit. Il login dell’amministratore non protegge automaticamente questa app.')
 st.caption('Versione 3.0')
try: rows=store.read()
except DataError as exc:
 st.error(str(exc));st.info('Il file originale non è stato sovrascritto. Correggi il CSV o ripristina una copia verificata.');st.stop()
if 'flash' in st.session_state:st.success(st.session_state.pop('flash'))
st.markdown('<div class="gdp-kicker">IL TUO SPAZIO COMMERCIALE</div>',unsafe_allow_html=True)
st.title('Lead & Audit')
st.markdown('<div class="gdp-subtitle">Conosci le aziende. Documenta le verifiche. Scegli il prossimo passo.</div>',unsafe_allow_html=True)

def save(row,changes):
 try:store.update(row['Lead ID'],changes,row['Versione']);st.session_state['flash']='Dati salvati. La versione precedente è conservata nei backup locali.';st.rerun()
 except DataError as exc:st.error(str(exc))
def render_scan(result):
 st.caption('Controllo del '+result.get('date',''))
 if result.get('error'):st.warning(result['error'])
 if result.get('final_url'):st.write('URL finale:',result['final_url'])
 if result.get('status'):st.write('Risposta HTTP:',result['status'])
 if result.get('headers_seconds') is not None:st.write('Tempo fino agli header:',str(result['headers_seconds'])+' s · non è il tempo completo di caricamento')
 obs=result.get('observations',{})
 if obs:
  st.write('**Title:**',obs.get('title') or 'Non trovato nell’HTML')
  st.write('**Description:**',obs.get('description') or 'Non trovata nell’HTML')
  st.write('**H1:**', ' | '.join(obs.get('h1',[])) or 'Non trovato nell’HTML')
 st.caption(result.get('limitations',''))

if page=='Panoramica':
 columns=st.columns(4)
 columns[0].metric('Aziende',len(rows));columns[1].metric('Da analizzare',sum(r['Stato Workflow'] in ('Importato','In Analisi') for r in rows));columns[2].metric('In trattativa',sum(r['Stato Workflow']=='In Trattativa' for r in rows));columns[3].metric('Clienti acquisiti',sum(r['Stato Workflow']=='Vinto' for r in rows))
 st.subheader('Il tuo elenco di lavoro')
 left,middle,right=st.columns([2,1,1]);q=left.text_input('Cerca azienda, sito o sede',placeholder='Scrivi un nome o una località…');state=middle.selectbox('Stato',['Tutti']+STATES);city=right.selectbox('Sede',['Tutte']+sorted({r['Sede'] for r in rows if r['Sede']}))
 filtered=[r for r in rows if (state=='Tutti' or r['Stato Workflow']==state) and (city=='Tutte' or r['Sede']==city) and q.casefold() in ' '.join([r['Ragione Sociale'],r['Sito Web'],r['Sede']]).casefold()]
 columns=['Ragione Sociale','Sede','Sito Web','Stato Workflow','Prossima Azione','Scadenza','Score Opportunità (%)']
 table=pd.DataFrame(filtered,columns=columns).rename(columns={'Score Opportunità (%)':'Indice criticità (%)'})
 st.dataframe(table,hide_index=True,width='stretch')
 st.caption(f'{len(filtered)} aziende visualizzate. L’indice usa soltanto i controlli verificati; i vecchi score restano provvisori fino al nuovo salvataggio della checklist.')
 with st.expander('Aggiungi un nuovo lead'):
  with st.form('new_lead',clear_on_submit=True):
   company=st.text_input('Ragione sociale *');url=st.text_input('Sito web');location=st.text_input('Sede');email=st.text_input('Email');phone=st.text_input('Telefono')
   if st.form_submit_button('Aggiungi azienda',type='primary'):
    try:store.add({'Ragione Sociale':company,'Sito Web':url,'Sede':location,'MAIL':email,'Telefono':phone});st.session_state['flash']='Nuova azienda inserita.';st.rerun()
    except DataError as exc:st.error(str(exc))
elif page=='Scheda lead':
 if not rows:st.info('Nessuna azienda. Inserisci un lead dalla Panoramica o importa un CSV.');st.stop()
 ids=[r['Lead ID'] for r in rows];by_id={r['Lead ID']:r for r in rows}
 selected=st.selectbox('Seleziona azienda',ids,format_func=lambda v:f'{by_id[v]["Ragione Sociale"]} · {by_id[v]["Sede"] or "Sede non indicata"} · {v[:6]}')
 row=by_id[selected];values=checklist(row);issues,done,total,score=metrics(values)
 st.markdown(f'<div class="lead-banner"><h2>{html.escape(row["Ragione Sociale"])}<span class="gdp-pill">{html.escape(row["Stato Workflow"])}</span></h2><p>{html.escape(row["Sede"] or "Sede non indicata")} · {html.escape(row["Sito Web"] or "Sito non indicato")}</p></div>',unsafe_allow_html=True)
 details=st.columns(3);details[0].write('**Email:** '+row.get('MAIL',row.get('Email','')));details[1].write('**Telefono:** '+row.get('Telefono',''));details[2].write('**Prossima azione:** '+(row['Prossima Azione'] or 'Da definire'))
 tabs=st.tabs(['Note e contatti','Audit preliminare','Checklist','Report e allegati','Anagrafica'])
 with tabs[0]:
  with st.form('workflow_'+selected):
   status=st.selectbox('Stato del lead',STATES,index=STATES.index(row['Stato Workflow']));notes=st.text_area('Note e valutazione',row['Note Audit Digitale'],height=150);action=st.text_input('Prossima azione',row['Prossima Azione']);deadline=st.text_input('Scadenza (AAAA-MM-GG)',row['Scadenza'],placeholder='2026-10-20')
   if st.form_submit_button('Salva note e prossimo passo',type='primary'):
    try:
     if deadline:datetime.date.fromisoformat(deadline)
     save(row,{'Stato Workflow':status,'Note Audit Digitale':notes,'Prossima Azione':action,'Scadenza':deadline})
    except ValueError:st.error('Scrivi una data valida nel formato AAAA-MM-GG, oppure lascia vuoto.')
  st.subheader('Storico dei contatti')
  contacts=history(row,'Contatti JSON')
  for event in reversed(contacts):
   with st.expander(event.get('date','')[:10]+' · '+event.get('channel','')):st.write(event.get('note',''))
  with st.form('contact_'+selected,clear_on_submit=True):
   channel=st.selectbox('Tipo di contatto',['Telefonata','Email','Incontro','Altro']);contact=st.text_area('Esito e appunti')
   if st.form_submit_button('Registra contatto'):
    if not contact.strip():st.error('Scrivi un esito prima di registrare il contatto.')
    else:save(row,{'Contatti JSON':json.dumps(contacts+[{'date':now(),'channel':channel,'note':contact.strip()}],ensure_ascii=False)})
 with tabs[1]:
  st.info('Controllo preliminare della pagina: HTTP, HTTPS verificato, title, description e H1. Non è un audit SEO completo.')
  if st.button('Esegui controllo preliminare',type='primary',disabled=not bool(row['Sito Web'])):
   with st.spinner('Controllo della pagina in corso…'):st.session_state['scan_'+selected]=scan(row['Sito Web'])
  result=st.session_state.get('scan_'+selected)
  if result:
   render_scan(result)
   if st.button('Conserva questa scansione nello storico'):
    scans=history(row,'Scansioni JSON')
    if any(x.get('date')==result.get('date') for x in scans):st.info('Questa scansione è già nello storico.')
    else:save(row,{'Scansioni JSON':json.dumps(scans+[result],ensure_ascii=False)})
   if result.get('checks') and st.button('Riporta i risultati automatici nella checklist'):
    new={**values,**result['checks']};count,checked,applicable,index=metrics(new);save(row,{'Checklist JSON':json.dumps(new,ensure_ascii=False),'Score Opportunità (%)':str(index) if index is not None else ''})
  scans=history(row,'Scansioni JSON')
  st.subheader('Scansioni conservate')
  if not scans:st.caption('Nessuna scansione salvata.')
  for item in reversed(scans):
   with st.expander(item.get('date','')+' · HTTP '+str(item.get('status','—'))):render_scan(item)
 with tabs[2]:
  a,b,c=st.columns(3);a.metric('Criticità accertate',issues);b.metric('Controlli verificati',f'{done}/{total}');c.metric('Indice criticità',f'{score}%' if score is not None else '—')
  st.progress(done/max(total,1));st.caption('Indice = criticità / controlli verificati applicabili. Non indica probabilità di vendita. L’assenza di blog, FAQ o breadcrumbs va valutata rispetto alle esigenze del sito.')
  with st.form('checklist_'+selected):
   new={}
   for group,checks in CHECKS.items():
    with st.expander(group,expanded=group=='SEO tecnica'):
     if group.startswith('Verifiche informative'):st.caption('Registrazione di verifiche da approfondire: non certifica conformità normativa.')
     for key,label in checks:new[key]=st.selectbox(label,OPTIONS,index=OPTIONS.index(values[key]),key=selected+'_'+key)
   if st.form_submit_button('Salva checklist e aggiorna indice',type='primary'):
    count,checked,applicable,index=metrics(new);changes={'Checklist JSON':json.dumps(new,ensure_ascii=False),'Score Opportunità (%)':str(index) if index is not None else ''};changes.update({key:str(value=='Criticità') for key,value in new.items()});save(row,changes)
 with tabs[3]:
  st.caption('Carica testi o documenti: il contenuto estratto si aggiunge al report soltanto dopo il salvataggio.')
  uploaded=st.file_uploader('Allega un audit',type=['txt','md','pdf','docx'],key='audit_'+selected)
  addition=''
  if uploaded:
   try:
    if uploaded.size>10*1024*1024:raise ValueError('Limite 10 MB per documento.')
    if uploaded.name.lower().endswith('.pdf'):
     from pypdf import PdfReader
     addition='\n'.join(p.extract_text() or '' for p in PdfReader(uploaded).pages)
    elif uploaded.name.lower().endswith('.docx'):
     from docx import Document
     addition='\n'.join(p.text for p in Document(uploaded).paragraphs)
    else:addition=uploaded.getvalue().decode('utf-8-sig')
    st.text_area('Anteprima del testo estratto',addition[:100000],height=150,disabled=True)
    if not addition.strip():st.warning('Nessun testo estratto. I PDF scansionati richiedono OCR e non sono supportati.')
   except Exception:st.error('Documento non leggibile o oltre 10 MB. Il report salvato resta invariato.')
  with st.form('report_'+selected):
   report=st.text_area('Report audit',row['Report Audit Completo'],height=300);append=st.checkbox('Aggiungi al report il testo del documento caricato',value=False)
   if st.form_submit_button('Salva report',type='primary'):
    if append and not addition.strip():st.error('Carica prima un documento leggibile.')
    else:save(row,{'Report Audit Completo':report+('\n\n--- '+uploaded.name+' ---\n'+addition if append else '')})
  st.download_button('Scarica la scheda e l’audit',report_markdown(row),file_name='scheda-lead-'+selected[:8]+'.md',mime='text/markdown')
  prompt=f'Avvia il Metodo Gilberto Del Pizzo per {row["Ragione Sociale"]}, sito {row["Sito Web"]}. Usa i dati allegati distinguendo verifiche accertate, ipotesi e informazioni mancanti. Non dedurre qualità, conformità o probabilità di vendita dalle sole caselle. Valido io le fasi.'
  with st.expander('Prompt per approfondire la strategia'):st.code(prompt,language=None)
 with tabs[4]:
  with st.form('company_'+selected):
   name=st.text_input('Ragione sociale',row['Ragione Sociale']);web=st.text_input('Sito web',row['Sito Web']);city=st.text_input('Sede',row['Sede']);email=st.text_input('Email',row.get('MAIL',''));phone=st.text_input('Telefono',row.get('Telefono',''))
   if st.form_submit_button('Salva anagrafica'):
    if not name.strip():st.error('Il nome azienda è obbligatorio.')
    else:save(row,{'Ragione Sociale':name.strip(),'Sito Web':web.strip(),'Sede':city.strip(),'MAIL':email.strip(),'Telefono':phone.strip()})
elif page=='Importa ed esporta':
 st.subheader('Conserva una copia del tuo lavoro')
 st.info('Archivio completo: conserva ID, versioni, note, checklist e storico. Scaricalo prima di aggiornare o riavviare l’app Cloud.')
 st.download_button('Scarica archivio completo · CSV',encode_csv(rows),file_name='gestionale-lead-backup.csv',mime='text/csv',type='primary')
 st.download_button('Scarica copia per foglio di calcolo',encode_csv(rows,spreadsheet_safe=True),file_name='gestionale-lead-tabella.csv',mime='text/csv')
 st.subheader('Importa nuove aziende')
 st.caption('Aggiunge solo le aziende non già presenti con lo stesso nome e sito. Non sovrascrive note o verifiche esistenti. Non è un ripristino completo di backup.')
 upload=st.file_uploader('CSV con AZIENDA o Ragione Sociale',type=['csv'])
 if upload:
  try:
   if upload.size>10*1024*1024:raise DataError('Il CSV supera 10 MB.')
   incoming=parse_csv(upload.getvalue());st.write(f'{len(incoming)} righe lette correttamente.');st.dataframe(pd.DataFrame(incoming)[['Ragione Sociale','Sito Web','Sede']],hide_index=True)
   if st.button('Conferma importazione'):
    added=store.import_new(incoming);st.session_state['flash']=f'Inserite {added} nuove aziende; quelle già presenti sono rimaste invariate.';st.rerun()
  except DataError as exc:st.error(str(exc))
else:
 st.markdown((ROOT/'GUIDA_USO.md').read_text(encoding='utf-8'))
 st.download_button('Scarica la guida d’uso',(ROOT/'GUIDA_USO.md').read_bytes(),file_name='Guida_Gestionale_Lead_v3.md',mime='text/markdown')
