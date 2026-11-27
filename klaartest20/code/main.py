# Geen rode cirkels bij een rechtermuisklik: Kivy gebruikt de rechterknop standaard om een
# "tweede vinger" (multitouch) na te doen. Dit moet vóór alle andere Kivy-imports staan.
from kivy.config import Config
from kivy.logger import Logger
from kivy.utils import platform

# LET OP: alleen op de pc! Op Android haalt Kivy zelf alle "mouse"-invoer weg, want de tablet geeft
# alleen vingers door. Zetten we de muis hier toch aan, dan komt elke aanraking TWEE keer binnen
# (één keer als vinger, één keer als nep-muis). Gevolgen: vegen springt 2 pagina's, 4x tikken wordt
# 2x tikken, het toetsenbord verdwijnt/opent dubbel en er blijft een "spook-aanraking" op het scherm.
if platform != "android":
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.clock import Clock  # Scherm een paar keer opnieuw tekenen na het opstarten
from kivy.app import App  # Importeer de hoofdklasse App uit Kivy om de applicatie te maken en uit te voeren
from kivy.core.window import Window  # Het venster (o.a. hoe het toetsenbord op de tablet werkt)
from kivy.lang import Builder  # Importeer Builder om Kivy (.kv) lay-outbestanden handmatig te laden
from kivy.uix.screenmanager import FadeTransition, ScreenManager  # Schermen beheren en snel wisselen
from kivy.uix.modalview import ModalView  # Pop-upvensters (om ze te sluiten als de timer afloopt)

from backend.object_manager import ObjectManager  # Tijden van de timers (instellingen in de database)

from frontend.screens.home_screen import HomeScreen  # Importeer de HomeScreen-klasse uit het betreffende bestand
from frontend.screens.admin_screen import AdminScreen  # Importeer de AdminScreen-klasse voor het inlogscherm
from frontend.screens.admin_panel import AdminPanelScreen  # Importeer de AdminPanelScreen-klasse voor het beheerderspaneel

from frontend.screens.object_screen import ObjectScreen
from frontend.screens.object_detail_screen import ObjectDetailScreen  # Detailpagina van één object
from frontend.fonts import registreer_fonts  # De lettertypes "Titel", "Tekst" en "Klein"
from frontend import kiosk  # Kioskmodus en andere tablet-instellingen

registreer_fonts()  # Moet gebeuren voordat de .kv-bestanden geladen worden

