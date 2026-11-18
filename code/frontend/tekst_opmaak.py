# Opmaak van de beschrijving op de objectpagina: vet, schuin, onderstreept en tekstkleur.
#
# Hoe het werkt:
# - De tekst zelf blijft gewone tekst (kolom "beschrijving" in de database).
# - De opmaak staat apart (kolom "opmaak") als lijst van stukken: [begin, eind, stijl]
#   bv. [[0, 5, {"b": true}], [10, 20, {"kleur": "#7d4335", "i": true}]]
# - Tijdens het bewerken heeft elke letter zijn eigen stijl (een dict) in de lijst "stijlen".
# - Voor de objectpagina wordt het omgezet naar Kivy-markup: [b]..[/b], [color=#..]..[/color], enz.

import json
import re

from kivy.properties import StringProperty
from kivy.uix.textinput import TextInput

# Kleuren die je in het adminpaneel kunt kiezen. None = de standaard tekstkleur (opmaak eraf).
KLEUREN = [
    ("Standaard", None),
    ("Bruin", "#7d4335"),
    ("Rood", "#b3261e"),
    ("Blauw", "#1f4e8c"),
    ("Groen", "#2e7d32"),
    ("Goud", "#b8860b"),
    ("Grijs", "#8a8a8a"),
]

# Waar de opmaak op wordt toegepast (keuzes in het adminpaneel)
MODUS_WOORDEN = "Woorden (selectie)"
MODUS_ZIN = "Zin"
MODUS_ALINEA = "Alinea"
MODUS_ALLES = "Hele tekst"
MODI = [MODUS_WOORDEN, MODUS_ZIN, MODUS_ALINEA, MODUS_ALLES]


# ---------- Opslaan en laden ----------

def naar_stijlen(tekst, opmaak_json):
    # Maakt van de opgeslagen opmaak een lijst met één stijl (dict) per letter
    stijlen = [{} for _ in tekst]
    try:
        stukken = json.loads(opmaak_json) if opmaak_json else []
    except (ValueError, TypeError):
        stukken = []  # Kapotte opmaak: gewoon zonder opmaak tonen
    for begin, eind, stijl in stukken:
        for i in range(max(0, begin), min(eind, len(tekst))):
            stijlen[i] = dict(stijl)
    return stijlen


def naar_json(stijlen):
    # Maakt van de stijl per letter weer een korte lijst stukken (None = geen opmaak)
    stukken = []
    for begin, eind, stijl in _stukken(stijlen):
        if stijl:
            stukken.append([begin, eind, stijl])
    return json.dumps(stukken) if stukken else None


def _stukken(stijlen):
    # Groepeert letters die naast elkaar staan en dezelfde stijl hebben: (begin, eind, stijl)
    begin = 0
    for i in range(1, len(stijlen) + 1):
        if i == len(stijlen) or stijlen[i] != stijlen[begin]:
            yield begin, i, stijlen[begin]
            begin = i


# ---------- Tekst wordt getypt / verwijderd ----------

def pas_tekstwijziging_toe(oud, nieuw, stijlen):
    # Houdt de opmaak op de juiste letters als er tekst getypt, geplakt of verwijderd wordt.
    # Zoekt het stuk dat gelijk bleef aan het begin en aan het eind; daartussen is iets veranderd.
    voor = 0
    while voor < min(len(oud), len(nieuw)) and oud[voor] == nieuw[voor]:
        voor += 1
    na = 0
    while (na < min(len(oud), len(nieuw)) - voor
           and oud[len(oud) - 1 - na] == nieuw[len(nieuw) - 1 - na]):
        na += 1

    # Nieuwe letters krijgen de stijl van de letter ervoor (zoals in Word: doortypen in vet blijft vet)
    if voor > 0:
        erf = stijlen[voor - 1]
    elif len(oud) - na < len(stijlen):
        erf = stijlen[len(oud) - na]
    else:
        erf = {}
    aantal_nieuw = len(nieuw) - voor - na
    return stijlen[:voor] + [dict(erf) for _ in range(aantal_nieuw)] + stijlen[len(oud) - na:]


