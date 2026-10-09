"""Data handling and bounded preliminary HTML audit. No Streamlit side effects."""
from __future__ import annotations
import csv, io, json, os, hashlib, tempfile, shutil, threading, socket, ipaddress, ssl, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

STATES = ['Importato', 'In Analisi', 'Audit Generato', 'Contattato', 'In Trattativa', 'Vinto', 'Perso']
OPTIONS = ['Non verificato', 'Nessuna criticità', 'Criticità', 'Non applicabile']
CHECKS = {
 'SEO tecnica': [('Chk_Https','HTTPS e certificato'),('Chk_Http403','Accessibilità HTTP / blocchi'),('Chk_Title','Title'),('Chk_Desc','Meta description'),('Chk_H1','H1'),('Chk_Sitemap','Sitemap'),('Chk_Robots','Robots.txt'),('Chk_Lat','Tempo risposta'),('Chk_Mobile','Esperienza mobile'),('Chk_Hreflang','Hreflang, se pertinente')],
 'Esperienza e conversione': [('Chk_Nav','Navigazione'),('Chk_Cta','Call to action'),('Chk_Form','Form di contatto'),('Chk_Pop','Elementi invasivi'),('Chk_Brand','Coerenza del brand'),('Chk_Bread','Breadcrumb, se utili'),('Chk_Trust','Prove e segnali di fiducia')],
 'Contenuti e presenza locale': [('Chk_Eeat','Contenuti originali e prove di competenza'),('Chk_Faq','Risposte alle domande dei clienti'),('Chk_Blog','Aggiornamento dei contenuti'),('Chk_Nap','Coerenza nome, indirizzo e telefono'),('Chk_Social','Collegamenti social / Google Business Profile')],
 'Verifiche informative da approfondire': [('Chk_Piva','Dati identificativi e fiscali'),('Chk_Gdpr','Informativa privacy'),('Chk_Cookie','Informazioni sui cookie'),('Chk_Banner','Gestione dei consensi, se necessaria'),('Chk_Srl','Informazioni societarie applicabili'),('Chk_Pec','Contatti amministrativi pertinenti')],
}
KEYS = [k for group in CHECKS.values() for k,_ in group]
EXTRA = ['Lead ID','Ragione Sociale','Sito Web','Sede','Stato Workflow','Report Audit Completo','Note Audit Digitale','Score Opportunità (%)','Checklist JSON','Scansioni JSON','Contatti JSON','Prossima Azione','Scadenza','Versione']
LOCK = threading.RLock()
class DataError(Exception): pass
class ConflictError(DataError): pass

def now(): return datetime.now(timezone.utc).isoformat()
def text(value): return '' if value is None or str(value).strip().lower() in ('nan','none','n/d') else str(value).strip()
def checklist(row):
 try: parsed=json.loads(row.get('Checklist JSON') or '{}')
 except (ValueError,TypeError): parsed={}
 if not isinstance(parsed,dict):parsed={}
 return {k:parsed.get(k) if parsed.get(k) in OPTIONS else ('Criticità' if text(row.get(k)).lower() in ('true','1','yes','si','sì') else 'Non verificato') for k in KEYS}
def history(row,key):
 try:
  value=json.loads(row.get(key) or '[]')
  return value if isinstance(value,list) else []
 except (ValueError,TypeError): return []
def metrics(values):
 applicable=[v for v in values.values() if v!='Non applicabile']; checked=[v for v in applicable if v!='Non verificato']; issues=checked.count('Criticità')
 return issues,len(checked),len(applicable),round(100*issues/len(checked)) if checked else None

