from datetime import datetime

from sources.googlesheet import sheet_tab, sheet_value
from model.resultaat import BEGROTING_SHEET, RESULTAAT_TAB, RESULTAAT_BONUSSEN_ROW, BEGROTING_TAB, BEGROTING_WINST_VORIG_JAAR_ROW

def test_bonus_row_caption():
    ''' Test checkt of er niet per ongeluk regels zijn toegevoerd of verwijderd'''
    tab = sheet_tab(BEGROTING_SHEET, RESULTAAT_TAB)
    assert sheet_value(tab, RESULTAAT_BONUSSEN_ROW, 2) == 'Totaal bonussen'

def test_begroting_vorig_jaar_row_caption():
    ''' Test checkt of er niet per ongeluk regels zijn toegevoerd of verwijderd'''
    tab = sheet_tab(BEGROTING_SHEET, BEGROTING_TAB)
    assert sheet_value(tab, BEGROTING_WINST_VORIG_JAAR_ROW, 2) == datetime.today().year - 1