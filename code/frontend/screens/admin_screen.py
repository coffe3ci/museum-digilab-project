import threading  # Wachtwoord controleren op de achtergrond, zodat het scherm niet "bevriest"

from kivy.clock import mainthread  # Resultaat terug op de hoofdthread (alleen daar mag de interface veranderen)
from kivy.logger import Logger  # Meldingen die op de tablet via "adb logcat" te zien zijn
from kivy.uix.screenmanager import Screen
# Importeert de Screen-klasse van Kivy.
# Deze klasse wordt gebruikt als basis voor het AdminScreen.

from backend.admin_manager import AdminManager
# Importeert de AdminManager uit de backend.
# Deze klasse controleert de inloggegevens van de beheerder.

STANDAARD_GEBRUIKERSNAAM = "admin"  # De gebruikersnaam van de beheerder


class AdminScreen(Screen):
# Maakt een nieuw scherm aan met de naam AdminScreen.
# Het scherm erft de eigenschappen van de Kivy Screen-klasse.

    _bezig = False  # True terwijl het wachtwoord gecontroleerd wordt (dubbel tikken voorkomen)

    def on_pre_enter(self):
        # Elke keer dat het inlogscherm opent: leeg veld en geen oude foutmelding
        self.ids.wachtwoord_veld.text = ""
        self.ids.foutmelding.text = ""
        self._zet_knop(bezig=False)

    def terug_naar_home(self):
    # Deze functie wordt uitgevoerd wanneer de gebruiker op de terugknop drukt.
    # De gebruiker wordt teruggebracht naar het beginscherm.
        self.ids.wachtwoord_veld.text = ""
        self.ids.foutmelding.text = ""
        self.manager.current = "home"

    def inloggen_actie(self, ingevoerde_wachtwoord):
    # Deze functie wordt uitgevoerd wanneer de gebruiker probeert in te loggen.
    # Het controleren (hashen) kost op de tablet even tijd; dat gebeurt daarom op de achtergrond,
    # met "Bezig met inloggen…" op de knop, zodat de app intussen gewoon blijft reageren.
        if self._bezig:
            return
        self._zet_knop(bezig=True)
        self.ids.foutmelding.text = ""

        # Hulp bij problemen op de tablet (zichtbaar via "adb logcat"); het wachtwoord zelf wordt
        # nooit gelogd, alleen de lengte en of er spaties aan begin/eind staan.
        Logger.info(f"Inloggen: {len(ingevoerde_wachtwoord)} tekens, spatie aan begin/eind: "
                    f"{ingevoerde_wachtwoord != ingevoerde_wachtwoord.strip()}")

        threading.Thread(target=self._controleer, args=(ingevoerde_wachtwoord,), daemon=True).start()

    def _controleer(self, wachtwoord):
        # Draait op de achtergrond (eigen databaseverbinding in deze thread)
        try:
            gelukt = AdminManager().login(STANDAARD_GEBRUIKERSNAAM, wachtwoord)
        except Exception as fout:
            Logger.exception(f"Inloggen mislukt door een fout: {fout}")
            gelukt = False
        self._klaar(gelukt)

    @mainthread
    def _klaar(self, gelukt):
        self._zet_knop(bezig=False)
        self.ids.wachtwoord_veld.text = ""  # Wachtwoord nooit in het veld laten staan
        if gelukt:
            Logger.info("Inloggen geslaagd")
            self.ids.foutmelding.text = ""
            self.manager.current = "admin_panel"  # Naar het beheerpaneel
        else:
            Logger.info("Inloggen: onjuist wachtwoord")
            self.ids.foutmelding.text = "Onjuist wachtwoord!"

    def _zet_knop(self, bezig):
        self._bezig = bezig
        knop = self.ids.inloggen_knop
        knop.disabled = bezig
        knop.text = "Bezig met inloggen…" if bezig else "Inloggen"
