class AdminManager:  # Definieer de AdminManager-klasse die de authenticatielogica afhandelt
    USERNAME = "admin"  # Ingesteld als de standaard en toegestane gebruikersnaam voor de beheerder
    PASSWORD = "admin123"  # Ingesteld als het standaard en vereiste wachtwoord voor de beheerder

    def login(self, username, password):  # Functie/methode om de ingevoerde inloggegevens te controleren
        return (  # Geef de vergelijkingsuitslag direct terug als een boolean (True of False)
            username == self.USERNAME  # Controleer of de ingevoerde gebruikersnaam overeenkomt met de ingestelde gebruikersnaam
            and password == self.PASSWORD  # Controleer of het ingevoerde wachtwoord overeenkomt met het ingestelde wachtwoord
        )