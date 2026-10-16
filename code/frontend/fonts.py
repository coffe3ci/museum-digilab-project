import os  # Om te controleren of een lettertype-bestand echt bestaat

from kivy.core.text import LabelBase  # Hiermee geven we een lettertype een korte naam

# De drie lettertypes van de app. In de .kv-bestanden gebruik je alleen de korte naam:
#   font_name: "Titel"   -> grote titels (museumnaam, paginatitels, objecttitels)
#   font_name: "Tekst"   -> gewone tekst en knoppen
#   font_name: "Klein"   -> kleine labels, hulpregels en onderschriften
FONT_MAP = "assets/fonts"
NEW_YORK = f"{FONT_MAP}/Chalet NewYorkNineteenEighty.otf"
LONDON = f"{FONT_MAP}/Chalet London Nineteen Eighty.otf"
STANLEY = f"{FONT_MAP}/stanley.otf"


# Tekens die het Stanley-font (titels) niet heeft, met een gelijkend teken dat het wel heeft.
# Zonder deze vervanging tekent Kivy een leeg vierkantje.
STANLEY_VERVANGINGEN = {
    "–": "-",    # – gedachtestreepje
    "—": "-",    # — lang gedachtestreepje
    "…": "...",  # … beletselteken
}


def voor_titel(tekst):
    # Maakt een tekst (bv. een objecttitel uit de database) geschikt voor het Stanley-font
    for teken, vervanging in STANLEY_VERVANGINGEN.items():
        tekst = tekst.replace(teken, vervanging)
    return tekst


def _of_reserve(pad):
    # Bestaat het bestand (nog) niet, gebruik dan Chalet NewYork, zodat de app niet vastloopt
    return pad if os.path.exists(pad) else NEW_YORK


def registreer_fonts():
    LabelBase.register(name="Titel", fn_regular=_of_reserve(STANLEY))
    LabelBase.register(name="Tekst", fn_regular=NEW_YORK)
    LabelBase.register(name="Klein", fn_regular=_of_reserve(LONDON))

    # Tekst zonder eigen lettertype (bv. de nummertjes en de "<"-knoppen) gebruikt ook Chalet NewYork
    LabelBase.register(name="Roboto", fn_regular=NEW_YORK)