class MuseumApp(App):  # Definieer de hoofdklasse van de applicatie die overerft van Kivy App
    title = "Stadsmuseum Veenendaal"  # Naam bovenaan het venster (in plaats van "Museum")
    icon = "assets/images/icoon.png"  # Pictogram linksboven en in de taakbalk (beeldmerk van het museum)

    def build(self):  # De methode die de gebruikersinterface bouwt en initialiseert bij het opstarten
        Builder.load_file(  # Laad het lay-outbestand voor het startscherm
            "frontend/screens/home_screen.kv",  # Pad naar het KV-bestand van de home screen
            encoding="utf-8"  # Gebruik UTF-8 codering om speciale tekens correct te verwerken
        )

        Builder.load_file(  # Laad het lay-outbestand voor het inlogscherm
            "frontend/screens/admin_screen.kv",  # Pad naar het KV-bestand van de admin screen
            encoding="utf-8"  # Gebruik UTF-8 codering
        )

        Builder.load_file(  # Laad het lay-outbestand voor het beheerpaneel
            "frontend/screens/admin_panel.kv",  # Pad naar het KV-bestand van de admin panel screen
            encoding="utf-8"  # Gebruik UTF-8 codering
        )

        Builder.load_file(
            "frontend/screens/object_screen.kv",
            encoding="utf-8"
        )

        Builder.load_file(
            "frontend/screens/object_detail_screen.kv",
            encoding="utf-8"
        )


        # ScreenManager beheert alle schermen. Korte vervaging bij wisselen: de standaard schuifanimatie
        # (0,4 s, twee volledige schermen tegelijk tekenen) voelt op de tablet traag.
        sm = ScreenManager(transition=FadeTransition(duration=0.15))

        sm.add_widget(  # Voeg het startscherm toe aan de schermbeheerder
            HomeScreen(name="home")  # Maak een instantie van HomeScreen met de unieke naam 'home'
        )

        sm.add_widget(  # Voeg het inlogscherm toe aan de schermbeheerder
            AdminScreen(name="admin")  # Maak een instantie van AdminScreen met de unieke naam 'admin'
        )

        sm.add_widget(  # Voeg het beheerderspaneel toe aan de schermbeheerder
            AdminPanelScreen(name="admin_panel")  # Maak bir instantie van AdminPanelScreen met de unieke naam 'admin_panel'
        )

        sm.add_widget(
            ObjectScreen(name="objects")
        )

        sm.add_widget(
            ObjectDetailScreen(name="object_detail")
        )

        # Zorg dat het startscherm expliciet actief is zodra de app wordt getoond.
        sm.current = "home"

        # Timer: na een tijd zonder aanraking terug naar het startscherm. De tijd is per scherm
        # in te stellen in het adminpaneel (knop "Timers"). Elke aanraking, toets of ander scherm
        # begint de tijd opnieuw.
        self._sm = sm
        self._timer = None
        self.laad_timers()
        Window.bind(on_touch_down=self.herstart_timer, on_touch_move=self.herstart_timer,
                    on_key_down=self.herstart_timer, on_textinput=self.herstart_timer)
        sm.bind(current=self.herstart_timer)

        tablet_instellingen()  # Alleen op de tablet: toetsenbord, scherm aan houden
        return sm  # Geef de geconfigureerde ScreenManager terug als het hoofd-widget van de app

    def on_start(self):
        # Achtergrondkleur van het venster = kleur van de app (nooit zwart door), en na het opstarten
        # het scherm een paar seconden steeds opnieuw laten tekenen. Op sommige tablets bleef het
        # scherm zwart tot je het aanraakte (er werd gewoon geen nieuw beeld getoond).
        Window.clearcolor = (244 / 255, 239 / 255, 230 / 255, 1)
        # Op sommige Android-tablets wordt het eerste Kivy-frame te vroeg opgebouwd.
        # Daardoor is de achtergrond/inhoud pas zichtbaar na een aanraking. Plan daarom
        # enkele korte layout- en canvasverversingen direct na het tonen van het startscherm.
        for vertraging in (0, 0.08, 0.2, 0.4, 0.7, 1.1, 1.6):
            Clock.schedule_once(self._eerste_scherm_verversen, vertraging)
        self.forceer_tekenen(seconden=2)

    def _eerste_scherm_verversen(self, dt):
        if self.root is None:
            return
        try:
            self.root.current = "home"
            self.root.do_layout()
            huidig = self.root.get_screen("home")
            huidig.do_layout()
            huidig.canvas.ask_update()
            self.root.canvas.ask_update()
            Window.canvas.ask_update()
        except Exception as fout:
            Logger.warning(f"Startscherm: eerste verversing mislukt: {fout}")

    def forceer_tekenen(self, seconden=3):
        # Vraagt elke 0,2 seconde om een nieuw beeld, gedurende "seconden" seconden
        self._tekenen_tot = Clock.get_time() + seconden
        Clock.unschedule(self._teken_stap)
        Clock.schedule_interval(self._teken_stap, 0.3)

    def _teken_stap(self, dt):
        Window.canvas.ask_update()
        if self.root is not None:
            self.root.do_layout()
            self.root.canvas.ask_update()
            try:
                self.root.get_screen("home").canvas.ask_update()
            except Exception:
                pass
        return Clock.get_time() < self._tekenen_tot  # False = stoppen

    def laad_timers(self):
        # Leest de tijden uit de database (ook aangeroepen na "Opslaan" in het venster Timers).
        # Ze worden onthouden, zodat niet bij elke aanraking de database gelezen hoeft te worden.
        self.timers = ObjectManager().get_timers()
        self.herstart_timer()

    def herstart_timer(self, *args):
        # Zet de timer van het huidige scherm weer op nul. Geeft niets terug, zodat de
        # aanraking gewoon doorgaat naar de knoppen.
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        seconden = self.timers.get(self._sm.current, 0)  # startscherm heeft geen timer
        if seconden > 0:
            self._timer = Clock.schedule_once(self.te_lang_niet_aangeraakt, seconden)

    def te_lang_niet_aangeraakt(self, dt):
        # Te lang niemand aan het scherm: terug naar het startscherm, alles klaar voor de
        # volgende bezoeker (filter weer op "Alle objecten", wand weer vooraan).
        # Vanuit het beheerpaneel betekent dit ook: uitgelogd (opnieuw inloggen nodig).
        sm = self._sm
        if self.timers.get(sm.current, 0) <= 0:
            return
        Logger.info(f"Timer: {sm.current} te lang niet aangeraakt, terug naar het startscherm")
        # Open vensters (formulieren, meldingen) eerst sluiten; niet-opgeslagen wijzigingen vervallen
        for venster in [w for w in Window.children if isinstance(w, ModalView)]:
            venster.dismiss(animation=False)
        sm.get_screen("objects").terug_naar_home()

    def on_pause(self):
        # Android: app mag op de achtergrond gepauzeerd worden (bv. bij de systeemvraag van de
        # kioskmodus) in plaats van afgesloten
        return True

    def on_resume(self):
        self.forceer_tekenen(seconden=3)  # na terugkeren ook niet zwart blijven
        # Terug in de app: in kioskmodus de systeembalken opnieuw verbergen
        if kiosk.kiosk_actief():
            kiosk.verberg_balken()


def verwijder_muis_invoer():
    # Op de tablet mag alleen de vinger-invoer actief zijn. Staat er toch een muis-provider
    # (bv. door een oude configuratie), dan wordt elke tik dubbel geteld. Die halen we hier weg.
    try:
        from kivy.base import EventLoop  # noqa: PLC0415
        for provider in list(EventLoop.input_providers):
            if provider.__class__.__name__ == "MouseMotionEventProvider":
                EventLoop.remove_input_provider(provider)
                provider.stop()
                Logger.info("Invoer: muis-provider verwijderd (dubbele aanrakingen voorkomen)")
    except Exception as fout:
        Logger.warning(f"Invoer: muis-provider verwijderen lukte niet: {fout}")


def tablet_instellingen():
    # Instellingen die alleen op de Android-tablet nodig zijn
    if not kiosk.OP_TABLET:
        return
    # Het toetsenbord schuift het scherm omhoog zodat het actieve tekstveld zichtbaar blijft
    # (in plaats van het venster kleiner te maken; dat liet het toetsenbord in formulieren
    # meteen weer verdwijnen).
    Window.softinput_mode = "below_target"
    verwijder_muis_invoer()  # Extra zekerheid: nooit dubbele aanrakingen (vinger + nep-muis)
    kiosk.scherm_aan_houden()  # Scherm gaat niet vanzelf uit zolang de app open is
    if kiosk.kiosk_actief():
        kiosk.verberg_balken()


if __name__ == "__main__":  # Controleer of dit script rechtstreeks wordt uitgevoerd
    MuseumApp().run()  # Start en draai de Kivy-applicatie