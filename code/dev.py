import os
import threading
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from frontend.screens.home_screen import HomeScreen
from frontend.screens.admin_screen import AdminScreen


class MuseumApp(App):

    kv_files = [
        "frontend/screens/home_screen.kv",
        "frontend/screens/admin_screen.kv",
    ]

    def build(self):
        self.load_kv_files()

        self.sm = ScreenManager()
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(AdminScreen(name="admin"))

        self.start_file_watcher()

        return self.sm
    
    def load_kv_files(self):
        Builder.load_file("frontend/screens/home_screen.kv")
        Builder.load_file("frontend/screens/admin_screen.kv")

    def start_file_watcher(self):
        thread = threading.Thread(
            target=self.watch_files,
            daemon=True
        )
        thread.start()

    def watch_files(self):
        last_modified = {}

        for file in self.kv_files:
            last_modified[file] = os.path.getmtime(file)

        while True:
            time.sleep(0.5)

            for file in self.kv_files:
                current_modified = os.path.getmtime(file)

                if current_modified != last_modified[file]:
                    last_modified[file] = current_modified

                    Clock.schedule_once(
                        lambda dt: self.reload_kv()
                    )

    def reload_kv(self):
        try:
            current_screen = self.sm.current

            self.sm.clear_widgets()

            self.load_kv_files()

            self.sm.add_widget(HomeScreen(name="home"))
            self.sm.add_widget(AdminScreen(name="admin"))

            self.sm.current = current_screen

            print("KV besattand herladen")

        except Exception as e:
            print("KV fout", e)


if __name__ == "__main__":
    MuseumApp().run()