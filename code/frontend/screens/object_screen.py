import math  # Voor math.ceil: afronden naar boven bij het berekenen van het aantal pagina's

from kivy.metrics import dp  # Zet "dp"-waarden om naar pixels (zoals "30dp" in een .kv-bestand)
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget  # Lege widget, gebruikt als opvulling

from backend.object_manager import ObjectManager

PER_PAGINA = 9  # Aantal objectknoppen per pagina (3x3)


class ObjectScreen(Screen):
    objecten = []  # Alle objecten uit de database
    huidige_pagina = 1  # De pagina die nu getoond wordt

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
            knop = Button(text=obj["title"])
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
        print("Object", obj_id, "aangeklikt")

    def go_to_admin(self):  # Functie/methode om te navigeren naar het beheerderscherm
        self.manager.current = "admin"  # Verander het huidige actieve scherm naar het scherm met de naam 'admin'

    def terug_naar_home(self):
        # Deze functie wordt uitgevoerd wanneer de gebruiker op de terugknop drukt.
        # Schakelt via de ScreenManager terug naar het homescreen.
        self.manager.current = "home"
