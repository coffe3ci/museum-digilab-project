from kivy.uix.screenmanager import Screen  # Importeer de Screen-klasse uit Kivy om afzonderlijke schermen te maken


class HomeScreen(Screen):  # Definieer de HomeScreen-klasse die overerft van Screen (het hoofdscherm van de app)

    def go_to_admin(self):  # Functie/methode om te navigeren naar het beheerderscherm
        self.manager.current = "admin"  # Verander het huidige actieve scherm naar het scherm met de naam 'admin'

    def go_to_objects(self):
        self.manager.current = "objects"
