import os  # Om te controleren of een afbeelding echt bestaat
import time  # Om te meten hoe snel twee tikken na elkaar komen

from kivy.animation import Animation  # Voor het soepel doorschuiven naar de volgende 9
from kivy.core.image import Image as CoreImage  # Laadt een afbeelding als textuur om zelf te tekenen
from kivy.factory import Factory  # Maakt PaginaKnoppen aan (gedefinieerd in object_screen.kv)
from kivy.clock import Clock  # Om de titel één keer per frame passend te maken
from kivy.core.text import Label as CoreLabel  # Om te meten hoeveel regels een titel inneemt
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.stencilview import StencilView  # Toont alleen wat binnen het vlak valt
from kivy.uix.widget import Widget  # Lege widget, gebruikt als opvulling
from kivy.utils import escape_markup  # Tekens als [ en ] in een naam veilig tonen in markup

from backend.object_manager import ObjectManager
from frontend.beeld import tegel_pad  # Kleine versie van een foto voor de tegels

PER_PAGINA = 9  # Aantal objectknoppen per blok (3x3) = wat je in één keer ziet
ADMIN_TIK_TIJD = 0.6  # Maximaal aantal seconden tussen twee tikken op de geheime admin-knop
ADMIN_TIKKEN = 4  # Zo vaak snel achter elkaar tikken om het inlogscherm te openen
VEEG_AFSTAND = 40  # Zo ver (in dp) moet je minstens vegen om naar het volgende blok te gaan
TIK_AFSTAND = 15  # Minder bewogen dan dit (in dp) = een tik (object openen) in plaats van een veeg
ANIMATIE_TIJD = 0.35  # Duur van het doorschuiven in seconden
MAX_PAGINAKNOPPEN = 7  # Bij meer pagina's worden niet alle nummers getoond (dan komt er "...")
FILTERS_PER_BLOK = 3  # Zoveel filterknoppen staan er tegelijk in beeld boven de objecten

# Zachte kleuren voor de bubbels als "groeperen" aan staat (één per categorie, in tijdlijn-volgorde).
# Rustig genoeg dat de foto's het belangrijkst blijven, maar duidelijk verschillend.
BUBBEL_KLEUREN = [
    (0.93, 0.86, 0.76, 1),  # zand
    (0.84, 0.89, 0.86, 1),  # saliegroen
    (0.86, 0.87, 0.93, 1),  # lichtblauw
    (0.93, 0.84, 0.82, 1),  # oudroze
    (0.90, 0.88, 0.80, 1),  # olijf
    (0.88, 0.85, 0.91, 1),  # lavendel
]


def zichtbare_paginas(huidig, totaal):
    # Geeft de paginanummers die onderin getoond worden; None = "..." (overgeslagen nummers).
    # Tot 7 pagina's: allemaal. Daarboven: de eerste, de laatste en de huidige met zijn buren,
    # zodat de rij nummers nooit te breed wordt. Voorbeeld: pagina 6 van 12 -> 1 ... 5 6 7 ... 12
    if totaal <= MAX_PAGINAKNOPPEN:
        return list(range(1, totaal + 1))

    nummers = sorted({1, totaal, huidig - 1, huidig, huidig + 1} & set(range(1, totaal + 1)))
    resultaat = []
    for nr in nummers:
        if resultaat and nr - resultaat[-1] > 1:
            resultaat.append(None)  # Gat tussen twee nummers
        resultaat.append(nr)
    return resultaat


TITEL_GROOTTES = [15, 14, 13, 12]  # Lettergroottes (sp) voor de titel op een knop, van groot naar klein
TITEL_MARGE = 10  # Ruimte (dp) links en rechts van de titel in de balk


