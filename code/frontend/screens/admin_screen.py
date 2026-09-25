from kivy.uix.screenmanager import Screen
from backend.admin_manager import AdminManager


class AdminScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admin_manager = AdminManager()

    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text

        if self.admin_manager.login(username, password):
            self.ids.error_message.text = ""
            self.manager.current = "object_screen"
        else:
            self.ids.error_message.text = (
                "Verkeerde gebruikersnaam of wachtwoord"
            )

    def go_to_home(self):
        self.manager.current = "home"