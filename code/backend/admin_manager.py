import hashlib  # Om het wachtwoord te "hashen" (onleesbaar maken)
import hmac  # Om twee hashes veilig te vergelijken
import os  # Voor een willekeurige "salt"
import sqlite3

# Het wachtwoord staat NIET leesbaar in de database, maar als hash:
#   pbkdf2_sha256$<aantal rondes>$<salt>$<hash>
# Uit een hash kun je het wachtwoord niet terugrekenen. Bij inloggen wordt het ingevoerde
# wachtwoord op dezelfde manier gehasht en vergeleken.
VOORVOEGSEL = "pbkdf2_sha256"
RONDES = 600_000  # Hoe vaker, hoe trager raden gaat (aanbevolen waarde voor PBKDF2-SHA256)


def maak_hash(wachtwoord, salt=None, rondes=RONDES):
    # Maakt de hash die in de database komt. De salt is voor elk wachtwoord anders,
    # zodat twee gelijke wachtwoorden toch een andere hash hebben.
    salt = salt or os.urandom(16).hex()
    hash_ = hashlib.pbkdf2_hmac("sha256", wachtwoord.encode("utf-8"), salt.encode("utf-8"), rondes).hex()
    return f"{VOORVOEGSEL}${rondes}${salt}${hash_}"


def klopt_wachtwoord(wachtwoord, opgeslagen):
    # Controleert of het ingevoerde wachtwoord bij de opgeslagen hash hoort
    try:
        voorvoegsel, rondes, salt, _ = opgeslagen.split("$")
    except (ValueError, AttributeError):
        return False
    if voorvoegsel != VOORVOEGSEL:
        return False
    nieuw = maak_hash(wachtwoord, salt, int(rondes))
    return hmac.compare_digest(nieuw, opgeslagen)  # Vergelijkt veilig (even snel bij goed of fout)


class AdminManager:
    # Hulpmethode om verbinding te maken met de database
    def get_connection(self):
        return sqlite3.connect("database/museum.db")

    def login(self, username, password):
        # Haal de opgeslagen (gehashte) wachtwoord van deze gebruiker op
        conn = self.get_connection()
        rij = conn.execute(
            "SELECT wachtwoord FROM admin WHERE gebruikersnaam = ?", (username,)
        ).fetchone()

        if rij is None:
            conn.close()
            return False
        opgeslagen = rij[0] or ""

        if opgeslagen.startswith(VOORVOEGSEL + "$"):
            gelukt = klopt_wachtwoord(password, opgeslagen)
        else:
            # Oud, nog leesbaar opgeslagen wachtwoord: vergelijk één keer gewoon
            # en sla het meteen gehasht op, zodat het daarna niet meer leesbaar is.
            gelukt = hmac.compare_digest(password.encode("utf-8"), opgeslagen.encode("utf-8"))
            if gelukt:
                conn.execute(
                    "UPDATE admin SET wachtwoord = ? WHERE gebruikersnaam = ?",
                    (maak_hash(password), username),
                )
                conn.commit()

        conn.close()
        return gelukt

    def verander_wachtwoord(self, username, nieuw_wachtwoord):
        # Zet een nieuw wachtwoord (gehasht) voor deze gebruiker.
        # Gebruik bv.:  python -c "from backend.admin_manager import AdminManager; AdminManager().verander_wachtwoord('admin', 'NieuwWachtwoord')"
        conn = self.get_connection()
        aangepast = conn.execute(
            "UPDATE admin SET wachtwoord = ? WHERE gebruikersnaam = ?",
            (maak_hash(nieuw_wachtwoord), username),
        ).rowcount
        conn.commit()
        conn.close()
        return aangepast > 0