def aantal_regels(tekst, grootte, breedte):
    # Op hoeveel regels komt deze tekst bij deze lettergrootte en breedte? (zelfde lettertype als de knop)
    meet = CoreLabel(text=tekst, font_name="Tekst", font_size=grootte, bold=True,
                     text_size=(breedte, None), line_height=0.95)
    meet.refresh()
    een = CoreLabel(text="X", font_name="Tekst", font_size=grootte, bold=True, line_height=0.95)
    een.refresh()
    return round(meet.texture.height / een.texture.height) if een.texture.height else 1


class ObjectKnop(ButtonBehavior, FloatLayout):
    # Een knop met een afbeelding die de hele knop vult, met afgeronde hoeken.
    # Hoe hij eruitziet staat in object_screen.kv (<ObjectKnop>).
    titel = StringProperty("")
    titel_tekst = StringProperty("")  # De titel zoals hij op de knop staat (eventueel ingekort met "…")
    titel_grootte = NumericProperty(sp(TITEL_GROOTTES[0]))  # Lettergrootte van de titel (past zich aan)
    nummer = StringProperty("")  # Volgnummer linksboven in de knop (1, 2, 3, ...)
    afbeelding = StringProperty("")  # Pad naar de afbeelding
    textuur = ObjectProperty(None, allownone=True)  # De geladen afbeelding (volledig)
    uitsnede = ObjectProperty(None, allownone=True)  # Het bijgesneden deel dat getoond wordt

    def __init__(self, **kwargs):
        self._titel_later = Clock.create_trigger(self.past_titel)
        super().__init__(**kwargs)

    def on_afbeelding(self, *args):
        # Laadt de afbeelding zodra het pad verandert
        self.textuur = CoreImage(self.afbeelding).texture if self.afbeelding else None
        self._titel_later()

    def on_titel(self, *args):
        self._titel_later()

    def on_textuur(self, *args):
        self.bereken_uitsnede()

    def on_size(self, *args):
        self.bereken_uitsnede()
        self._titel_later()

    def past_titel(self, *args):
        # Zorgt dat de titel netjes in de balk past: hooguit 2 regels (met afbeelding).
        # Eerst de normale lettergrootte; past het niet, dan steeds iets kleiner (tot 12sp).
        # Past het dan nog niet (heel smalle knop), dan wordt de titel ingekort met "…".
        breedte = self.width - dp(2 * TITEL_MARGE)
        if breedte <= 0 or not self.titel:
            self.titel_tekst = self.titel
            return
        max_regels = 2 if self.afbeelding else 4  # zonder afbeelding is er de hele knop
        for grootte in TITEL_GROOTTES:
            if aantal_regels(self.titel, sp(grootte), breedte) <= max_regels:
                self.titel_grootte = sp(grootte)
                self.titel_tekst = self.titel
                return
        # Zelfs op de kleinste maat te lang: woorden weghalen tot het past, met "…" erachter
        self.titel_grootte = sp(TITEL_GROOTTES[-1])
        woorden = self.titel.split()
        while len(woorden) > 1:
            woorden.pop()
            kort = " ".join(woorden).rstrip(",;:-") + "…"
            if aantal_regels(kort, self.titel_grootte, breedte) <= max_regels:
                self.titel_tekst = kort
                return
        self.titel_tekst = self.titel

    def bereken_uitsnede(self):
        # Snijdt de afbeelding bij zodat hij de knop precies vult zonder uit te rekken ("cover").
        if not self.textuur or self.width == 0 or self.height == 0:
            self.uitsnede = None
            return

        beeld_breedte, beeld_hoogte = self.textuur.size
        knop_verhouding = self.width / self.height

        if beeld_breedte / beeld_hoogte > knop_verhouding:
            # Afbeelding is breder dan de knop: links en rechts een stuk afsnijden
            breedte = beeld_hoogte * knop_verhouding
            hoogte = beeld_hoogte
        else:
            # Afbeelding is hoger dan de knop: boven en onder een stuk afsnijden
            breedte = beeld_breedte
            hoogte = beeld_breedte / knop_verhouding

        # Pak het middelste stuk van de afbeelding
        x = (beeld_breedte - breedte) / 2
        y = (beeld_hoogte - hoogte) / 2
        self.uitsnede = self.textuur.get_region(x, y, breedte, hoogte)


