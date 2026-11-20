# Verkleint alle museumfoto's voor de app (eenmalig, of opnieuw na het toevoegen van foto's op de pc).
#
#   - Het origineel gaat naar <project>/fotos_origineel/ (buiten de map code, dus niet in de APK)
#   - De foto in assets/objects_img/ wordt een weergaveversie (langste zijde max. 1600 px)
#   - In assets/objects_img/klein/ komt een tegelversie (max. 512 px) voor de objectenwand
#
# Gebruik (vanuit de map code):   python tools/fotos_verkleinen.py
# Het script kan veilig vaker gedraaid worden: wat al klaar is, wordt overgeslagen.

import os
import shutil
import sys

sys.path.insert(0, os.getcwd())
from frontend.beeld import TEGEL_MAP, TEGEL_MAX, WEERGAVE_MAX, verklein  # noqa: E402

FOTO_MAP = "assets/objects_img"
ORIGINEEL_MAP = os.path.join("..", "fotos_origineel")
FOTO_SOORTEN = (".jpg", ".jpeg", ".png")


def main():
    from PIL import Image

    os.makedirs(ORIGINEEL_MAP, exist_ok=True)
    os.makedirs(os.path.join(FOTO_MAP, TEGEL_MAP), exist_ok=True)
    voor = na = 0
    for naam in sorted(os.listdir(FOTO_MAP)):
        pad = os.path.join(FOTO_MAP, naam)
        if not os.path.isfile(pad) or not naam.lower().endswith(FOTO_SOORTEN):
            continue  # mappen (logo, klein) en andere bestanden overslaan
        voor += os.path.getsize(pad)

        with Image.open(pad) as img:
            groot = max(img.size) > WEERGAVE_MAX
        origineel = os.path.join(ORIGINEEL_MAP, naam)
        if groot:
            if not os.path.exists(origineel):
                shutil.copy2(pad, origineel)  # origineel eerst veiligstellen
            tijdelijk = pad + ".tmp" + os.path.splitext(naam)[1]
            verklein(pad, tijdelijk, WEERGAVE_MAX)
            os.replace(tijdelijk, pad)

        klein = os.path.join(FOTO_MAP, TEGEL_MAP, naam)
        if not os.path.exists(klein):
            verklein(pad, klein, TEGEL_MAX)
        na += os.path.getsize(pad)
        print(f"{'verkleind' if groot else 'al klein  '}  {naam}")

    print(f"\nFoto's: {voor / 1e6:.1f} MB -> {na / 1e6:.1f} MB (plus tegels in {TEGEL_MAP}/)")


if __name__ == "__main__":
    main()
