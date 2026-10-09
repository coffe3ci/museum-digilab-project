import math  # Voor math.ceil: afronden naar boven bij het berekenen van het aantal pagina's
import os  # Om te controleren of een afbeelding echt bestaat
import time  # Om te meten hoe snel twee tikken na elkaar komen

from kivy.core.image import Image as CoreImage  # Laadt een afbeelding als textuur om zelf te tekenen
from kivy.metrics import dp  # Zet "dp"-waarden om naar pixels (zoals "30dp" in een .kv-bestand)
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget  # Lege widget, gebruikt als opvulling

from backend.object_manager import ObjectManager

PER_PAGINA = 9  # Aantal objectknoppen per pagina (3x3)
DUBBELTIK_TIJD = 0.6  # Maximaal aantal seconden tussen twee tikken op de geheime admin-knop


class ObjectKnop(ButtonBehavior, FloatLayout):
    # Een knop met een afbeelding die de hele knop vult, met afgeronde hoeken.
    # Hoe hij eruitziet staat in object_screen.kv (<ObjectKnop>).
    titel = StringProperty("")
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
    huidige_pagina = 1  # De pagina die nu getoond wordt
    vorige_admin_tik = 0  # Tijdstip van de vorige tik op de geheime admin-knop

    def on_enter(self):
        # Wordt automatisch uitgevoerd elke keer dat dit scherm geopend wordt.
        # Zo zijn nieuwe objecten uit het adminpaneel direct zichtbaar.
        self.objecten = ObjectManager().get_all_objects()
        self.huidige_pagina = 1
        self.toon_pagina()

    def toon_pagina(self):
        # Vult het raster met de objectknoppen van de huidige pagina.
        grid = self.ids.grid
        grid.clear_widgets()  # Verwijder de knoppen van de vorige pagina

        # Pak de 9 objecten die bij deze pagina horen
        start = (self.huidige_pagina - 1) * PER_PAGINA
        pagina_objecten = self.objecten[start:start + PER_PAGINA]

        for obj in pagina_objecten:
            knop = ObjectKnop()
            knop.titel = obj[1]

            # Toon de afbeelding alleen als het bestand echt bestaat
            if obj[3] and os.path.exists(obj[3]):
                knop.afbeelding = obj[3]

            # obj_id=obj["id"] zorgt dat elke knop zijn eigen id onthoudt
            knop.bind(on_release=lambda btn, obj_id=obj["id"]: self.open_object(obj_id))
            grid.add_widget(knop)

        # Vul lege plekken op, zodat de knoppen niet te groot worden
        for _ in range(PER_PAGINA - len(pagina_objecten)):
            grid.add_widget(Widget())

        self.maak_paginaknoppen()

    def maak_paginaknoppen(self):
        # Maakt onder het raster één kleine knop per pagina.
        balk = self.ids.pagina_knoppen
        balk.clear_widgets()

        aantal_paginas = math.ceil(len(self.objecten) / PER_PAGINA)

        # Bij 1 pagina of minder zijn er geen paginaknoppen nodig
        if aantal_paginas <= 1:
            return

        balk.add_widget(Widget())  # Lege ruimte links (centreert de knoppen)
        for nr in range(1, aantal_paginas + 1):
            knop = Button(text=str(nr), size_hint=(None, None), size=(dp(30), dp(30)))
            # nr=nr zorgt dat elke knop zijn eigen paginanummer onthoudt
            knop.bind(on_release=lambda btn, nr=nr: self.go_to_page(nr))
            balk.add_widget(knop)
        balk.add_widget(Widget())  # Lege ruimte rechts

    def go_to_page(self, pagina):
        # Wordt uitgevoerd als op een paginaknop wordt gedrukt.
        self.huidige_pagina = pagina
        self.toon_pagina()

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
