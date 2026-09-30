from kivy.uix.screenmanager import Screen # Basisklasse voor schermen

class AdminPanelScreen(Screen):
    def terug_naar_home(self):
        self.manager.current = "home" # Navigeert terug naar het hoofdscherm

    def object_toevoegen(self):
        print("Object toevoegen knop ingedrukt") # Navigeer naar toevoegscherm
        
    
    def object_bewerken(self, object_naam):
        print(f"Bewerken: {object_naam}")

    def object_verwijderen(self, object_naam):
        print(f"Verwijderen: {object_naam}")

    def uitloggen(self):
        self.manager.current = "admin" # Stuurt beheerder terug naar inlogscherm