# Bouwinstellingen voor de Android-app (APK) van Stadsmuseum Veenendaal.
# Bouwen (Linux/WSL, vanuit de map code):   buildozer android debug
# De APK staat daarna in code/bin/.
#
# Gericht op brede Android-tabletcompatibiliteit: Android 7.0+ (API 24+), 32- en 64-bits ARM.

[app]

title = Stadsmuseum Veenendaal
package.name = museumveenendaal
package.domain = nl.stadsmuseumveenendaal
version = 1.2

source.dir = .
# Alle bestanden die de app nodig heeft (foto's in kleine én hoofdletters, lettertypes, database)
source.include_exts = py,png,jpg,jpeg,JPG,JPEG,PNG,kv,otf,ttf,db,ico
# Niet meenemen in de APK: ontwikkelhulpmiddelen en de virtuele omgeving van de pc
source.exclude_dirs = .venv, venv, tools, __pycache__, .buildozer, bin, tests
source.exclude_patterns = dev.py, requirements.txt

# python3 en kivy: de app zelf
# pillow: foto's verkleinen als er in het adminpaneel een foto wordt toegevoegd
# plyer: de fotokiezer (galerij) in het adminpaneel
# pyjnius + android: kioskmodus, scherm aan houden en opslaglocatie op de tablet
requirements = python3,kivy==2.3.1,pillow,plyer,pyjnius,android,filetype

orientation = landscape
# Volledig scherm (geen statusbalk bovenin)
fullscreen = 1

icon.filename = %(source.dir)s/assets/images/icoon.png
presplash.filename = %(source.dir)s/assets/images/presplash.png
android.presplash_color = #F4EFE6

# Foto's kiezen uit de galerij (oude en nieuwe Android-versies) en het scherm aan houden
android.permissions = READ_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, WAKE_LOCK

android.api = 35
android.minapi = 24
# 32-bits ARM voor oudere tablets en 64-bits ARM voor moderne tablets (o.a. Galaxy Tab A9+).
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
# Scherm gaat niet uit zolang de app open is
android.wakelock = True
android.allow_backup = True

p4a.bootstrap = sdl2
# Gebruik dezelfde geteste python-for-android release als de eerdere build.
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