# ---------- Welk stuk tekst? (woorden / zin / alinea / alles) ----------

def _alinea_om(tekst, positie):
    # Begin en eind van de alinea (regel tussen twee enters) waar positie in staat
    begin = tekst.rfind("\n", 0, positie) + 1
    eind = tekst.find("\n", positie)
    return begin, len(tekst) if eind == -1 else eind


def _zin_om(tekst, positie):
    # Begin en eind van de zin waar positie in staat (zin eindigt op . ! of ?)
    a_begin, a_eind = _alinea_om(tekst, positie)
    alinea = tekst[a_begin:a_eind]
    zinnen = list(re.finditer(r"\S[^.!?]*(?:[.!?]+[\"')\]]*|$)", alinea))
    if not zinnen:
        return positie, positie
    p = positie - a_begin
    for zin in zinnen:
        if zin.start() <= p <= zin.end():
            return a_begin + zin.start(), a_begin + zin.end()
    # Cursor staat tussen twee zinnen (in de spatie): neem de zin ervoor, anders de eerste
    eerdere = [zin for zin in zinnen if zin.end() <= p]
    zin = eerdere[-1] if eerdere else zinnen[0]
    return a_begin + zin.start(), a_begin + zin.end()


def _woord_om(tekst, positie):
    # Begin en eind van het woord waar de cursor in (of direct achter) staat
    begin = positie
    while begin > 0 and (tekst[begin - 1].isalnum() or tekst[begin - 1] in "-'"):
        begin -= 1
    eind = positie
    while eind < len(tekst) and (tekst[eind].isalnum() or tekst[eind] in "-'"):
        eind += 1
    return begin, eind


def bereik(tekst, modus, cursor, selectie):
    # Geeft (begin, eind) van het stuk tekst waar de opmaak op komt.
    # selectie = (van, tot) van de geselecteerde tekst, of None; cursor = plek van de cursor.
    if modus == MODUS_ALLES:
        begin, eind = 0, len(tekst)
    elif selectie and selectie[0] != selectie[1]:
        van, tot = sorted(selectie)
        if modus == MODUS_ZIN:
            begin, eind = _zin_om(tekst, van)[0], _zin_om(tekst, max(van, tot - 1))[1]
        elif modus == MODUS_ALINEA:
            begin, eind = _alinea_om(tekst, van)[0], _alinea_om(tekst, max(van, tot - 1))[1]
        else:
            begin, eind = van, tot  # Precies de geselecteerde woorden
    else:
        cursor = max(0, min(cursor, len(tekst)))
        if modus == MODUS_ZIN:
            begin, eind = _zin_om(tekst, cursor)
        elif modus == MODUS_ALINEA:
            begin, eind = _alinea_om(tekst, cursor)
        else:
            begin, eind = _woord_om(tekst, cursor)  # Niets geselecteerd: het woord bij de cursor

    # Spaties en enters aan de randen niet meenemen
    while begin < eind and tekst[begin].isspace():
        begin += 1
    while eind > begin and tekst[eind - 1].isspace():
        eind -= 1
    return begin, eind


# ---------- Opmaak aanpassen ----------

def wissel(stijlen, begin, eind, sleutel):
    # Vet ("b"), schuin ("i") of onderstreept ("u") aan/uit voor het stuk.
    # Heeft het hele stuk het al, dan gaat het eraf; anders komt het op het hele stuk.
    deel = stijlen[begin:eind]
    aan = not all(stijl.get(sleutel) for stijl in deel)
    for stijl in deel:
        if aan:
            stijl[sleutel] = True
        else:
            stijl.pop(sleutel, None)


def zet_kleur(stijlen, begin, eind, kleur):
    # Geeft het stuk een kleur (bv. "#7d4335"); None = terug naar de standaard kleur
    for stijl in stijlen[begin:eind]:
        if kleur:
            stijl["kleur"] = kleur
        else:
            stijl.pop("kleur", None)


