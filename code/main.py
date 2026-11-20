# Geen rode cirkels bij een rechtermuisklik: Kivy gebruikt de rechterknop standaard om een
# "tweede vinger" (multitouch) na te doen. Dit moet vóór alle andere Kivy-imports staan.
from kivy.config import Config
Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.app import App  # Importeer de hoofdklasse App uit Kivy om de applicatie te maken en uit te voeren
from kivy.core.window import Window  # Het venster (o.a. hoe het toetsenbord op de tablet werkt)
from kivy.lang import Builder  # Importeer Builder om Kivy (.kv) lay-outbestanden handmatig te laden
from kivy.uix.screenmanager import FadeTransition, ScreenManager  # Schermen beheren en snel wisselen

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

        tablet_instellingen()  # Alleen op de tablet: toetsenbord, scherm aan houden
        return sm  # Geef de geconfigureerde ScreenManager terug als het hoofd-widget van de app

    def on_pause(self):
        # Android: app mag op de achtergrond gepauzeerd worden (bv. bij de systeemvraag van de
        # kioskmodus) in plaats van afgesloten
        return True

    def on_resume(self):
        # Terug in de app: in kioskmodus de systeembalken opnieuw verbergen
        if kiosk.kiosk_actief():
            kiosk.verberg_balken()


def tablet_instellingen():
    # Instellingen die alleen op de Android-tablet nodig zijn
    if not kiosk.OP_TABLET:
        return
    # Het toetsenbord schuift het scherm omhoog zodat het actieve tekstveld zichtbaar blijft
    # (in plaats van het venster kleiner te maken; dat liet het toetsenbord in formulieren
    # meteen weer verdwijnen).
    Window.softinput_mode = "below_target"
    kiosk.scherm_aan_houden()  # Scherm gaat niet vanzelf uit zolang de app open is
    if kiosk.kiosk_actief():
        kiosk.verberg_balken()


if __name__ == "__main__":  # Controleer of dit script rechtstreeks wordt uitgevoerd
    MuseumApp().run()  # Start en draai de Kivy-applicatie