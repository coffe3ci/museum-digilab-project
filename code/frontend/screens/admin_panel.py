import os      # om te controleren of bestanden en mappen bestaan
import shutil  # om bestanden te kopiëren
import time    # voor een unieke bestandsnaam

from kivy.clock import Clock, mainthread  # mainthread: code op de hoofdthread van Kivy laten draaien
from kivy.factory import Factory # Hiermee maken we ObjectItems aan (gedefinieerd in admin_panel.kv)
from kivy.uix.screenmanager import Screen # Basisklasse voor schermen
from kivy.utils import platform  # "win", "macosx", "linux", "android" of "ios"

from backend.admin_manager import AdminManager  # Wachtwoord controleren en veranderen
from backend.object_manager import ObjectManager # Haalt de objecten uit de database
from frontend.tekst_opmaak import OpmaakVeld  # noqa: F401  (invoerveld met opmaak, gebruikt in admin_panel.kv)
from frontend.screens.object_detail_screen import PaginaVoorbeeld  # noqa: F401  (voorbeeld van de objectpagina)

AFBEELDING_MAP = "assets/objects_img"  # hier worden de afbeeldingen naartoe gekopieerd
ADMIN_GEBRUIKER = "admin"  # De beheerder (zelfde gebruikersnaam als in admin_screen.py)
MIN_WACHTWOORD_LENGTE = 8  # Een nieuw wachtwoord moet minstens zo lang zijn
GEEN_CATEGORIE = "Geen categorie"  # Keuze in het objectformulier als een object (nog) geen categorie heeft


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
        namen = {cat["id"]: cat["naam"] for cat in ObjectManager().get_categorieen()}
        for obj in objecten:
            item = Factory.ObjectItem()
            item.object_naam = obj[1]  # Alleen de titel, geen beschrijving
            item.categorie = namen.get(obj["categorie_id"], "")  # "" = nog geen categorie (rood)
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
        self.vul_categorie_keuze(formulier, None)
        self.toon_extra_afbeeldingen(formulier)
        formulier.open()

    def vul_categorie_keuze(self, formulier, categorie_id):
        # Vult de keuzelijst "Categorie" in het objectformulier met alle categorieën (tijdlijn-volgorde)
        categorieen = ObjectManager().get_categorieen()
        formulier.categorie_per_naam = {cat["naam"]: cat["id"] for cat in categorieen}
        keuze = formulier.ids.categorie
        keuze.values = [cat["naam"] for cat in categorieen] + [GEEN_CATEGORIE]
        keuze.text = next((cat["naam"] for cat in categorieen if cat["id"] == categorie_id), GEEN_CATEGORIE)

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
        self.vul_categorie_keuze(formulier, obj["categorie_id"])
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

        # Elk object hoort in een categorie (als er categorieën zijn)
        categorie_id = formulier.categorie_per_naam.get(formulier.ids.categorie.text)
        if categorie_id is None and formulier.categorie_per_naam:
            formulier.ids.foutmelding.text = "Kies een categorie voor dit object."
            return

        afbeelding = formulier.afbeelding or None  # "" wordt None (leeg) in de database
        hoofd_formaat = formulier.ids.hoofd_formaat.text.lower()  # grootte van de hoofdfoto op de objectpagina

        if formulier.obj_id == 0:
            obj_id = ObjectManager().add_object(  # Nieuw object (achteraan)
                titel, beschrijving, afbeelding, hoofd_formaat, opmaak, titel_opmaak, categorie_id)
        else:
            obj_id = formulier.obj_id
            ObjectManager().update_object(  # Bestaand object
                obj_id, titel, beschrijving, afbeelding, hoofd_formaat, opmaak, titel_opmaak, categorie_id)

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

    # ---------- Categorieën (periodes op de tijdlijn) ----------

    def open_categorie_beheer(self):
        # Opent het overzicht van alle categorieën (CategorieBeheer in admin_panel.kv)
        self.categorie_beheer = Factory.CategorieBeheer()
        self.categorie_beheer.bind(on_dismiss=lambda *a: self.laad_objecten())  # Lijst bijwerken na sluiten
        # Aan/uit-knoppen "Weergave voor bezoekers" op de opgeslagen stand zetten
        for sleutel in ("filter_tonen", "groeperen"):
            self.categorie_beheer.ids[sleutel].aan = ObjectManager().get_instelling(sleutel)
        self.vul_categorie_lijst()
        self.categorie_beheer.open()

    def instelling_gewijzigd(self, sleutel, aan):
        # Een aan/uit-knop bij "Weergave voor bezoekers" is omgezet: meteen opslaan.
        # De objectenwand leest dit elke keer dat hij geopend wordt.
        ObjectManager().zet_instelling(sleutel, aan)

    def vul_categorie_lijst(self):
        # (Opnieuw) de rijen in het categoriebeheer maken, in tijdlijn-volgorde
        beheer = getattr(self, "categorie_beheer", None)
        if beheer is None:
            return
        lijst = beheer.ids.lijst
        lijst.clear_widgets()
        categorieen = ObjectManager().get_categorieen()
        for i, cat in enumerate(categorieen):
            rij = Factory.CategorieRij()
            rij.cat_id = cat["id"]
            rij.naam = cat["naam"]
            rij.periode = cat["periode"]
            rij.aantal = cat["aantal"]
            rij.eerste = i == 0
            rij.laatste = i == len(categorieen) - 1
            lijst.add_widget(rij)
        if not categorieen:
            lijst.add_widget(Factory.ExtraLeegLabel(text="Nog geen categorieën. Voeg er hieronder een toe."))

        # Waarschuwing: objecten zonder categorie
        zonder = [obj["id"] for obj in ObjectManager().get_all_objects() if obj["categorie_id"] is None]
        beheer.ids.zonder_melding.text = (
            f"Nog zonder categorie: object {', '.join(map(str, zonder))}" if zonder else "")

    def categorie_verplaatsen(self, cat_id, richting):
        # Pijltje omhoog (-1) of omlaag (+1): eerder of later op de tijdlijn
        ObjectManager().verplaats_categorie(cat_id, richting)
        self.vul_categorie_lijst()

    def categorie_toevoegen(self):
        Factory.CategorieFormulier().open()

    def categorie_bewerken(self, cat_id):
        cat = next((c for c in ObjectManager().get_categorieen() if c["id"] == cat_id), None)
        if cat is None:
            return
        formulier = Factory.CategorieFormulier()
        formulier.cat_id = cat_id
        formulier.ids.naam.text = cat["naam"]
        formulier.ids.periode.text = cat["periode"]
        formulier.open()

    def categorie_formulier_opslaan(self, formulier):
        naam = formulier.ids.naam.text.strip()
        periode = formulier.ids.periode.text.strip()
        if not naam:
            formulier.ids.foutmelding.text = "Vul een naam in."
            return
        if naam == GEEN_CATEGORIE:
            formulier.ids.foutmelding.text = f'"{GEEN_CATEGORIE}" kan geen naam zijn.'
            return
        if ObjectManager().naam_bestaat(naam, formulier.cat_id or None):
            formulier.ids.foutmelding.text = "Er is al een categorie met deze naam."
            return

        if formulier.cat_id == 0:
            ObjectManager().voeg_categorie_toe(naam, periode)
        else:
            ObjectManager().update_categorie(formulier.cat_id, naam, periode)
        formulier.dismiss()
        self.vul_categorie_lijst()

    def categorie_verwijderen(self, cat_id):
        cat = next((c for c in ObjectManager().get_categorieen() if c["id"] == cat_id), None)
        if cat is None:
            return
        bevestiging = Factory.BevestigCategorieVerwijderen()
        bevestiging.cat_id = cat_id
        bevestiging.naam = cat["naam"]
        bevestiging.aantal = cat["aantal"]
        bevestiging.open()

    def categorie_verwijderen_bevestigd(self, bevestiging):
        ObjectManager().verwijder_categorie(bevestiging.cat_id)
        bevestiging.dismiss()
        self.vul_categorie_lijst()

    def categorie_objecten(self, cat_id):
        # Lijst met alle objecten en een vinkje: aangevinkt = zit in deze categorie
        categorieen = ObjectManager().get_categorieen()
        cat = next((c for c in categorieen if c["id"] == cat_id), None)
        if cat is None:
            return
        namen = {c["id"]: c["naam"] for c in categorieen}

        venster = Factory.CategorieObjecten()
        venster.cat_id = cat_id
        venster.cat_naam = cat["naam"]
        for obj in ObjectManager().get_all_objects():
            rij = Factory.CategorieObjectRij()
            rij.obj_id = obj["id"]
            rij.titel = obj[1]
            rij.ids.vink.active = obj["categorie_id"] == cat_id
            # Zit het nu in een andere categorie? Dan tonen we die (het verhuist als je het aanvinkt)
            if obj["categorie_id"] not in (None, cat_id):
                rij.andere = namen.get(obj["categorie_id"], "")
            venster.ids.lijst.add_widget(rij)
        venster.open()

    def categorie_objecten_opslaan(self, venster):
        aangevinkt = [rij.obj_id for rij in venster.ids.lijst.children if rij.ids.vink.active]
        ObjectManager().zet_objecten_in_categorie(venster.cat_id, aangevinkt)
        venster.dismiss()
        self.vul_categorie_lijst()

    # ---------- Wachtwoord wijzigen ----------

    def open_wachtwoord_formulier(self):
        # Opent de pop-up om het wachtwoord van de adminpagina te veranderen (WachtwoordFormulier in admin_panel.kv)
        Factory.WachtwoordFormulier().open()

    def wachtwoord_opslaan(self, formulier):
        # Controleert de drie velden en slaat het nieuwe wachtwoord (gehasht) op
        huidig = formulier.ids.huidig.text
        nieuw = formulier.ids.nieuw.text
        herhaal = formulier.ids.herhaal.text
        formulier.ids.gelukt.text = ""

        fout = None
        if not AdminManager().login(ADMIN_GEBRUIKER, huidig):
            fout = "Het huidige wachtwoord klopt niet."
        elif len(nieuw) < MIN_WACHTWOORD_LENGTE:
            fout = f"Het nieuwe wachtwoord moet minstens {MIN_WACHTWOORD_LENGTE} tekens hebben."
        elif nieuw != herhaal:
            fout = "De twee nieuwe wachtwoorden zijn niet hetzelfde."
        elif nieuw == huidig:
            fout = "Het nieuwe wachtwoord is hetzelfde als het huidige."

        if fout:
            formulier.ids.foutmelding.text = fout
            return

        AdminManager().verander_wachtwoord(ADMIN_GEBRUIKER, nieuw)
        formulier.ids.foutmelding.text = ""
        formulier.ids.gelukt.text = "Wachtwoord gewijzigd!"
        for veld in ("huidig", "nieuw", "herhaal"):
            formulier.ids[veld].text = ""  # Wachtwoorden niet in de velden laten staan
        Clock.schedule_once(lambda dt: formulier.dismiss(), 1.2)  # Melding even laten zien, dan sluiten

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
