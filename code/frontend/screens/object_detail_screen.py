import os  # Om te controleren of een afbeelding echt bestaat

from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen

from backend.object_manager import ObjectManager


class ObjectDetailScreen(Screen):
    # Eén pagina voor alle objecten: hij vult zichzelf met het object waarop geklikt is.
    titel = StringProperty("")
    beschrijving = StringProperty("")
    afbeelding = StringProperty("")  # Pad naar de afbeelding ("" = geen afbeelding)

    def toon_object(self, obj_id):
        # Haalt het object op uit de database en zet de gegevens op de pagina
        obj = ObjectManager().get_object(obj_id)
        if obj is None:
            return

        self.titel = obj[1]
        self.beschrijving = obj[2] or ""

        # Toon de afbeelding alleen als het bestand echt bestaat
        self.afbeelding = obj[3] if obj[3] and os.path.exists(obj[3]) else ""

        self.ids.tekst_scroll.scroll_y = 1  # Begin bovenaan de beschrijving

    def terug(self):
        # Terug naar het overzicht met alle objecten
        self.manager.current = "objects"
