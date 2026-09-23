
from kivy.uix.screenmanager import Screen


class HomeScreen(Screen):

    def go_to_admin(self):
        self.manager.current = "admin"