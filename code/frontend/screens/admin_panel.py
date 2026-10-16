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
            item.nummer = str(obj["id"])  # Het id is ook het nummer op de objectenwand
            item.afbeelding = obj[3] or ""  # obj[3] = afbeelding (None wordt "")
            lijst.add_widget(item)

        self.ids.aantal_label.text = f"{len(objecten)} OBJECTEN" # Toont het echte aantal objecten

    def terug_naar_home(self):
        self.manager.current = "home" # Navigeert terug naar het hoofdscherm

    def object_toevoegen(self):
        formulier = Factory.ObjectFormulier() # Leeg formulier (obj_id blijft 0 = nieuw object)
        formulier.ids.nummer.text = str(len(ObjectManager().get_all_objects()) + 1) # Standaard achteraan
        self.toon_extra_afbeeldingen(formulier)
        formulier.open()

    def object_bewerken(self, obj_id):
        obj = ObjectManager().get_object(obj_id)
        if obj is None:
            return

        formulier = Factory.ObjectFormulier()
        formulier.obj_id = obj_id # Onthoudt welk object bewerkt wordt
        formulier.ids.nummer.text = str(obj["id"]) # Vult de huidige gegevens in
        formulier.ids.titel.text = obj[1]
        formulier.ids.beschrijving.text = obj[2]
        formulier.afbeelding = obj[3] or ""
        formulier.extra_afbeeldingen = ObjectManager().get_extra_afbeeldingen(obj_id)
        self.toon_extra_afbeeldingen(formulier)
        formulier.open()

    def formulier_opslaan(self, formulier):
        titel = formulier.ids.titel.text.strip()
        beschrijving = formulier.ids.beschrijving.text.strip()

        # Titel en beschrijving zijn verplicht in de database
        if not titel or not beschrijving:
            formulier.ids.foutmelding.text = "Vul een titel en beschrijving in."
            return

        # Het nummer bepaalt de plek op de objectenwand
        nummer_tekst = formulier.ids.nummer.text.strip()
        if not nummer_tekst.isdigit() or int(nummer_tekst) == 0:
            formulier.ids.foutmelding.text = "Vul een geldig nummer in."
            return
        nummer = int(nummer_tekst)

        afbeelding = formulier.afbeelding or None  # "" wordt None (leeg) in de database

        if formulier.obj_id == 0:
            obj_id = ObjectManager().add_object(titel, beschrijving, afbeelding) # Nieuw object (achteraan)
        else:
            obj_id = formulier.obj_id
            ObjectManager().update_object(obj_id, titel, beschrijving, afbeelding) # Bestaand object

        # Extra afbeeldingen opslaan (voor het ruilen, dan verhuizen ze vanzelf mee)
        ObjectManager().zet_extra_afbeeldingen(obj_id, formulier.extra_afbeeldingen)

        # Zet het object op het gekozen nummer; het object dat daar stond ruilt van plek
        ObjectManager().verander_nummer(obj_id, nummer)

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

    def open_kiezer(self, formulier, doel):
        # Opent de bestandskiezer. doel = "hoofd" (hoofdafbeelding van het object)
        # of "extra" (de afbeelding in het paneel voor een extra afbeelding)
        kiezer = Factory.AfbeeldingKiezer()
        kiezer.formulier = formulier  # onthoud voor welk formulier/paneel het is
        kiezer.doel = doel

        # Begin in de map Afbeeldingen (Pictures), anders in je gebruikersmap
        start = os.path.join(os.path.expanduser("~"), "Pictures")
        kiezer.ids.kiezer.path = start if os.path.isdir(start) else os.path.expanduser("~")
        kiezer.open()

    def kies_afbeelding(self, formulier):
        self.open_kiezer(formulier, "hoofd")

    def afbeelding_gekozen(self, kiezer):
        selectie = kiezer.ids.kiezer.selection
        if not selectie:  # niets geselecteerd
            return

        bron = selectie[0]
        # Tijdstempel voor de naam, zodat twee bestanden met de naam "foto.png" elkaar niet overschrijven
        naam = f"{int(time.time())}_{os.path.basename(bron)}"
        doel = f"{AFBEELDING_MAP}/{naam}"
        shutil.copy(bron, doel)  # kopieer naar het project

        formulier = kiezer.formulier
        formulier.afbeelding = doel  # het voorbeeld in het formulier/paneel verandert vanzelf

        # Extra afbeelding zonder titel: vul de bestandsnaam (zonder extensie) alvast in
        if kiezer.doel == "extra" and not formulier.ids.titel.text.strip():
            formulier.ids.titel.text = os.path.splitext(os.path.basename(bron))[0]
        kiezer.dismiss()

    # ---------- Extra afbeeldingen (onder de beschrijving) ----------

    def toon_extra_afbeeldingen(self, formulier):
        # Bouwt in het objectformulier de lijst met titels van de extra afbeeldingen opnieuw op
        lijst = formulier.ids.extra_lijst
        lijst.clear_widgets()

        if not formulier.extra_afbeeldingen:
            lijst.add_widget(Factory.ExtraLeegLabel())  # "Nog geen extra afbeeldingen"
            return

        for index, item in enumerate(formulier.extra_afbeeldingen):
            knop = Factory.ExtraTitelKnop()
            knop.text = f"{index + 1}. {item['titel']}  ({item['positie']})"
            if not item["titel_zichtbaar"]:
                knop.text += "  (titel verborgen)"  # zo zie je meteen dat de titel niet op de pagina staat
            # index=index zorgt dat elke knop zijn eigen plek in de lijst onthoudt
            knop.bind(on_release=lambda btn, index=index: self.open_extra_formulier(formulier, index))
            lijst.add_widget(knop)

    def open_extra_formulier(self, formulier, index):
        # Opent het paneel voor één extra afbeelding. index = -1 betekent: nieuwe afbeelding
        paneel = Factory.ExtraAfbeeldingFormulier()
        paneel.formulier = formulier
        paneel.index = index

        if index >= 0:
            item = formulier.extra_afbeeldingen[index]
            paneel.afbeelding = item["pad"]
            paneel.ids.titel.text = item["titel"]
            paneel.ids.breedte.text = str(item["breedte"] or "")
            paneel.ids.hoogte.text = str(item["hoogte"] or "")
            paneel.ids.titel_zichtbaar.active = item["titel_zichtbaar"]
            paneel.ids.positie.text = item["positie"].capitalize()  # "links" -> "Links"
            paneel.ids.formaat.text = item["formaat"].capitalize()  # "klein" -> "Klein"
            paneel.ids.positie_hoogte.text = str(item["positie_hoogte"] or "")
        paneel.open()

    def extra_opslaan(self, paneel):
        # Slaat de extra afbeelding op in de lijst van het objectformulier
        # (de database wordt pas bijgewerkt bij "Opslaan" in het objectformulier)
        titel = paneel.ids.titel.text.strip()
        if not paneel.afbeelding:
            paneel.ids.foutmelding.text = "Kies een afbeelding."
            return
        if not titel:
            paneel.ids.foutmelding.text = "Vul een titel in."
            return

        # Positie op de pagina. De hoogte vanaf boven bestaat alleen voor links en rechts.
        positie = paneel.ids.positie.text.lower()  # "Links" -> "links"
        positie_hoogte = None
        if positie != "midden" and paneel.ids.positie_hoogte.text:
            positie_hoogte = int(paneel.ids.positie_hoogte.text)  # leeg = automatisch onder elkaar

        item = {
            "positie": positie,
            "positie_hoogte": positie_hoogte,
            "formaat": paneel.ids.formaat.text.lower(),  # klein / normaal / groot / origineel
            "pad": paneel.afbeelding,
            "titel": titel,
            "breedte": int(paneel.ids.breedte.text or 0) or None,  # leeg of 0 = geen limiet
            "hoogte": int(paneel.ids.hoogte.text or 0) or None,
            "titel_zichtbaar": paneel.ids.titel_zichtbaar.active,  # vinkje: titel onder de foto tonen
        }

        formulier = paneel.formulier
        lijst = list(formulier.extra_afbeeldingen)
        if paneel.index >= 0:
            lijst[paneel.index] = item  # bestaande afbeelding bijwerken
        else:
            lijst.append(item)  # nieuwe afbeelding achteraan
        formulier.extra_afbeeldingen = lijst

        self.toon_extra_afbeeldingen(formulier)
        paneel.dismiss()

    def extra_verwijderen(self, paneel):
        # Haalt deze extra afbeelding uit de lijst (definitief na "Opslaan" in het objectformulier)
        formulier = paneel.formulier
        lijst = list(formulier.extra_afbeeldingen)
        del lijst[paneel.index]
        formulier.extra_afbeeldingen = lijst

        self.toon_extra_afbeeldingen(formulier)
        paneel.dismiss()
