from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_app_navigation_and_workflow(tmp_path,monkeypatch):
 csv=tmp_path/'leads.csv';csv.write_text('AZIENDA;SEDE;WEB\nTest Company;Udine;example.com\n',encoding='utf-8-sig');monkeypatch.setenv('GDP_LEAD_FILE',str(csv))
 at=AppTest.from_file(str(Path(__file__).parents[1]/'App.py'),default_timeout=20).run();assert not at.exception
 at.radio[0].set_value('Scheda lead').run();assert not at.exception
 next(x for x in at.text_area if x.label=='Note e valutazione').set_value('Nota salvata durante il test');next(x for x in at.text_input if x.label=='Prossima azione').set_value('Telefonare')
 next(x for x in at.button if x.label=='Salva note e prossimo passo').click().run();assert not at.exception;assert 'Nota salvata' in csv.read_text()
 at.radio[0].set_value('Importa ed esporta').run();assert not at.exception
 at.radio[0].set_value('Guida').run();assert not at.exception