def parse_csv(data:bytes):
 try:
  content=data.decode('utf-8-sig'); dialect=csv.Sniffer().sniff(content[:8192],delimiters=',;\t')
  reader=csv.DictReader(io.StringIO(content),dialect=dialect); names=reader.fieldnames
  if not names: raise DataError('CSV privo di intestazioni.')
  aliases={'azienda':'Ragione Sociale','ragione sociale':'Ragione Sociale','ragionesociale':'Ragione Sociale','nome':'Ragione Sociale','company':'Ragione Sociale','web':'Sito Web','sito':'Sito Web','sito web':'Sito Web','sitoweb':'Sito Web','url':'Sito Web','website':'Sito Web','dominio':'Sito Web','sede':'Sede','città':'Sede','citta':'Sede','location':'Sede'}
  columns=[aliases.get(n.strip().lower(),n.strip()) for n in names]
  if len(set(columns))!=len(columns): raise DataError('Intestazioni duplicate: controlla le colonne del CSV.')
  if 'Ragione Sociale' not in columns: raise DataError('Serve una colonna AZIENDA o Ragione Sociale.')
  result=[]; ids=set()
  for line,raw in enumerate(reader,2):
   if None in raw or any(v is None for v in raw.values()): raise DataError(f'Riga {line}: numero di campi non valido. Il file resta invariato.')
   row={columns[i]:text(raw[n]) for i,n in enumerate(names)}
   if not row['Ragione Sociale']: raise DataError(f'Riga {line}: nome azienda mancante.')
   # Stable ID for historical rows, including duplicate company names.
   row['Lead ID']=row.get('Lead ID') or str(uuid.uuid5(uuid.NAMESPACE_URL,f'{line}|{row["Ragione Sociale"]}|{row.get("Sito Web","")}'))
   if row['Lead ID'] in ids: raise DataError(f'Riga {line}: Lead ID duplicato.')
   ids.add(row['Lead ID'])
   for key in EXTRA+KEYS: row.setdefault(key,'')
   row['Stato Workflow']=row['Stato Workflow'] if row['Stato Workflow'] in STATES else 'Importato'
   row['Versione']=row['Versione'] or '0'
   if not row['Versione'].isdigit():raise DataError(f'Riga {line}: versione della scheda non valida.')
   result.append(row)
  return result
 except (UnicodeError,csv.Error) as exc: raise DataError('CSV non leggibile: usa UTF-8 e separatore virgola o punto e virgola.') from exc

def encode_csv(rows,spreadsheet_safe=False):
 columns=list(dict.fromkeys(EXTRA+KEYS+[k for row in rows for k in row])); out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=columns);writer.writeheader()
 for row in rows:
  values={k:str(row.get(k,'')) for k in columns}
  if spreadsheet_safe: values={k:("'"+v if v.startswith(('=','+','-','@')) else v) for k,v in values.items()}
  writer.writerow(values)
 return out.getvalue().encode('utf-8-sig')

class Store:
 def __init__(self,path): self.path=Path(path)
 def read(self):
  if not self.path.exists(): return []
  return parse_csv(self.path.read_bytes())
 def _write(self,rows):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  if self.path.exists():
   backup=self.path.parent/'backups';backup.mkdir(exist_ok=True);shutil.copy2(self.path,backup/f'lead-{time.time_ns()}.csv')
   for p in sorted(backup.glob('lead-*.csv'))[:-20]:p.unlink()
  temp=None
  try:
   with tempfile.NamedTemporaryFile(dir=self.path.parent,delete=False) as f:
    temp=f.name;f.write(encode_csv(rows));f.flush();os.fsync(f.fileno())
   os.replace(temp,self.path);temp=None
  finally:
   if temp and os.path.exists(temp):os.unlink(temp)
 def update(self,lead_id,changes,expected):
  with LOCK:
   rows=self.read();row=next((r for r in rows if r['Lead ID']==lead_id),None)
   if row is None:raise DataError('Lead non trovato.')
   if row['Versione']!=str(expected):raise ConflictError('Il lead è stato modificato in un’altra sessione. Ricarica la scheda prima di salvare.')
   row.update({k:str(v) for k,v in changes.items() if k not in ('Lead ID','Versione')});row['Versione']=str(int(row['Versione'])+1);self._write(rows);return row
 def add(self,values):
  with LOCK:
   rows=self.read(); row={k:'' for k in EXTRA+KEYS};row.update(values);row['Ragione Sociale']=text(row['Ragione Sociale'])
   if not row['Ragione Sociale']:raise DataError('Inserisci il nome azienda.')
   row['Lead ID']=str(uuid.uuid4());row['Versione']='0';row['Stato Workflow']='Importato';rows.append(row);self._write(rows);return row
 def import_new(self,incoming):
  with LOCK:
   rows=self.read(); identities={(r['Ragione Sociale'].casefold(),r['Sito Web'].casefold()) for r in rows};added=0
   for source in incoming:
    identity=(source['Ragione Sociale'].casefold(),source['Sito Web'].casefold())
    if identity in identities:continue
    row=dict(source);row['Lead ID']=str(uuid.uuid4());row['Versione']='0';rows.append(row);identities.add(identity);added+=1
   if added:self._write(rows)
   return added

