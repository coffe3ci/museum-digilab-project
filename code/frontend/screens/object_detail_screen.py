import os  # Om te controleren of een afbeelding echt bestaat

from kivy.clock import Clock  # Om het herschikken van de zijkolom één keer per frame te doen
from kivy.factory import Factory  # Maakt ExtraFoto's aan (gedefinieerd in object_detail_screen.kv)
from kivy.metrics import dp  # Zet "dp"-waarden om naar pixels
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from backend.object_manager import ObjectManager
from frontend.fonts import voor_titel  # Vervangt tekens die het Stanley-font niet heeft

TUSSENRUIMTE = dp(20)  # Ruimte tussen foto's die automatisch onder elkaar staan

# Maximale breedte x hoogte (dp) per grootte-keuze in het adminpaneel.
# De foto past in dit vak en houdt zijn vorm. "origineel" staat hier niet in:
# die toont de foto op zijn echte grootte (zie ExtraFoto in object_detail_screen.kv).
FORMATEN = {
    "klein": (150, 150),
    "normaal": (250, 250),
    "groot": (350, 350),
}

# Hoogte van de hoofdfoto (het schilderij bovenaan) als deel van de schermhoogte.
# 0 = origineel: de foto op zijn echte grootte (nooit breder dan de pagina).
HOOFD_FORMATEN = {
    "klein": 0.25,
    "normaal": 0.35,
    "groot": 0.50,
    "origineel": 0,
}


class ZijKolom(FloatLayout):
    # Kolom links of rechts naast de beschrijving met extra foto's.
    # Foto's met een "hoogte vanaf boven" staan precies op die plek;
    # foto's zonder hoogte worden automatisch van boven naar beneden onder elkaar gezet.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._herschik_later = Clock.create_trigger(self.herschik)
        self.bind(size=self._herschik_later, pos=self._herschik_later)

    def voeg_foto_toe(self, blok, positie_hoogte):
        # positie_hoogte = dp vanaf de bovenkant, of None = automatisch onder elkaar
        blok.positie_hoogte = positie_hoogte
        blok.size_hint = (1, None)  # Zo breed als de kolom
        blok.bind(height=self._herschik_later)  # Foto geladen of van grootte veranderd: opnieuw schikken
        self.add_widget(blok)

    def herschik(self, *args):
        boven_auto = 0  # Waar de volgende automatische foto komt (afstand vanaf boven)
        laagste = 0  # Onderkant van de laagste foto = benodigde hoogte van de kolom

        for blok in reversed(self.children):  # children staat in omgekeerde volgorde van toevoegen
            if blok.positie_hoogte is not None:
                boven = dp(blok.positie_hoogte)  # Vaste plek die in het adminpaneel is ingevuld
            else:
                boven = boven_auto
                boven_auto = boven + blok.height + TUSSENRUIMTE

            blok.x = self.x
            blok.top = self.top - boven
            laagste = max(laagste, boven + blok.height)

        self.height = laagste


class ObjectDetailScreen(Screen):
    # Eén pagina voor alle objecten: hij vult zichzelf met het object waarop geklikt is.
    titel = StringProperty("")
    beschrijving = StringProperty("")
    afbeelding = StringProperty("")  # Pad naar de afbeelding ("" = geen afbeelding)
    hoofd_hoogte_deel = NumericProperty(0.35)  # Grootte van de hoofdfoto (zie HOOFD_FORMATEN)

    def toon_object(self, obj_id):
        # Haalt het object op uit de database en zet de gegevens op de pagina
        obj = ObjectManager().get_object(obj_id)
        if obj is None:
            return

        self.titel = voor_titel(obj[1])  # tekens die het titelfont niet heeft worden vervangen
        self.beschrijving = obj[2] or ""

        # Toon de afbeelding alleen als het bestand echt bestaat
        self.afbeelding = obj[3] if obj[3] and os.path.exists(obj[3]) else ""
        # Grootte van de hoofdfoto zoals gekozen in het adminpaneel
        self.hoofd_hoogte_deel = HOOFD_FORMATEN.get(obj["hoofd_formaat"], 0.35)

        # Extra afbeeldingen: midden = onder de beschrijving, links/rechts = in een kolom ernaast
        extra_fotos = self.ids.extra_fotos
        kolom_links = self.ids.kolom_links
        kolom_rechts = self.ids.kolom_rechts
        for houder in (extra_fotos, kolom_links, kolom_rechts):
            houder.clear_widgets()

        for item in ObjectManager().get_extra_afbeeldingen(obj_id):
            if not os.path.exists(item["pad"]):  # Alleen bestanden die echt bestaan
                continue

            blok = Factory.ExtraFotoBlok()  # foto met de titel eronder
            foto = blok.ids.foto
            # Eigen grootte (als ingevuld) gaat voor de keuze klein/normaal/groot/origineel
            if item["breedte"] or item["hoogte"]:
                foto.max_breedte = item["breedte"] or 0  # 0 = geen limiet
                foto.max_hoogte = item["hoogte"] or 0
            else:
                foto.origineel = item["formaat"] == "origineel"  # echte grootte van de foto
                foto.max_breedte, foto.max_hoogte = FORMATEN.get(item["formaat"], (0, 0))
            foto.source = item["pad"]
            # Titel alleen onder de foto als het vinkje in het adminpaneel aan staat
            blok.ids.onderschrift.text = item["titel"] if item["titel_zichtbaar"] else ""

            if item["positie"] == "links":
                kolom_links.voeg_foto_toe(blok, item["positie_hoogte"])
            elif item["positie"] == "rechts":
                kolom_rechts.voeg_foto_toe(blok, item["positie_hoogte"])
            else:
                extra_fotos.add_widget(blok)

        self.ids.tekst_scroll.scroll_y = 1  # Begin bovenaan de beschrijving

    def terug(self):
        # Terug naar het overzicht met alle objecten
        self.manager.current = "objects"
