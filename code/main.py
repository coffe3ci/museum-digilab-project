from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from frontend.home_screen import HomeScreen
from frontend.admin_screen import AdminScreen
from frontend.object_screen import ObjectScreen


class MuseumApp(App):

    def build(self):

        Builder.load_file(
            "frontend/home_screen.kv"
        )

        Builder.load_file(
            "frontend/admin_screen.kv"
        )

        Builder.load_file(
            "frontend/object_screen.kv"
        )

        sm = ScreenManager()

        sm.add_widget(
            HomeScreen(name="home")
        )

        sm.add_widget(
            AdminScreen(name="admin")
        )

        sm.add_widget(
            ObjectScreen(name="object_screen")
        )

        return sm


if __name__ == "__main__":
    MuseumApp().run()