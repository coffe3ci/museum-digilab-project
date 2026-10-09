from kivy.app import App  # Importeer de hoofdklasse App uit Kivy om de applicatie te maken en uit te voeren
from kivy.lang import Builder  # Importeer Builder om Kivy (.kv) lay-outbestanden handmatig te laden
from kivy.uix.screenmanager import ScreenManager  # Importeer ScreenManager om tussen verschillende schermen te navigeren

from frontend.screens.home_screen import HomeScreen  # Importeer de HomeScreen-klasse uit het betreffende bestand
from frontend.screens.admin_screen import AdminScreen  # Importeer de AdminScreen-klasse voor het inlogscherm
from frontend.screens.admin_panel import AdminPanelScreen  # Importeer de AdminPanelScreen-klasse voor het beheerderspaneel

from frontend.screens.object_screen import ObjectScreen

class MuseumApp(App):  # Definieer de hoofdklasse van de applicatie die overerft van Kivy App

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


        sm = ScreenManager()  # Maak een nieuwe ScreenManager-instantie aan die alle schermen gaat beheren

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

        return sm  # Geef de geconfigureerde ScreenManager terug als het hoofd-widget van de app


if __name__ == "__main__":  # Controleer of dit script rechtstreeks wordt uitgevoerd
    MuseumApp().run()  # Start en draai de Kivy-applicatie