def wis(stijlen, begin, eind):
    # Haalt alle opmaak van het stuk af
    for stijl in stijlen[begin:eind]:
        stijl.clear()


# ---------- Tonen ----------

def _ontsnap(tekst):
    # Tekens die in Kivy-markup een speciale betekenis hebben, worden gewone tekens
    return tekst.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def naar_markup(tekst, stijlen):
    # Maakt Kivy-markup van de tekst met opmaak (voor een Label met markup: True)
    delen = []
    for begin, eind, stijl in _stukken(stijlen):
        stuk = _ontsnap(tekst[begin:eind])
        if stijl.get("u"):
            stuk = f"[u]{stuk}[/u]"
        if stijl.get("i"):
            stuk = f"[i]{stuk}[/i]"
        if stijl.get("b"):
            stuk = f"[b]{stuk}[/b]"
        if stijl.get("kleur"):
            stuk = f"[color={stijl['kleur']}]{stuk}[/color]"
        delen.append(stuk)
    return "".join(delen) if stijlen else _ontsnap(tekst)


def opgemaakte_tekst(tekst, opmaak_json):
    # Voor de objectpagina: tekst + opgeslagen opmaak -> markup
    tekst = tekst or ""
    return naar_markup(tekst, naar_stijlen(tekst, opmaak_json))


# ---------- Het invoerveld in het adminpaneel ----------

class OpmaakVeld(TextInput):
    # Invoerveld voor de beschrijving dat ook de opmaak per letter bijhoudt.
    # Hoe het eruitziet staat in admin_panel.kv (<OpmaakVeld>).
    voorbeeld = StringProperty("")  # Markup voor het voorbeeld onder het veld

    def __init__(self, **kwargs):
        self.stijlen = []
        self._oude_tekst = ""
        self.laatste_selectie = None  # (van, tot) van de laatst geselecteerde tekst
        self.laatste_cursor = 0
        super().__init__(**kwargs)

    def zet_inhoud(self, tekst, opmaak_json):
        # Vult het veld met een bestaande beschrijving en zijn opmaak
        tekst = tekst or ""
        self._oude_tekst = tekst
        self.stijlen = naar_stijlen(tekst, opmaak_json)
        self.text = tekst
        self._ververs()

    def inhoud(self):
        # Geeft (tekst, opmaak_json) om op te slaan; spaties/enters aan begin en eind gaan eraf
        tekst = self.text
        begin = len(tekst) - len(tekst.lstrip())
        eind = len(tekst.rstrip())
        if eind <= begin:
            return "", None
        return tekst[begin:eind], naar_json(self.stijlen[begin:eind])

    def on_text(self, *args):
        # Tekst veranderd (typen, plakken, wissen): opmaak verschuift mee
        self.stijlen = pas_tekstwijziging_toe(self._oude_tekst, self.text, self.stijlen)
        self._oude_tekst = self.text
        self._ververs()

    # Kivy wist de selectie zodra je op een knop drukt; daarom onthouden we hem zelf
    def on_selection_text(self, instance, waarde):
        if waarde:
            self.laatste_selectie = tuple(sorted((self.selection_from, self.selection_to)))
        elif self.focus:
            self.laatste_selectie = None  # Selectie bewust weggehaald tijdens het typen

    def on_cursor(self, *args):
        if self.focus:
            self.laatste_cursor = self.cursor_index()

    def pas_opmaak_toe(self, modus, actie, kleur=None):
        # actie: "b", "i", "u" (aan/uit), "kleur" of "wis"
        begin, eind = bereik(self.text, modus, self.laatste_cursor, self.laatste_selectie)
        if begin >= eind:
            return False  # Niets om op te maken (bv. cursor niet in een woord)
        if actie == "kleur":
            zet_kleur(self.stijlen, begin, eind, kleur)
        elif actie == "wis":
            wis(self.stijlen, begin, eind)
        else:
            wissel(self.stijlen, begin, eind, actie)
        self._ververs()
        return True

    def _ververs(self):
        self.voorbeeld = naar_markup(self.text, self.stijlen)
