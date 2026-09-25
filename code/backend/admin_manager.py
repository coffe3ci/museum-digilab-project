class AdminManager:

    USERNAME = "admin"
    PASSWORD = "admin123"

    def login(self, username, password):
        return (
            username == self.USERNAME
            and password == self.PASSWORD
        )