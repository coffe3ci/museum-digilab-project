import os  # Om te controleren of een afbeelding echt bestaat
import time  # Om te meten hoe snel twee tikken na elkaar komen

from kivy.core.image import Image as CoreImage  # Laadt een afbeelding als textuur om zelf te tekenen
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget  # Lege widget, gebruikt als opvulling

from backend.object_manager import ObjectManager

PER_PAGINA = 9  # Aantal objectknoppen per blok (3x3) = wat je in één keer ziet
DUBBELTIK_TIJD = 0.6  # Maximaal aantal seconden tussen twee tikken op de geheime admin-knop


class ObjectKnop(ButtonBehavior, FloatLayout):
    # Een knop met een afbeelding die de hele knop vult, met afgeronde hoeken.
    # Hoe hij eruitziet staat in object_screen.kv (<ObjectKnop>).
    titel = StringProperty("")
    nummer = StringProperty("")  # Volgnummer linksboven in de knop (1, 2, 3, ...)
    afbeelding = StringProperty("")  # Pad naar de afbeelding
    textuur = ObjectProperty(None, allownone=True)  # De geladen afbeelding (volledig)
    uitsnede = ObjectProperty(None, allownone=True)  # Het bijgesneden deel dat getoond wordt

    def on_afbeelding(self, *args):
        # Laadt de afbeelding zodra het pad verandert
        self.textuur = CoreImage(self.afbeelding).texture if self.afbeelding else None

    def on_textuur(self, *args):
        self.bereken_uitsnede()

    def on_size(self, *args):
        self.bereken_uitsnede()

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


class ObjectScreen(Screen):
    objecten = []  # Alle objecten uit de database
    vorige_admin_tik = 0  # Tijdstip van de vorige tik op de geheime admin-knop

    def on_kv_post(self, base_widget):
        # Als het venster van grootte verandert, worden de blokken mee breder/smaller
        self.ids.scroller.bind(width=self.pas_blokbreedte_aan)

    def pas_blokbreedte_aan(self, scroller, breedte):
        for blok in self.ids.wand.children:
            blok.width = breedte

    def on_enter(self):
        # Wordt automatisch uitgevoerd elke keer dat dit scherm geopend wordt.
        # Zo zijn nieuwe objecten uit het adminpaneel direct zichtbaar.
        self.objecten = ObjectManager().get_all_objects()
        self.toon_objecten()

    def toon_objecten(self):
        # Zet alle objecten op de wand: blokken van 3x3 naast elkaar.
        # Eén blok is precies zo breed als het zichtbare deel, dus je ziet eerst 9 objecten
        # en scrollt van links naar rechts om de rest te zien.
        scroller = self.ids.scroller
        wand = self.ids.wand
        wand.clear_widgets()  # Verwijder de knoppen van de vorige keer

        for start in range(0, max(len(self.objecten), 1), PER_PAGINA):
            blok_objecten = self.objecten[start:start + PER_PAGINA]

            blok = GridLayout(cols=3, spacing=dp(15), size_hint_x=None, width=scroller.width)

            for obj in blok_objecten:
                blok.add_widget(self.maak_knop(obj))

            # Vul lege plekken op, zodat de knoppen niet te groot worden
            for _ in range(PER_PAGINA - len(blok_objecten)):
                blok.add_widget(Widget())

            wand.add_widget(blok)

        scroller.scroll_x = 0  # Begin altijd helemaal links

    def maak_knop(self, obj):
        # Maakt één objectknop voor het gegeven object.
        knop = ObjectKnop()
        knop.titel = obj[1]
        knop.nummer = str(obj["id"])  # Het id uit de database is het nummer (aanpasbaar in het adminpaneel)

        # Toon de afbeelding alleen als het bestand echt bestaat
        if obj[3] and os.path.exists(obj[3]):
            knop.afbeelding = obj[3]

        # obj_id=obj["id"] zorgt dat elke knop zijn eigen id onthoudt
        knop.bind(on_release=lambda btn, obj_id=obj["id"]: self.open_object(obj_id))
        return knop

    def open_object(self, obj_id):
        # Wordt uitgevoerd als op een objectknop wordt gedrukt.
        # Vult de detailpagina met dit object en gaat er naartoe.
        self.manager.get_screen("object_detail").toon_object(obj_id)
        self.manager.current = "object_detail"

    def admin_tik(self):
        # Wordt uitgevoerd bij elke tik op de onzichtbare knop rechtsboven.
        # Pas bij 2 tikken kort na elkaar gaat het inlogscherm open.
        nu = time.time()
        if nu - self.vorige_admin_tik < DUBBELTIK_TIJD:
            self.vorige_admin_tik = 0  # Opnieuw beginnen met tellen
            self.go_to_admin()
        else:
            self.vorige_admin_tik = nu  # Eerste tik onthouden

    def go_to_admin(self):  # Functie/methode om te navigeren naar het beheerderscherm
        self.manager.current = "admin"  # Verander het huidige actieve scherm naar het scherm met de naam 'admin'

    def terug_naar_home(self):
        # Deze functie wordt uitgevoerd wanneer de gebruiker op de terugknop drukt.
        # Schakelt via de ScreenManager terug naar het homescreen.
        self.manager.current = "home"
