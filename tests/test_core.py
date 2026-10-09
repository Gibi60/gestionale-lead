import json,ssl
import pytest
from lead_core import Store,DataError,ConflictError,parse_csv,encode_csv,checklist,metrics,parse_html,scan,public_url

def test_migration_and_roundtrip():
 data='AZIENDA;SEDE;WEB\nA;Udine;a.com\nA;Trieste;b.com\n'.encode('utf-8-sig');r=parse_csv(data)
 assert len(r)==2 and r[0]['Stato Workflow']=='Importato' and r[0]['Lead ID']!=r[1]['Lead ID'];assert r==parse_csv(data)
 r[0]['Report Audit Completo']='testo\ncon , e ;';assert parse_csv(encode_csv(r))==r

def test_malformed_never_overwrites(tmp_path):
 p=tmp_path/'data.csv';p.write_text('AZIENDA;WEB\nA;site;extra\n');before=p.read_bytes()
 with pytest.raises(DataError):Store(p).read()
 assert p.read_bytes()==before

def test_save_conflicts_backup_and_import(tmp_path):
 p=tmp_path/'data.csv';p.write_text('AZIENDA;WEB\nA;a.com\nB;b.com\n');s=Store(p);old=s.read();a=old[0];s.update(a['Lead ID'],{'Note Audit Digitale':'keep'},0)
 assert s.read()[0]['Note Audit Digitale']=='keep' and s.read()[1]==old[1]
 assert len(list((tmp_path/'backups').glob('*.csv')))==1
 with pytest.raises(ConflictError):s.update(a['Lead ID'],{'Note Audit Digitale':'perso'},0)
 assert s.import_new(parse_csv(b'AZIENDA;WEB\nA;a.com\nC;c.com\n'))==1
 assert s.read()[0]['Note Audit Digitale']=='keep'

def test_checklist_and_metrics():
 c=checklist({'Chk_Title':'False','Chk_H1':'True','Chk_Desc':'nan'})
 assert c['Chk_Title']=='Non verificato' and c['Chk_H1']=='Criticità' and c['Chk_Desc']=='Non verificato'
 assert metrics({'a':'Criticità','b':'Nessuna criticità','c':'Non verificato','d':'Non applicabile'})==(1,2,3,50)
 assert metrics({'a':'Non verificato'})[-1] is None

def test_html_attributes_entities():
 assert parse_html('<title>A &amp; B</title><meta content="Test" NAME="Description"><h1><span>Ciao</span></h1>')=={'title':'A & B','description':'Test','h1':['Ciao']}

def test_block_private(monkeypatch):
 monkeypatch.setattr('socket.getaddrinfo',lambda *a,**k:[(2,1,6,'',('127.0.0.1',443))])
 with pytest.raises(ValueError):public_url('https://example.com')
 assert scan('https://example.com')['error']

def test_verified_certificates(monkeypatch):
 monkeypatch.setattr('socket.getaddrinfo',lambda *a,**k:[(2,1,6,'',('8.8.8.8',443))]);observed={}
 def handler(context):observed['context']=context;return object()
 class Response:
  url='https://example.com/';status=200
  class Headers:
   def get_content_type(self):return 'text/html'
   def get_content_charset(self):return 'utf-8'
  headers=Headers()
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self,*args):return b'<title>A</title><meta content="D" name="description"><h1>B</h1>'
 class Opener:
  def open(self,*args,**kwargs):return Response()
 monkeypatch.setattr('lead_core.HTTPSHandler',handler);monkeypatch.setattr('lead_core.build_opener',lambda *a:Opener())
 r=scan('example.com');assert not r['error'];assert r['checks']['Chk_Desc']=='Nessuna criticità';assert observed['context'].verify_mode==ssl.CERT_REQUIRED and observed['context'].check_hostname
