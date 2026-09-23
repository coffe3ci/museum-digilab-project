
from kivy.uix.screenmanager import Screen


class AdminScreen(Screen):

    def go_to_home(self):
        self.manager.current = "home"