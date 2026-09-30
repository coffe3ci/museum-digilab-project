
# os wordt gebruikt om te controleren of bestanden bestaan
# en om de wijzigingsdatum van bestanden te controleren.
import os

# threading wordt gebruikt om de bestandscontrole
# op de achtergrond te laten draaien.
import threading

# time wordt gebruikt om een korte wachttijd in de bestandscontrole te plaatsen.
import time


# App is de basis van iedere Kivy-applicatie.
from kivy.app import App

# Clock wordt gebruikt om functies veilig vanuit de Kivy-interface
# uit te voeren nadat een bestand is gewijzigd.
from kivy.clock import Clock

# Builder wordt gebruikt om KV-bestanden in Kivy te laden.
from kivy.lang import Builder

# ScreenManager beheert de verschillende schermen van de applicatie.
from kivy.uix.screenmanager import ScreenManager


# Importeert het homescreen van de applicatie.
from frontend.screens.home_screen import HomeScreen

# Importeert het inlogscherm voor de beheerder.
from frontend.screens.admin_screen import AdminScreen

# Importeert het beheerpaneel voor de museumobjecten.
from frontend.screens.admin_panel import AdminPanelScreen


# ============================================================
# MUSEUM APP
# ============================================================

class MuseumApp(App):
    # Dit is de hoofdklasse van de Kivy-applicatie.


    # ========================================================
    # KV-BESTANDEN
    # ========================================================

    kv_files = [
        # KV-bestand van het homescreen.
        "frontend/screens/home_screen.kv",

        # KV-bestand van het admin-inlogscherm.
        "frontend/screens/admin_screen.kv",

        # KV-bestand van het beheerpaneel.
        "frontend/screens/admin_panel.kv",
    ]


    # ========================================================
    # BUILD
    # ========================================================

    def build(self):
        # Deze functie wordt automatisch uitgevoerd wanneer
        # de Kivy-applicatie wordt gestart.


        # Laadt alle KV-bestanden die hierboven zijn opgegeven.
        self.load_kv_files()


        # Maakt een ScreenManager aan.
        # Deze manager zorgt ervoor dat we tussen schermen
        # kunnen navigeren.
        self.sm = ScreenManager()


        # Voegt het homescreen toe aan de ScreenManager.
        # De naam "home" wordt later gebruikt voor navigatie.
        self.sm.add_widget(
            HomeScreen(name="home")
        )


        # Voegt het admin-inlogscherm toe.
        # De naam "admin" wordt gebruikt om naar dit scherm te gaan.
        self.sm.add_widget(
            AdminScreen(name="admin")
        )


        # Voegt het adminpaneel toe.
        # De naam "admin_panel" wordt gebruikt om naar dit scherm te gaan.
        self.sm.add_widget(
            AdminPanelScreen(name="admin_panel")
        )


        # Start de automatische controle van de KV-bestanden.
        # Hierdoor hoeven we de applicatie tijdens het ontwikkelen
        # niet telkens volledig opnieuw te starten.
        self.start_file_watcher()


        # Geeft de ScreenManager terug aan Kivy.
        # De ScreenManager wordt daardoor de hoofdinterface van de app.
        return self.sm


    # ========================================================
    # KV-BESTANDEN LADEN
    # ========================================================

    def load_kv_files(self):
        # Deze functie laadt alle KV-bestanden opnieuw.


        # Doorloopt ieder KV-bestand uit de lijst.
        for file in self.kv_files:

            # Probeert eerst de oude versie van het KV-bestand
            # uit de Kivy Builder te verwijderen.
            try:
                Builder.unload_file(file)

            # Als het bestand nog niet eerder geladen is,
            # kan unload_file een fout geven.
            # Die fout negeren we bewust.
            except Exception:
                pass


        # Doorloopt opnieuw alle KV-bestanden.
        for file in self.kv_files:

            # Controleert of het KV-bestand daadwerkelijk bestaat.
            if os.path.exists(file):

                # Probeert het KV-bestand te laden.
                try:
                    Builder.load_file(
                        file,
                        encoding="utf-8"
                    )

                # Als het laden mislukt, wordt de fout in de terminal getoond.
                except Exception as e:
                    print(
                        f"Fout bij laden van {file}: {e}"
                    )


    # ========================================================
    # FILE WATCHER STARTEN
    # ========================================================

    def start_file_watcher(self):
        # Deze functie start een aparte thread
        # die de KV-bestanden controleert.


        # Maakt een nieuwe achtergrondthread aan.
        thread = threading.Thread(

            # De functie watch_files() wordt uitgevoerd
            # in de nieuwe thread.
            target=self.watch_files,

            # Daemon=True betekent dat de thread automatisch stopt
            # wanneer de hoofdapplicatie wordt afgesloten.
            daemon=True
        )


        # Start de achtergrondthread.
        thread.start()


    # ========================================================
    # KV-BESTANDEN CONTROLEREN
    # ========================================================

    def watch_files(self):
        # Deze functie controleert voortdurend
        # of een KV-bestand is gewijzigd.


        # Dictionary waarin de laatste wijzigingstijd
        # van ieder bestand wordt opgeslagen.
        last_modified = {}


        # Doorloopt alle KV-bestanden.
        for file in self.kv_files:

            # Controleert of het bestand bestaat.
            if os.path.exists(file):

                # Slaat de huidige wijzigingstijd van het bestand op.
                last_modified[file] = os.path.getmtime(file)


        # Deze lus blijft draaien zolang de applicatie actief is.
        while True:

            # Wacht een halve seconde voordat opnieuw wordt gecontroleerd.
            time.sleep(0.5)


            # Controleert ieder KV-bestand.
            for file in self.kv_files:


                # Als het bestand niet bestaat,
                # wordt dit bestand overgeslagen.
                if not os.path.exists(file):
                    continue


                # Leest de huidige wijzigingstijd van het bestand.
                current_modified = os.path.getmtime(file)


                # Haalt de vorige wijzigingstijd uit de dictionary.
                previous_modified = last_modified.get(file)


                # Als het bestand nog niet eerder geregistreerd was,
                # wordt de huidige tijd opgeslagen.
                if previous_modified is None:
                    last_modified[file] = current_modified
                    continue


                # Controleert of het bestand sinds de vorige controle
                # is gewijzigd.
                if current_modified != previous_modified:

                    # Slaat de nieuwe wijzigingstijd op.
                    last_modified[file] = current_modified


                    # Plant reload_kv() in op de Kivy Clock.
                    # Hierdoor wordt de interface op een veilige manier
                    # opnieuw geladen vanuit de hoofdthread.
                    Clock.schedule_once(
                        lambda dt: self.reload_kv()
                    )


    # ========================================================
    # KV-BESTANDEN OPNIEUW LADEN
    # ========================================================

    def reload_kv(self):
        # Deze functie wordt uitgevoerd wanneer een KV-bestand
        # is gewijzigd.


        # Probeert de huidige schermnaam op te slaan.
        try:
            current_screen = self.sm.current


            # Verwijdert alle schermen tijdelijk uit de ScreenManager.
            self.sm.clear_widgets()


            # Laadt alle KV-bestanden opnieuw.
            self.load_kv_files()


            # Voegt het homescreen opnieuw toe.
            self.sm.add_widget(
                HomeScreen(name="home")
            )


            # Voegt het admin-inlogscherm opnieuw toe.
            self.sm.add_widget(
                AdminScreen(name="admin")
            )


            # Voegt het adminpaneel opnieuw toe.
            self.sm.add_widget(
                AdminPanelScreen(name="admin_panel")
            )


            # Controleert of het vorige scherm nog bestaat.
            if current_screen in [
                "home",
                "admin",
                "admin_panel",
            ]:

                # Gaat terug naar hetzelfde scherm.
                self.sm.current = current_screen

            else:

                # Als het vorige scherm niet meer bestaat,
                # gaat de applicatie terug naar het homescreen.
                self.sm.current = "home"


            # Geeft in de terminal aan dat de KV-bestanden
            # succesvol opnieuw zijn geladen.
            print("KV-bestanden zijn vernieuwd.")


        # Als er tijdens het opnieuw laden een fout ontstaat,
        # wordt deze fout weergegeven in de terminal.
        except Exception as e:
            print(
                "Fout bij het vernieuwen van de KV-bestanden:",
                e
            )


# ============================================================
# APPLICATIE STARTEN
# ============================================================

if __name__ == "__main__":
    # Deze code wordt alleen uitgevoerd wanneer dev.py
    # rechtstreeks wordt gestart.

    MuseumApp().run()
    # Maakt de MuseumApp aan en start de Kivy-applicatie.

