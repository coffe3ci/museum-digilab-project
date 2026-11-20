import hashlib  # Om het wachtwoord te "hashen" (onleesbaar maken)
import hmac  # Om twee hashes veilig te vergelijken
import os  # Voor een willekeurige "salt"

from database.database import get_connection

# Het wachtwoord staat NIET leesbaar in de database, maar als hash:
#   pbkdf2_sha256$<aantal rondes>$<salt>$<hash>
# Uit een hash kun je het wachtwoord niet terugrekenen. Bij inloggen wordt het ingevoerde
# wachtwoord op dezelfde manier gehasht en vergeleken.
VOORVOEGSEL = "pbkdf2_sha256"
# Hoe vaker, hoe trager raden gaat. 200.000 rondes: veilig voor deze app en op de tablet nog
# acceptabel snel (600.000 duurde daar enkele seconden). Oude hashes met een ander aantal rondes
# blijven werken en worden bij de eerstvolgende geslaagde login automatisch omgezet.
RONDES = 200_000


def maak_hash(wachtwoord, salt=None, rondes=RONDES):
    # Maakt de hash die in de database komt. De salt is voor elk wachtwoord anders,
    # zodat twee gelijke wachtwoorden toch een andere hash hebben.
    salt = salt or os.urandom(16).hex()
    hash_ = hashlib.pbkdf2_hmac("sha256", wachtwoord.encode("utf-8"), salt.encode("utf-8"), rondes).hex()
    return f"{VOORVOEGSEL}${rondes}${salt}${hash_}"


def rondes_van(opgeslagen):
    # Hoeveel rondes zijn gebruikt voor deze hash? (0 als het geen geldige hash is)
    try:
        return int(opgeslagen.split("$")[1])
    except (IndexError, ValueError, AttributeError):
        return 0


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
    # Hulpmethode om verbinding te maken met de database (dezelfde als de rest van de app,
    # ook op de tablet waar de database in de eigen opslag van de app staat)
    def get_connection(self):
        return get_connection()

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

        # Eerst precies zoals getypt; lukt dat niet, dan zonder spaties aan begin/eind
        # (een tablettoetsenbord zet soms vanzelf een spatie achter een woord).
        pogingen = [password] + ([password.strip()] if password.strip() != password else [])

        if opgeslagen.startswith(VOORVOEGSEL + "$"):
            juist = next((p for p in pogingen if klopt_wachtwoord(p, opgeslagen)), None)
            # Hash met een ander aantal rondes (oude versie)? Meteen omzetten naar de huidige.
            if juist is not None and rondes_van(opgeslagen) != RONDES:
                self._sla_op(conn, username, juist)
        else:
            # Oud, nog leesbaar opgeslagen wachtwoord: vergelijk één keer gewoon
            # en sla het meteen gehasht op, zodat het daarna niet meer leesbaar is.
            juist = next((p for p in pogingen
                          if hmac.compare_digest(p.encode("utf-8"), opgeslagen.encode("utf-8"))), None)
            if juist is not None:
                self._sla_op(conn, username, juist)

        conn.close()
        return juist is not None

    def _sla_op(self, conn, username, wachtwoord):
        conn.execute("UPDATE admin SET wachtwoord = ? WHERE gebruikersnaam = ?",
                     (maak_hash(wachtwoord), username))
        conn.commit()

    def verander_wachtwoord(self, username, nieuw_wachtwoord):
        # Zet een nieuw wachtwoord (gehasht) voor deze gebruiker.
        # Gebruik bv.:  python -c "from backend.admin_manager import AdminManager; AdminManager().verander_wachtwoord('admin', 'NieuwWachtwoord')"
        conn = self.get_connection()
        aangepast = conn.execute(
            "UPDATE admin SET wachtwoord = ? WHERE gebruikersnaam = ?",
            (maak_hash(nieuw_wachtwoord.strip()), username),
        ).rowcount
        conn.commit()
        conn.close()
        return aangepast > 0
