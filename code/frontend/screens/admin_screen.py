from kivy.uix.screenmanager import Screen
# Importeert de Screen-klasse van Kivy.
# Deze klasse wordt gebruikt als basis voor het AdminScreen.

from backend.admin_manager import AdminManager
# Importeert de AdminManager uit de backend.
# Deze klasse controleert de inloggegevens van de beheerder.


class AdminScreen(Screen):
# Maakt een nieuw scherm aan met de naam AdminScreen.
# Het scherm erft de eigenschappen van de Kivy Screen-klasse.


    def __init__(self, **kwargs):
    # Deze functie wordt automatisch uitgevoerd wanneer het scherm wordt aangemaakt.
    # **kwargs ontvangt extra instellingen die door Kivy worden meegegeven.

        super().__init__(**kwargs)
        # Voert de constructor van de bovenliggende Screen-klasse uit.
        # Hierdoor wordt het scherm correct door Kivy ingesteld.

        self.beheerder = AdminManager()
        # Maakt een AdminManager-object aan.
        # Dit object wordt gebruikt om de inloggegevens te controleren.


    def terug_naar_home(self):
    # Deze functie wordt uitgevoerd wanneer de gebruiker op de terugknop drukt.
    # De gebruiker wordt teruggebracht naar het beginscherm.

        # Wachtwoord wissen
        # Maakt het wachtwoordveld leeg.
        self.ids.wachtwoord_veld.text = ""

        # Foutmelding wissen
        # Verwijdert een eventuele foutmelding van het scherm.
        self.ids.foutmelding.text = ""

        # Terug naar home
        # Schakelt via de ScreenManager terug naar het homescreen.
        self.manager.current = "home"

    def inloggen_actie(self, ingevoerde_wachtwoord):
    # Deze functie wordt uitgevoerd wanneer de gebruiker probeert in te loggen.
    # Het ingevoerde wachtwoord wordt gecontroleerd.

        standaard_gebruikersnaam = "admin"
        # Stelt de standaard gebruikersnaam van de beheerder in.

        # Controleer login
        # Controleert of de ingevoerde inloggegevens correct zijn.
        is_gelukt = self.beheerder.login(
            standaard_gebruikersnaam,
            ingevoerde_wachtwoord
        )
        # Roept de login-functie van AdminManager aan.
        # Het resultaat is True wanneer de gegevens correct zijn
        # en False wanneer de gegevens niet correct zijn.

        if is_gelukt:
        # Deze code wordt uitgevoerd wanneer het inloggen succesvol is.

            print("Inloggen geslaagd!")
            # Toont in de terminal dat het inloggen succesvol is.

            # Wachtwoordveld leegmaken
            # Maakt het wachtwoordveld leeg nadat het inloggen is gelukt.
            self.ids.wachtwoord_veld.text = ""

            # Foutmelding verwijderen
            # Verwijdert een eventuele eerdere foutmelding.
            self.ids.foutmelding.text = ""

            # Naar admin panel
            # Gaat naar het beheerpaneel.
            self.manager.current = "admin_panel"

        else:
        # Deze code wordt uitgevoerd wanneer het inloggen mislukt.

            print("Onjuist wachtwoord!")
            # Toont in de terminal dat het wachtwoord onjuist is.

            # Wachtwoordveld leegmaken
            # Maakt het wachtwoordveld leeg na een mislukte inlogpoging.
            self.ids.wachtwoord_veld.text = ""

            # Foutmelding tonen
            # Toont een foutmelding aan de gebruiker.
            self.ids.foutmelding.text = "Onjuist wachtwoord!"
