import os  # Om te controleren of een afbeelding echt bestaat

from kivy.clock import Clock  # Om het herschikken van de zijkolom één keer per frame te doen
from kivy.factory import Factory  # Maakt ExtraFoto's aan (gedefinieerd in object_detail_screen.kv)
from kivy.metrics import dp  # Zet "dp"-waarden om naar pixels
from kivy.core.window import Window  # Schermgrootte (voor het voorbeeld in het adminpaneel)
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter  # Om het voorbeeld van de pagina te verkleinen
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from backend.object_manager import ObjectManager
from frontend.tekst_opmaak import opgemaakte_tekst  # Beschrijving + opmaak -> Kivy-markup

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


class PaginaInhoud(BoxLayout):
    # De inhoud van een objectpagina: schilderij (hoofdfoto), titel, beschrijving en extra foto's.
    # Wordt gebruikt op de echte objectpagina én (verkleind) als voorbeeld in het adminpaneel.
    # Hoe het eruitziet staat in object_detail_screen.kv (<PaginaInhoud>).
    titel = StringProperty("")  # Markup (met opmaak)
    beschrijving = StringProperty("")  # Markup (met opmaak)
    afbeelding = StringProperty("")  # Pad naar de hoofdfoto ("" = geen afbeelding)
    hoofd_hoogte_deel = NumericProperty(0.35)  # Grootte van de hoofdfoto (zie HOOFD_FORMATEN)
    boven_ruimte = NumericProperty(dp(70))  # Ruimte bovenaan (op de echte pagina voor de terug-knop)

    def zet_hoofdfoto(self, pad, formaat):
        # Toon de afbeelding alleen als het bestand echt bestaat
        self.afbeelding = pad if pad and os.path.exists(pad) else ""
        # Grootte van de hoofdfoto zoals gekozen in het adminpaneel ("Groot" en "groot" mogen allebei)
        self.hoofd_hoogte_deel = HOOFD_FORMATEN.get((formaat or "normaal").lower(), 0.35)

    def zet_extra_fotos(self, items):
        # Extra afbeeldingen: midden = onder de beschrijving, links/rechts = in een kolom ernaast
        extra_fotos = self.ids.extra_fotos
        kolom_links = self.ids.kolom_links
        kolom_rechts = self.ids.kolom_rechts
        for houder in (extra_fotos, kolom_links, kolom_rechts):
            houder.clear_widgets()

        for item in items:
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


class ObjectDetailScreen(Screen):
    # Eén pagina voor alle objecten: hij vult zichzelf met het object waarop geklikt is.

    def toon_object(self, obj_id):
        # Haalt het object op uit de database en zet de gegevens op de pagina
        obj = ObjectManager().get_object(obj_id)
        if obj is None:
            return

        inhoud = self.ids.inhoud
        # Titel en beschrijving met de opmaak uit het adminpaneel (vet, schuin, onderstreept, kleur) als markup
        inhoud.titel = opgemaakte_tekst(obj[1], obj["titel_opmaak"])
        inhoud.beschrijving = opgemaakte_tekst(obj[2], obj["opmaak"])
        inhoud.zet_hoofdfoto(obj[3], obj["hoofd_formaat"])
        inhoud.zet_extra_fotos(ObjectManager().get_extra_afbeeldingen(obj_id))

        self.ids.tekst_scroll.scroll_y = 1  # Begin bovenaan de beschrijving

    def terug(self):
        # Terug naar het overzicht met alle objecten
        self.manager.current = "objects"


class PaginaVoorbeeld(Widget):
    # Verkleind voorbeeld van de objectpagina (voor het formulier in het adminpaneel).
    # De pagina wordt opgebouwd op de echte schermgrootte en daarna verkleind (Scatter),
    # zodat foto's, tekst en kolommen precies dezelfde verhoudingen hebben als op de echte pagina.
    titel = StringProperty("")  # Markup (met opmaak)
    beschrijving = StringProperty("")  # Markup (met opmaak)
    afbeelding = StringProperty("")  # Pad naar de hoofdfoto
    hoofd_formaat = StringProperty("normaal")  # "klein", "normaal", "groot" of "origineel"
    extra = ListProperty([])  # Extra afbeeldingen (dicts zoals in ObjectManager.get_extra_afbeeldingen)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inhoud = PaginaInhoud(boven_ruimte=dp(30))  # Geen terug-knop, dus minder ruimte bovenaan
        self.verkleiner = Scatter(do_rotation=False, do_scale=False, do_translation=False,
                                  size_hint=(None, None))
        self.verkleiner.add_widget(self.inhoud)
        self.add_widget(self.verkleiner)
        self.on_titel()
        self.on_beschrijving()

        # Foto's opnieuw opbouwen kost meer tijd: alleen als de foto's veranderen, niet bij elke letter
        self._fotos_later = Clock.create_trigger(self._zet_fotos)
        self.bind(afbeelding=self._fotos_later, hoofd_formaat=self._fotos_later, extra=self._fotos_later)
        self._fotos_later()

        self._schik_later = Clock.create_trigger(self._schik)
        self.bind(pos=self._schik_later, width=self._schik_later)
        self.inhoud.bind(height=self._schik_later)
        Window.bind(size=self._schik_later)

    # (Kivy kan deze al aanroepen voordat __init__ klaar is; dan bestaat self.inhoud nog niet)
    def on_titel(self, *args):
        if hasattr(self, "inhoud"):
            self.inhoud.titel = self.titel or "[color=#999999](geen titel)[/color]"

    def on_beschrijving(self, *args):
        if hasattr(self, "inhoud"):
            self.inhoud.beschrijving = self.beschrijving or "[color=#999999](nog geen beschrijving)[/color]"

    def _zet_fotos(self, *args):
        self.inhoud.zet_hoofdfoto(self.afbeelding, self.hoofd_formaat)
        self.inhoud.zet_extra_fotos(self.extra)

    def _schik(self, *args):
        # De pagina is zo breed als het echte scherm; het voorbeeld verkleint hem tot de eigen breedte
        breedte = Window.width
        schaal = self.width / breedte if breedte else 1
        self.inhoud.width = breedte
        self.verkleiner.scale = schaal
        self.verkleiner.size = (breedte, self.inhoud.height)
        self.verkleiner.pos = self.pos
        self.height = self.inhoud.height * schaal

    # Het voorbeeld is alleen om naar te kijken: aanrakingen gaan door naar het formulier (scrollen)
    def on_touch_down(self, touch):
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_up(self, touch):
        return False