class VeegWand(StencilView):
    # Het zichtbare vlak met de objecten. De blokken van 9 staan naast elkaar;
    # met één veeg naar links of rechts schuift de wand (met animatie) precies één blok op.
    # De wand zelf (id: wand) staat in object_screen.kv en schuift mee met "positie".
    blok = NumericProperty(0)  # Welk blok nu zichtbaar is (0 = het eerste)
    aantal_blokken = NumericProperty(1)
    positie = NumericProperty(0)  # Hoeveel pixels de wand naar links is geschoven

    def wand(self):
        # De rij met blokken (het enige kind van de VeegWand, zie object_screen.kv)
        return self.children[0]

    def stap(self):
        # Afstand van het ene blok naar het volgende: blokbreedte + de ruimte tussen de blokken.
        # De ruimte lezen we uit de wand zelf (spacing in object_screen.kv), zodat het altijd klopt,
        # ook bij Windows-schermschaling (125%, 150%) waarbij "dp" pas later zijn echte waarde krijgt.
        if not self.children:
            return self.width
        return self.width + self.wand().spacing

    def on_width(self, *args):
        # Venster veranderd van grootte: blokken mee laten groeien en netjes op het blok blijven staan
        if not self.children:
            return
        for blok in self.wand().children:
            blok.width = self.width
        Animation.cancel_all(self, "positie")
        self.positie = self.blok * self.stap()

    def ga_naar_blok(self, blok, animatie=True):
        # Schuift naar het gegeven blok (wordt binnen de grenzen gehouden)
        self.blok = max(0, min(blok, self.aantal_blokken - 1))
        doel = self.blok * self.stap()
        Animation.cancel_all(self, "positie")
        if animatie:
            Animation(positie=doel, d=ANIMATIE_TIJD, t="out_cubic").start(self)
        else:
            self.positie = doel

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return False
        # Deze aanraking is van ons: we volgen hem tot de vinger loslaat
        touch.grab(self)
        touch.ud["wand_start"] = self.positie
        Animation.cancel_all(self, "positie")  # Een lopende animatie stoppen
        # Meteen laten zien welke knop je aanraakt (voelt direct, ook op een trage tablet)
        knop = self.knop_onder(touch)
        if knop is not None:
            knop.state = "down"
            touch.ud["wand_knop"] = knop
        return True

    def los_knop(self, touch):
        # Haalt de "ingedrukt"-weergave weer weg (bij vegen of loslaten)
        knop = touch.ud.pop("wand_knop", None)
        if knop is not None:
            knop.state = "normal"
        return knop

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        if abs(touch.x - touch.ox) > dp(TIK_AFSTAND) or abs(touch.y - touch.oy) > dp(TIK_AFSTAND):
            self.los_knop(touch)  # het wordt een veeg, geen tik
        # De wand beweegt met de vinger mee
        nieuw = touch.ud["wand_start"] - (touch.x - touch.ox)
        uiterste = (self.aantal_blokken - 1) * self.stap()
        # Voorbij het begin of eind: wand gaat maar een klein stukje mee (voelt als een elastiekje)
        if nieuw < 0:
            nieuw *= 0.3
        elif nieuw > uiterste:
            nieuw = uiterste + (nieuw - uiterste) * 0.3
        self.positie = nieuw
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        knop = self.los_knop(touch)

        dx = touch.x - touch.ox
        dy = touch.y - touch.oy
        # dp() hier pas uitrekenen (niet bovenaan), zodat de schermschaling al bekend is
        tik, veeg = dp(TIK_AFSTAND), dp(VEEG_AFSTAND)
        if abs(dx) < tik and abs(dy) < tik:
            # Nauwelijks bewogen: het is een tik, dus open het object onder de vinger
            self.ga_naar_blok(self.blok)
            if knop is not None:
                knop.dispatch("on_release")
        elif dx < -veeg:
            self.ga_naar_blok(self.blok + 1)  # Naar links geveegd: volgende 9
        elif dx > veeg:
            self.ga_naar_blok(self.blok - 1)  # Naar rechts geveegd: vorige 9
        else:
            self.ga_naar_blok(self.blok)  # Te kleine veeg: terug naar hetzelfde blok
        return True

    def knop_onder(self, touch):
        # Zoekt de knop onder de vinger (objectknop of filterknop, ook binnen een bubbel)
        for knop in self.wand().walk(restrict=True):
            if isinstance(knop, ButtonBehavior) and not knop.disabled and knop.collide_point(*touch.pos):
                return knop
        return None


