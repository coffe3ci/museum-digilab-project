import os      # om te controleren of bestanden en mappen bestaan
import shutil  # om bestanden te kopiëren
import time    # voor een unieke bestandsnaam

from kivy.clock import mainthread  # Zorgt dat code op de hoofdthread van Kivy draait
from kivy.factory import Factory # Hiermee maken we ObjectItems aan (gedefinieerd in admin_panel.kv)
from kivy.uix.screenmanager import Screen # Basisklasse voor schermen
from kivy.utils import platform  # "win", "macosx", "linux", "android" of "ios"

from backend.object_manager import ObjectManager # Haalt de objecten uit de database
from frontend.tekst_opmaak import OpmaakVeld  # noqa: F401  (invoerveld met opmaak, gebruikt in admin_panel.kv)
from frontend.screens.object_detail_screen import PaginaVoorbeeld  # noqa: F401  (voorbeeld van de objectpagina)

AFBEELDING_MAP = "assets/objects_img"  # hier worden de afbeeldingen naartoe gekopieerd


def fotomap():
    # Geeft de map met foto's van deze computer (Windows: "Afbeeldingen", ook als die in OneDrive staat)
    if platform == "win":
        try:
            from win32com.shell import shell, shellcon
            return shell.SHGetFolderPath(0, shellcon.CSIDL_MYPICTURES, None, 0)
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Pictures")

class AdminPanelScreen(Screen):
    def on_enter(self):
        self.laad_objecten() # Laadt de objecten elke keer dat het adminpaneel geopend wordt

    def laad_objecten(self):
        lijst = self.ids.objecten_lijst
        lijst.clear_widgets() # Verwijdert de oude lijst

        objecten = ObjectManager().get_all_objects()
        for obj in objecten:
            item = Factory.ObjectItem()
            item.object_naam = obj[1]  # Alleen de titel, geen beschrijving
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
        formulier.ids.titel.zet_inhoud(obj[1], obj["titel_opmaak"])  # tekst + opmaak (vet, kleur, ...)
        formulier.ids.beschrijving.zet_inhoud(obj[2], obj["opmaak"])
        formulier.afbeelding = obj[3] or ""
        formulier.ids.hoofd_formaat.text = (obj["hoofd_formaat"] or "normaal").capitalize()  # "groot" -> "Groot"
        formulier.extra_afbeeldingen = ObjectManager().get_extra_afbeeldingen(obj_id)
        self.toon_extra_afbeeldingen(formulier)
        formulier.open()

    def formulier_opslaan(self, formulier):
        titel, titel_opmaak = formulier.ids.titel.inhoud()  # tekst en opmaak horen bij elkaar
        beschrijving, opmaak = formulier.ids.beschrijving.inhoud()

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
        hoofd_formaat = formulier.ids.hoofd_formaat.text.lower()  # grootte van de hoofdfoto op de objectpagina

        if formulier.obj_id == 0:
            obj_id = ObjectManager().add_object(  # Nieuw object (achteraan)
                titel, beschrijving, afbeelding, hoofd_formaat, opmaak, titel_opmaak)
        else:
            obj_id = formulier.obj_id
            ObjectManager().update_object(  # Bestaand object
                obj_id, titel, beschrijving, afbeelding, hoofd_formaat, opmaak, titel_opmaak)

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
        # Opent de fotokiezer van het apparaat zelf (via plyer):
        # - Android: de galerij / Foto's-kiezer (alleen afbeeldingen)
        # - iOS: de fotobibliotheek
        # - Windows / Mac: het eigen "Openen"-venster, meteen in de map Afbeeldingen
        # doel = "hoofd" (hoofdafbeelding van het object) of "extra" (afbeelding in het extra-paneel)
        def gekozen(selectie):
            # plyer roept dit aan met een lijst gekozen bestanden (leeg = geannuleerd)
            if selectie:
                self.verwerk_afbeelding(selectie[0], formulier, doel)

        try:
            from plyer import filechooser
            if platform in ("android", "ios"):
                # "image" = alleen foto's tonen (opent de galerij)
                filechooser.open_file(filters=["image"], on_selection=gekozen)
            else:
                filechooser.open_file(
                    title="Kies een foto",
                    path=fotomap(),
                    filters=[("Afbeeldingen", "*.png", "*.jpg", "*.jpeg")],
                    on_selection=gekozen,
                )
        except Exception as fout:
            # plyer niet beschikbaar of werkt niet op dit apparaat: gebruik de Kivy-bestandskiezer
            print("Fotokiezer van het apparaat werkt niet, Kivy-kiezer wordt gebruikt:", fout)
            self.open_kivy_kiezer(formulier, doel)

    def open_kivy_kiezer(self, formulier, doel):
        # Reserve: de ingebouwde Kivy-bestandskiezer (popup AfbeeldingKiezer in admin_panel.kv)
        kiezer = Factory.AfbeeldingKiezer()
        kiezer.formulier = formulier  # onthoud voor welk formulier/paneel het is
        kiezer.doel = doel
        start = fotomap()
        kiezer.ids.kiezer.path = start if os.path.isdir(start) else os.path.expanduser("~")
        kiezer.open()

    def tekst_opmaken(self, formulier, actie, kleur=None):
        # Knoppen boven de beschrijving: actie = "b" (vet), "i" (schuin), "u" (onderstreept),
        # "kleur" of "wis". Het stuk tekst hangt af van de keuze bij "Toepassen op".
        # Werkt op het veld (titel of beschrijving) waarin het laatst is geklikt.
        modus = formulier.ids.opmaak_modus.text
        veld = formulier.ids[formulier.opmaak_doel]  # "titel" of "beschrijving"
        gelukt = veld.pas_opmaak_toe(modus, actie, kleur)
        if gelukt:
            formulier.ids.foutmelding.text = ""
        elif modus == "Woorden (selectie)":
            formulier.ids.foutmelding.text = f"Selecteer eerst woorden in de {formulier.opmaak_doel} (of zet de cursor in een woord)."
        else:
            formulier.ids.foutmelding.text = f"Klik eerst in de {formulier.opmaak_doel} op de plek die je wilt opmaken."

    def kies_afbeelding(self, formulier):
        self.open_kiezer(formulier, "hoofd")

    def afbeelding_gekozen(self, kiezer):
        # Wordt aangeroepen door de Kivy-bestandskiezer (reserve)
        selectie = kiezer.ids.kiezer.selection
        if not selectie:  # niets geselecteerd
            return
        self.verwerk_afbeelding(selectie[0], kiezer.formulier, kiezer.doel)
        kiezer.dismiss()

    @mainthread  # Op Android komt de keuze uit een andere thread; de interface mag alleen hier veranderen
    def verwerk_afbeelding(self, bron, formulier, doel):
        # Kopieert de gekozen foto naar het project en toont hem in het formulier/paneel.
        # Tijdstempel voor de naam, zodat twee bestanden met de naam "foto.png" elkaar niet overschrijven
        naam = f"{int(time.time())}_{os.path.basename(bron)}"
        kopie = f"{AFBEELDING_MAP}/{naam}"
        shutil.copy(bron, kopie)  # kopieer naar het project

        formulier.afbeelding = kopie  # het voorbeeld in het formulier/paneel verandert vanzelf

        # Extra afbeelding zonder titel: vul de bestandsnaam (zonder extensie) alvast in
        if doel == "extra" and not formulier.ids.titel.text.strip():
            formulier.ids.titel.text = os.path.splitext(os.path.basename(bron))[0]

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
