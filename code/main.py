from kivy.app import App
from kivy.uix.label import Label


class MuseumApp(App):
    def build(self):
        return Label(
            text="Museum DigiLab",
            font_size="40sp"
        )


if __name__ == "__main__":
    MuseumApp().run()