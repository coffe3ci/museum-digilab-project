
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from frontend.screens.home_screen import HomeScreen
from frontend.screens.admin_screen import AdminScreen


class MuseumApp(App):

    def build(self):
        Builder.load_file(
            "frontend/screens/home_screen.kv"
        )

        Builder.load_file(
            "frontend/screens/admin_screen.kv"
        )

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(AdminScreen(name="admin"))

        return sm


if __name__ == "__main__":
    MuseumApp().run()