class ObjectScreen(Screen):
    alle_objecten = []  # Alle objecten uit de database
    objecten = []  # De objecten die nu op de wand staan (na het filter)
    categorieen = []  # Alle categorieën (periodes) in tijdlijn-volgorde
    filter_id = None  # Gekozen categorie; None = alle objecten
    filter_knoppen = []  # (categorie-id, knop) van alle filterknoppen
    terug_naar_blok = None  # Na het bekijken van een object terugkomen op dezelfde 9
    filter_zichtbaar = BooleanProperty(True)  # Filterbalk tonen (instelling in het adminpaneel)
    groeperen = False  # Objecten per categorie in een bubbel (instelling in het adminpaneel)
    vorige_admin_tik = 0  # Tijdstip van de vorige tik op de geheime admin-knop
    admin_tikken = 0  # Hoeveel keer er al snel achter elkaar op de admin-knop is getikt
    _vorige_stand = None  # Gegevens waarmee de wand het laatst is opgebouwd (om onnodig opbouwen te voorkomen)

    def on_enter(self):
        # Wordt automatisch uitgevoerd elke keer dat dit scherm geopend wordt.
        # Zo zijn nieuwe objecten en categorieën uit het adminpaneel direct zichtbaar.
        manager = ObjectManager()
        self.alle_objecten = manager.get_all_objects()
        self.categorieen = manager.get_categorieen()
        # Instellingen uit het adminpaneel ("Weergave voor bezoekers")
        self.filter_zichtbaar = manager.get_instelling("filter_tonen")
        self.groeperen = manager.get_instelling("groeperen")
        # Bestaat het gekozen filter niet meer (verwijderd in het adminpaneel), of staat de
        # filterbalk uit? Dan weer alles tonen.
        if not self.filter_zichtbaar or self.filter_id not in [cat["id"] for cat in self.categorieen]:
            self.filter_id = None

        # Is er sinds de vorige keer niets veranderd (bv. terug van een objectpagina)? Dan staat de
        # wand er al: niet alles opnieuw opbouwen, dat is op de tablet het traagste deel.
        stand = (tuple(tuple(obj) for obj in self.alle_objecten),
                 tuple(tuple(sorted(cat.items())) for cat in self.categorieen),
                 self.filter_zichtbaar, self.groeperen, self.filter_id)
        if stand == self._vorige_stand and self.ids.wand.children:
            if self.terug_naar_blok is None:
                self.ids.veegwand.ga_naar_blok(0, animatie=False)  # nieuwe bezoeker: vooraan beginnen
            self.terug_naar_blok = None
            return
        self._vorige_stand = stand

        self.maak_filterknoppen()
        # Terug van een objectpagina: zelfde filter en dezelfde 9 objecten als daarvoor
        self.toon_objecten(begin_blok=self.terug_naar_blok or 0)
        self.terug_naar_blok = None

    def maak_filterknoppen(self):
        # Maakt de knoppen boven de wand: "Alle objecten" en één per periode (alleen periodes met objecten).
        # Er staan altijd precies 3 filters in beeld (in blokjes van 3, net als de 9 objecten);
        # met de pijltjes of door te vegen zie je de volgende/vorige 3.
        # Hoe de knoppen eruitzien staat in object_screen.kv (<FilterKnop>).
        filter_wand = self.ids.filter_wand
        rij = self.ids.filters
        rij.clear_widgets()
        self.filter_knoppen = []
        met_objecten = [cat for cat in self.categorieen if cat["aantal"] > 0]
        # Geen filterrij als het museum hem heeft uitgezet of als er geen categorieën zijn
        toon = self.filter_zichtbaar and bool(met_objecten)
        self.filter_zichtbaar = toon  # De wand wordt dan groter (zie object_screen.kv)
        filter_wand.opacity = 1 if toon else 0
        filter_wand.disabled = not toon
        if not toon:
            filter_wand.aantal_blokken = 1
            self.werk_filterpijlen_bij()
            return

        # Twee regels per knop: naam (vet) en daaronder klein de periode (of het aantal bij "Alle objecten")
        knoppen = [(None, f"[b]Alle objecten[/b]\n[size=11sp]{len(self.alle_objecten)} objecten[/size]")]
        for cat in met_objecten:
            onder = cat["periode"] or f"{cat['aantal']} objecten"
            tekst = f"[b]{escape_markup(cat['naam'])}[/b]\n[size=11sp]{escape_markup(onder)}[/size]"
            knoppen.append((cat["id"], tekst))

        actief_blok = 0
        for start in range(0, len(knoppen), FILTERS_PER_BLOK):
            # Eén blok = 3 filters naast elkaar, precies zo breed als het zichtbare deel
            blok = BoxLayout(spacing=rij.spacing, size_hint_x=None, width=filter_wand.width)
            for cat_id, tekst in knoppen[start:start + FILTERS_PER_BLOK]:
                knop = Factory.FilterKnop(text=tekst)
                knop.actief = cat_id == self.filter_id
                if knop.actief:
                    actief_blok = start // FILTERS_PER_BLOK
                # cat_id=cat_id zorgt dat elke knop zijn eigen categorie onthoudt
                knop.bind(on_release=lambda btn, cat_id=cat_id: self.kies_filter(cat_id))
                blok.add_widget(knop)
                self.filter_knoppen.append((cat_id, knop))
            # Laatste blok niet vol? Lege plekken, zodat de knoppen even breed blijven
            for _ in range(FILTERS_PER_BLOK - len(knoppen[start:start + FILTERS_PER_BLOK])):
                blok.add_widget(Widget())
            rij.add_widget(blok)

        filter_wand.aantal_blokken = -(-len(knoppen) // FILTERS_PER_BLOK)  # naar boven afgerond
        filter_wand.ga_naar_blok(actief_blok, animatie=False)  # Het gekozen filter staat in beeld
        self.werk_filterpijlen_bij()

    def werk_filterpijlen_bij(self):
        # Pijltjes naast de filters: vaag als je niet verder kunt, onzichtbaar als alles in één keer past
        if "filter_wand" not in self.ids:  # Scherm wordt nog opgebouwd
            return
        filter_wand = self.ids.filter_wand
        huidig, totaal = filter_wand.blok, filter_wand.aantal_blokken
        for pijl, kan_niet in ((self.ids.filter_links, huidig == 0),
                               (self.ids.filter_rechts, huidig >= totaal - 1)):
            pijl.disabled = kan_niet or totaal <= 1
            pijl.opacity = 0 if totaal <= 1 or filter_wand.disabled else (0.3 if kan_niet else 1)

    def kies_filter(self, cat_id):
        # Wordt uitgevoerd als op een filterknop wordt gedrukt.
        if cat_id == self.filter_id:
            return
        self.filter_id = cat_id
        self._vorige_stand = None  # wand wordt hieronder opnieuw opgebouwd
        for knop_cat_id, knop in self.filter_knoppen:  # De gekozen knop wordt bruin
            knop.actief = knop_cat_id == cat_id

        # Wand kort laten vervagen, nieuwe objecten zetten en weer laten verschijnen
        veegwand = self.ids.veegwand
        Animation.cancel_all(veegwand, "opacity")
        uit = Animation(opacity=0, d=0.12)
        uit.bind(on_complete=lambda *a: (self.toon_objecten(),
                                          Animation(opacity=1, d=0.2).start(veegwand)))
        uit.start(veegwand)

    def toon_objecten(self, begin_blok=0):
        # Zet de objecten (van het gekozen filter) op de wand: blokken van 3x3 naast elkaar.
        # Eén blok is precies zo breed als het zichtbare deel, dus je ziet eerst 9 objecten
        # en veegt naar links of rechts om de volgende/vorige 9 te zien.
        # De nummers blijven gewoon het nummer van het object; objecten buiten het filter
        # worden niet getoond, de rest schuift aan.
        if self.filter_id is None:
            self.objecten = list(self.alle_objecten)
        else:
            self.objecten = [obj for obj in self.alle_objecten if obj["categorie_id"] == self.filter_id]
        self.ids.leeg_melding.opacity = 0 if self.objecten else 1

        veegwand = self.ids.veegwand
        wand = self.ids.wand
        wand.clear_widgets()  # Verwijder de knoppen van de vorige keer

        for cat, blok_objecten in self.paginas():
            # Zelfde ruimte tussen de knoppen als tussen de blokken (spacing van de wand in de .kv)
            raster = GridLayout(cols=3, spacing=wand.spacing)

            for obj in blok_objecten:
                raster.add_widget(self.maak_knop(obj))

            # Vul lege plekken op, zodat de knoppen niet te groot worden
            for _ in range(PER_PAGINA - len(blok_objecten)):
                raster.add_widget(Widget())

            if cat is None:
                blok = raster
            else:
                # Groeperen staat aan: de 9 objecten in een gekleurde bubbel met de naam van de periode
                blok = Factory.CategorieBubbel()
                blok.naam = cat["naam"]
                blok.periode = cat["periode"]
                blok.kleur = BUBBEL_KLEUREN[cat["plek"] % len(BUBBEL_KLEUREN)]
                blok.ids.inhoud.add_widget(raster)
            blok.size_hint_x = None
            blok.width = veegwand.width
            wand.add_widget(blok)

        veegwand.aantal_blokken = len(wand.children)
        veegwand.ga_naar_blok(begin_blok, animatie=False)  # Meestal de eerste 9 (blok 0)
        self.werk_navigatie_bij()  # Pijlen en nummers kloppend maken (ook als blok al 0 was)

    def paginas(self):
        # Verdeelt de objecten over pagina's van 9. Geeft een lijst (categorie, objecten) terug.
        # Groeperen uit: gewoon op nummer, categorie = None (geen bubbel).
        # Groeperen aan: per categorie (in tijdlijn-volgorde) eigen pagina's, elke pagina met
        # een bubbel; objecten zonder categorie komen achteraan onder "Overig".
        if not self.groeperen:
            starts = range(0, max(len(self.objecten), 1), PER_PAGINA)
            return [(None, self.objecten[s:s + PER_PAGINA]) for s in starts]

        groepen = []
        for plek, cat in enumerate(self.categorieen):
            leden = [obj for obj in self.objecten if obj["categorie_id"] == cat["id"]]
            if leden:
                groepen.append((dict(cat, plek=plek), leden))
        bekend = {cat["id"] for cat in self.categorieen}
        overig = [obj for obj in self.objecten if obj["categorie_id"] not in bekend]
        if overig:
            groepen.append(({"naam": "Overig", "periode": "", "plek": len(self.categorieen)}, overig))

        resultaat = []
        for cat, leden in groepen:
            for s in range(0, len(leden), PER_PAGINA):
                resultaat.append((cat, leden[s:s + PER_PAGINA]))
        return resultaat or [(None, [])]

    def werk_navigatie_bij(self):
        # Zet de pijlen < > aan/uit en maakt onderin de paginanummers (1 2 3 ...).
        # Wordt vanzelf aangeroepen als je naar andere 9 objecten gaat (pijl, nummer of vegen)
        # en als het aantal pagina's verandert (bijv. nieuw object in het adminpaneel).
        if "veegwand" not in self.ids:  # Scherm wordt nog opgebouwd
            return
        veegwand = self.ids.veegwand
        huidig = veegwand.blok
        totaal = veegwand.aantal_blokken

        # Pijlen: vaag en uit als je al op de eerste of laatste pagina bent, onzichtbaar bij maar 1 pagina
        for pijl, kan_niet in ((self.ids.pijl_links, huidig == 0),
                               (self.ids.pijl_rechts, huidig >= totaal - 1)):
            pijl.disabled = kan_niet
            if totaal <= 1:
                pijl.opacity = 0
            else:
                pijl.opacity = 0.3 if kan_niet else 1

        # Paginanummers: precies zoveel als er pagina's zijn (bij 1 pagina geen nummers)
        balk = self.ids.pagina_nummers
        balk.clear_widgets()
        if totaal <= 1:
            return
        for nr in zichtbare_paginas(huidig + 1, totaal):
            if nr is None:
                balk.add_widget(Factory.PaginaPuntjes())  # "..." bij heel veel pagina's
                continue
            knop = Factory.PaginaKnop(text=str(nr))
            knop.actief = nr == huidig + 1  # De pagina die je nu ziet is bruin
            # nr=nr zorgt dat elke knop zijn eigen paginanummer onthoudt (blok telt vanaf 0)
            knop.bind(on_release=lambda btn, nr=nr: veegwand.ga_naar_blok(nr - 1))
            balk.add_widget(knop)

    def maak_knop(self, obj):
        # Maakt één objectknop voor het gegeven object.
        knop = ObjectKnop()
        knop.titel = obj[1]
        knop.nummer = str(obj["id"])  # Het id uit de database is het nummer (aanpasbaar in het adminpaneel)

        # Toon de afbeelding alleen als het bestand echt bestaat (kleine tegelversie: snel te laden)
        if obj[3] and os.path.exists(obj[3]):
            knop.afbeelding = tegel_pad(obj[3])

        # obj_id=obj["id"] zorgt dat elke knop zijn eigen id onthoudt
        knop.bind(on_release=lambda btn, obj_id=obj["id"]: self.open_object(obj_id))
        return knop

    def open_object(self, obj_id):
        # Wordt uitgevoerd als op een objectknop wordt gedrukt.
        # Vult de detailpagina met dit object en gaat er naartoe.
        self.terug_naar_blok = self.ids.veegwand.blok  # Bij terugkomen weer deze 9 laten zien
        self.manager.get_screen("object_detail").toon_object(obj_id)
        self.manager.current = "object_detail"

    def admin_tik(self):
        # Wordt uitgevoerd bij elke tik op de onzichtbare knop rechtsboven.
        # Pas bij 4 tikken kort na elkaar gaat het inlogscherm open.
        nu = time.time()
        if nu - self.vorige_admin_tik < ADMIN_TIK_TIJD:
            self.admin_tikken += 1  # Snel genoeg na de vorige tik: doortellen
        else:
            self.admin_tikken = 1  # Te lang gewacht: opnieuw beginnen met tellen
        self.vorige_admin_tik = nu

        if self.admin_tikken >= ADMIN_TIKKEN:
            self.admin_tikken = 0
            self.vorige_admin_tik = 0
            self.go_to_admin()

    def go_to_admin(self):  # Functie/methode om te navigeren naar het beheerderscherm
        self.manager.current = "admin"  # Verander het huidige actieve scherm naar het scherm met de naam 'admin'

    def terug_naar_home(self):
        # Deze functie wordt uitgevoerd wanneer de gebruiker op de terugknop drukt.
        # Schakelt via de ScreenManager terug naar het homescreen.
        if self.filter_id is not None:
            self.filter_id = None  # Volgende bezoeker begint weer met alle objecten
            self._vorige_stand = None
        self.manager.current = "home"
