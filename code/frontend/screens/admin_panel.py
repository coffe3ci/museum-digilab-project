import os      # om te controleren of bestanden en mappen bestaan
import shutil  # om bestanden te kopiëren
import time    # voor een unieke bestandsnaam

from kivy.factory import Factory # Hiermee maken we ObjectItems aan (gedefinieerd in admin_panel.kv)
from kivy.uix.screenmanager import Screen # Basisklasse voor schermen

from backend.object_manager import ObjectManager # Haalt de objecten uit de database

AFBEELDING_MAP = "assets/objects_img"  # hier worden de afbeeldingen naartoe gekopieerd

class AdminPanelScreen(Screen):
    def on_enter(self):
        self.laad_objecten() # Laadt de objecten elke keer dat het adminpaneel geopend wordt

    def laad_objecten(self):
        lijst = self.ids.objecten_lijst
        lijst.clear_widgets() # Verwijdert de oude lijst

        objecten = ObjectManager().get_all_objects()
        for obj in objecten:
            item = Factory.ObjectItem()
            item.object_naam = f"{obj[1]}, {obj[2]}"
            item.object_id = obj["id"]
            item.afbeelding = obj[3] or ""  # obj[3] = afbeelding (None wordt "")
            lijst.add_widget(item)

        self.ids.aantal_label.text = f"{len(objecten)} OBJECTEN" # Toont het echte aantal objecten

    def terug_naar_home(self):
        self.manager.current = "home" # Navigeert terug naar het hoofdscherm

    def object_toevoegen(self):
        formulier = Factory.ObjectFormulier() # Leeg formulier (obj_id blijft 0 = nieuw object)
        formulier.open()

    def object_bewerken(self, obj_id):
        obj = ObjectManager().get_object(obj_id)
        if obj is None:
            return

        formulier = Factory.ObjectFormulier()
        formulier.obj_id = obj_id # Onthoudt welk object bewerkt wordt
        formulier.ids.titel.text = obj[1] # Vult de huidige gegevens in
        formulier.ids.beschrijving.text = obj[2]
        formulier.afbeelding = obj[3] or ""
        formulier.open()

    def formulier_opslaan(self, formulier):
        titel = formulier.ids.titel.text.strip()
        beschrijving = formulier.ids.beschrijving.text.strip()

        # Titel en beschrijving zijn verplicht in de database
        if not titel or not beschrijving:
            formulier.ids.foutmelding.text = "Vul een titel en beschrijving in."
            return

        afbeelding = formulier.afbeelding or None  # "" wordt None (leeg) in de database

        if formulier.obj_id == 0:
            ObjectManager().add_object(titel, beschrijving, afbeelding) # Nieuw object
        else:
            ObjectManager().update_object(formulier.obj_id, titel, beschrijving, afbeelding) # Bestaand object

        formulier.dismiss()
        self.laad_objecten() # Ververst de lijst

    def object_verwijderen(self, obj_id, object_naam):
        bevestiging = Factory.BevestigVerwijderen() # Vraagt eerst "Weet je het zeker?"
        bevestiging.obj_id = obj_id
        bevestiging.object_naam = object_naam
        bevestiging.open()

    def verwijderen_bevestigd(self, bevestiging):
        ObjectManager().delete_object(bevestiging.obj_id)
        bevestiging.dismiss()
        self.laad_objecten() # Ververst de lijst

    def uitloggen(self):
        self.manager.current = "admin" # Stuurt beheerder terug naar inlogscherm

    def kies_afbeelding(self, formulier):
        kiezer = Factory.AfbeeldingKiezer()
        kiezer.formulier = formulier  # onthoud voor welk formulier het is

        # Begin in de map Afbeeldingen (Pictures), anders in je gebruikersmap
        start = os.path.join(os.path.expanduser("~"), "Pictures")
        kiezer.ids.kiezer.path = start if os.path.isdir(start) else os.path.expanduser("~")
        kiezer.open()

    def afbeelding_gekozen(self, kiezer):
        selectie = kiezer.ids.kiezer.selection
        if not selectie:  # niets geselecteerd
            return

        bron = selectie[0]
        # Tijdstempel voor de naam, zodat twee bestanden met de naam "foto.png" elkaar niet overschrijven
        naam = f"{int(time.time())}_{os.path.basename(bron)}"
        doel = f"{AFBEELDING_MAP}/{naam}"

        shutil.copy(bron, doel)             # kopieer naar het project
        kiezer.formulier.afbeelding = doel  # het voorbeeld in het formulier verandert vanzelf
        kiezer.dismiss()


    