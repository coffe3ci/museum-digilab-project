import time  # Om te meten hoe snel twee tikken na elkaar komen

from kivy.uix.screenmanager import Screen  # Importeer de Screen-klasse uit Kivy om afzonderlijke schermen te maken

DUBBELTIK_TIJD = 0.6  # Maximaal aantal seconden tussen twee tikken op de geheime admin-knop


class HomeScreen(Screen):  # Definieer de HomeScreen-klasse die overerft van Screen (het hoofdscherm van de app)
    vorige_admin_tik = 0  # Tijdstip van de vorige tik op de geheime admin-knop

    def admin_tik(self):
        # Wordt uitgevoerd bij elke tik op de onzichtbare knop rechtsboven.
        # Pas bij 2 tikken kort na elkaar gaat het inlogscherm open.
        nu = time.time()
        if nu - self.vorige_admin_tik < DUBBELTIK_TIJD:
            self.vorige_admin_tik = 0  # Opnieuw beginnen met tellen
            self.go_to_admin()
        else:
            self.vorige_admin_tik = nu  # Eerste tik onthouden

    def go_to_admin(self):  # Functie/methode om te navigeren naar het beheerderscherm
        self.manager.current = "admin"  # Verander het huidige actieve scherm naar het scherm met de naam 'admin'

    def go_to_objects(self):
        self.manager.current = "objects"
