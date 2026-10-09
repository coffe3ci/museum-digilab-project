import sqlite3


class AdminManager:
    # Hulpmethode om verbinding te maken met de database
    def get_connection(self):
        return sqlite3.connect("database/museum.db")

    def login(self, username, password):
        # Maak verbinding met de database
        conn = self.get_connection()
        cursor = conn.cursor()

        # Controleer of de ingevoerde gebruikersnaam en het wachtwoord overeenkomen
        cursor.execute(
            "SELECT * FROM admin WHERE gebruikersnaam=? AND wachtwoord=?",
            (username, password),
        )

        # Haal de gevonden gebruiker op uit het resultaat
        gebruiker = cursor.fetchone()

        # Sluit de databaseverbinding
        conn.close()

        # Geeft True terug als de gebruiker bestaat, anders False
        return gebruiker is not None