def public_url(raw):
 value=text(raw)
 if not value:raise ValueError('URL mancante.')
 if '://' not in value:value='https://'+value
 parts=urlsplit(value)
 if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password:raise ValueError('Usa un URL web http o https senza credenziali.')
 if parts.port not in (None,80,443):raise ValueError('Sono consentite solo le porte web 80 e 443.')
 ips=socket.getaddrinfo(parts.hostname,parts.port or (443 if parts.scheme=='https' else 80),type=socket.SOCK_STREAM)
 if not ips or any(not ipaddress.ip_address(x[4][0]).is_global for x in ips):raise ValueError('Indirizzo locale o riservato non consentito.')
 return urlunsplit((parts.scheme,parts.netloc,parts.path or '/',parts.query,''))
class PublicRedirect(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  return super().redirect_request(req,fp,code,msg,headers,public_url(newurl))

def parse_html(html):
 soup=BeautifulSoup(html,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else '';desc=soup.find('meta',attrs={'name':lambda v:v and v.lower()=='description'});headings=[x.get_text(' ',strip=True) for x in soup.find_all('h1')]
 return {'title':title,'description':text(desc.get('content')) if desc else '', 'h1':headings}
def scan(raw):
 result={'date':now(),'requested':text(raw),'observations':{},'checks':{},'error':'','limitations':'Controllo preliminare del solo HTML della pagina richiesta. Non esegue JavaScript, non misura Core Web Vitals, non valuta mobile, sitemap, privacy o qualità della strategia.'}
 try:
  url=public_url(raw);start=time.monotonic();opener=build_opener(HTTPSHandler(context=ssl.create_default_context()),PublicRedirect());req=Request(url,headers={'User-Agent':'GDP-Lead-Audit/3.0','Accept':'text/html'})
  with opener.open(req,timeout=10) as response:
   result['final_url']=response.url;result['status']=response.status;result['headers_seconds']=round(time.monotonic()-start,2)
   kind=response.headers.get_content_type()
   if kind not in ('text/html','application/xhtml+xml'):raise ValueError('La risposta non è una pagina HTML.')
   data=response.read(2*1024*1024+1)
   if len(data)>2*1024*1024:raise ValueError('Pagina oltre il limite di 2 MB: audit non completato.')
   html=data.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')
  observations=parse_html(html);result['observations']=observations
  result['checks']={k:('Nessuna criticità' if observations[field] else 'Criticità') for k,field in [('Chk_Title','title'),('Chk_Desc','description'),('Chk_H1','h1')]}
  result['checks']['Chk_Http403']='Nessuna criticità'
  result['checks']['Chk_Https']='Nessuna criticità' if urlsplit(result['final_url']).scheme=='https' else 'Criticità'
 except HTTPError as exc:result['status']=exc.code;result['error']=f'Risposta HTTP {exc.code}. Il blocco del nostro controllo non dimostra che il sito sia offline.'
 except (ValueError,URLError,OSError,ssl.SSLError) as exc:result['error']=f'Controllo non completato: {exc}'
 return result

def report_markdown(row):
 issues,done,total,score=metrics(checklist(row)); lines=[f'# {row["Ragione Sociale"]}',f'Sito: {row["Sito Web"]}',f'Stato: {row["Stato Workflow"]}',f'Checklist: {done}/{total} verifiche applicabili; {issues} criticità.',f'Indice criticità: {score if score is not None else "non calcolabile"}%. Non è una probabilità di vendita.','## Note',row['Note Audit Digitale'],'## Prossima azione',row['Prossima Azione'],f'Scadenza: {row["Scadenza"]}','## Report',row['Report Audit Completo'],'## Checklist']
 values=checklist(row)
 for group,checks in CHECKS.items():
  lines.append('### '+group)
  lines.extend(f'- {label}: {values[key]}' for key,label in checks)
 lines.append('## Scansioni preliminari')
 for item in history(row,'Scansioni JSON'):
  lines.extend([f'### {item.get("date","")}',json.dumps(item,ensure_ascii=False,indent=2)])
 return '\n\n'.join(lines)
