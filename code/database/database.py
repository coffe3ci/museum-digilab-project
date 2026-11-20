import os
import shutil
import sqlite3

from kivy.utils import platform

# De database die met de app wordt meegeleverd (in de map code/database).
MEEGELEVERD = "database/museum.db"

# Op de tablet wordt de database gekopieerd naar de eigen opslag van de app. Daar blijft hij bewaard
# als er een nieuwe versie van de APK wordt geïnstalleerd (anders zouden alle wijzigingen uit het
# adminpaneel op de tablet verloren gaan).
# Wil je dat de tablet tóch de meegeleverde database overneemt (bv. na veel werk op de pc)?
# Verhoog dan DATABASE_VERSIE met 1 en bouw een nieuwe APK. Let op: wijzigingen die op de tablet
# zelf zijn gedaan, worden dan overschreven.
DATABASE_VERSIE = 1

# Pad naar de database die gebruikt wordt. None = automatisch bepalen (zie database_pad).
# Tests mogen dit zelf op een kopie zetten.
DB_PATH = None


def database_pad():
    global DB_PATH
    if DB_PATH:
        return DB_PATH
    if platform != "android":
        DB_PATH = MEEGELEVERD  # op de pc gewoon de database in het project
        return DB_PATH

    from android.storage import app_storage_path  # noqa: PLC0415 (bestaat alleen op Android)
    map_ = os.path.join(app_storage_path(), "database")
    os.makedirs(map_, exist_ok=True)
    pad = os.path.join(map_, "museum.db")
    versie_bestand = os.path.join(map_, "versie.txt")
    try:
        with open(versie_bestand) as f:
            huidige_versie = int(f.read().strip())
    except (OSError, ValueError):
        huidige_versie = 0
    if not os.path.exists(pad) or huidige_versie < DATABASE_VERSIE:
        shutil.copy(MEEGELEVERD, pad)  # eerste start (of nieuwere database meegeleverd)
        with open(versie_bestand, "w") as f:
            f.write(str(DATABASE_VERSIE))
    DB_PATH = pad
    return DB_PATH


def get_connection():
    conn = sqlite3.connect(database_pad())
    conn.row_factory = sqlite3.Row   # lets you write obj["title"] instead of obj[1]
    return conn
