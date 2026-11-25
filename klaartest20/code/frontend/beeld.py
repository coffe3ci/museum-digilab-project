# Foto's in de juiste maat voor het scherm.
#
# De originele museumfoto's zijn soms enorm (tot bijna 6000 px breed). Die volledig laden is op een
# tablet heel traag en kost veel geheugen. Daarom heeft elke foto twee versies:
#   - weergaveversie: de foto zelf in assets/objects_img/ (langste zijde max. WEERGAVE_MAX px)
#   - tegelversie:    assets/objects_img/klein/<naam> (max. TEGEL_MAX px), voor de objectenwand
# De originelen staan buiten de app in de map fotos_origineel/ (zie tools/fotos_verkleinen.py).

import os

from kivy.utils import platform

WEERGAVE_MAX = 1600  # px, langste zijde van de foto op de objectpagina
TEGEL_MAX = 512  # px, langste zijde van de foto op een tegel van de objectenwand
TEGEL_MAP = "klein"  # submap naast de foto met de tegelversies
JPEG_KWALITEIT = 85


def foto_map():
    # Map waar nieuwe foto's uit het adminpaneel worden opgeslagen.
    # Op de tablet in de eigen opslag van de app, zodat ze een nieuwe versie van de app overleven.
    if platform == "android":
        from android.storage import app_storage_path  # noqa: PLC0415 (bestaat alleen op Android)
        map_ = os.path.join(app_storage_path(), "fotos")
    else:
        map_ = "assets/objects_img"
    os.makedirs(os.path.join(map_, TEGEL_MAP), exist_ok=True)
    return map_


def tegel_pad(pad):
    # Kleine versie van een foto voor de objectenwand (of het origineel als die er (nog) niet is)
    if not pad:
        return pad
    klein = os.path.join(os.path.dirname(pad), TEGEL_MAP, os.path.basename(pad))
    return klein if os.path.exists(klein) else pad


def verklein(bron, doel, max_zijde):
    # Slaat een verkleinde kopie op (langste zijde max_zijde px). Is de foto al klein genoeg, dan
    # wordt hij gewoon gekopieerd. Geeft True terug als het gelukt is.
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        return False
    with Image.open(bron) as img:
        img.load()
        if max(img.size) > max_zijde:
            img.thumbnail((max_zijde, max_zijde), Image.LANCZOS)
        if doel.lower().endswith((".jpg", ".jpeg")):
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(doel, quality=JPEG_KWALITEIT, optimize=True)
        else:
            img.save(doel)
    return True


def maak_versies(pad):
    # Na het toevoegen van een foto in het adminpaneel: de foto zelf verkleinen tot weergavemaat
    # en een tegelversie maken. Lukt dat niet (bv. geen PIL), dan blijft het origineel staan.
    try:
        tijdelijk = pad + ".tmp" + os.path.splitext(pad)[1]
        if verklein(pad, tijdelijk, WEERGAVE_MAX):
            os.replace(tijdelijk, pad)
        klein = os.path.join(os.path.dirname(pad), TEGEL_MAP, os.path.basename(pad))
        os.makedirs(os.path.dirname(klein), exist_ok=True)
        verklein(pad, klein, TEGEL_MAX)
    except Exception as fout:  # een kapotte foto mag de app niet laten vastlopen
        print("Kon foto niet verkleinen:", pad, fout)
