# Kioskmodus voor de museumtablet (Android "scherm vastzetten" / lock task).
#
# Aan:  de app wordt vastgezet in beeld. Home-, terug- en recente-apps-knop werken niet meer en de
#       systeembalken worden verborgen. Bezoekers kunnen de app dus niet verlaten.
#       Android vraagt de eerste keer om bevestiging ("Scherm vastzetten?").
# Uit:  via de knop in het adminpaneel (geheime knop rechtsboven 4x tikken -> inloggen), of met
#       de pincode van de tablet als "Pincode vragen bij losmaken" aan staat.
#
# Op de pc (Windows/Mac) doet dit niets: OP_TABLET is dan False.

from kivy.logger import Logger
from kivy.utils import platform

OP_TABLET = platform == "android"


def _activity():
    from jnius import autoclass  # noqa: PLC0415 (pyjnius bestaat alleen op Android)
    return autoclass("org.kivy.android.PythonActivity").mActivity


def _op_ui_thread(functie):
    # Android-schermzaken moeten op de "UI-thread" van Android gebeuren
    from android.runnable import run_on_ui_thread  # noqa: PLC0415
    run_on_ui_thread(functie)()


def kiosk_actief():
    # Staat de app nu vastgezet?
    if not OP_TABLET:
        return False
    try:
        from jnius import autoclass, cast  # noqa: PLC0415
        context = autoclass("android.content.Context")
        manager = cast("android.app.ActivityManager", _activity().getSystemService(context.ACTIVITY_SERVICE))
        return manager.getLockTaskModeState() != 0  # 0 = LOCK_TASK_MODE_NONE
    except Exception as fout:
        Logger.warning(f"Kiosk: stand opvragen lukte niet: {fout}")
        return False


def verberg_balken():
    # Statusbalk en navigatiebalk verbergen ("immersive sticky"): de app vult het hele scherm.
    # Vegen vanaf de rand laat ze even zien; daarna verdwijnen ze vanzelf weer.
    if not OP_TABLET:
        return

    def doe():
        from jnius import autoclass  # noqa: PLC0415
        view = autoclass("android.view.View")
        vlaggen = (view.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | view.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                   | view.SYSTEM_UI_FLAG_FULLSCREEN | view.SYSTEM_UI_FLAG_LAYOUT_STABLE
                   | view.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | view.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)
        _activity().getWindow().getDecorView().setSystemUiVisibility(vlaggen)

    try:
        _op_ui_thread(doe)
    except Exception as fout:
        Logger.warning(f"Kiosk: balken verbergen lukte niet: {fout}")


def scherm_aan_houden():
    # Het scherm gaat niet vanzelf uit zolang de app open is (handig voor een museumtablet)
    if not OP_TABLET:
        return

    def doe():
        from jnius import autoclass  # noqa: PLC0415
        params = autoclass("android.view.WindowManager$LayoutParams")
        _activity().getWindow().addFlags(params.FLAG_KEEP_SCREEN_ON)

    try:
        _op_ui_thread(doe)
    except Exception as fout:
        Logger.warning(f"Kiosk: scherm aan houden lukte niet: {fout}")


def start_kiosk():
    # App vastzetten. Geeft False terug als het niet kan (bv. op de pc).
    if not OP_TABLET:
        return False

    def doe():
        _activity().startLockTask()

    try:
        _op_ui_thread(doe)
        verberg_balken()
        Logger.info("Kiosk: aangezet")
        return True
    except Exception as fout:
        Logger.warning(f"Kiosk: aanzetten lukte niet: {fout}")
        return False


def stop_kiosk():
    # App weer losmaken. Geeft False terug als het niet kan.
    if not OP_TABLET:
        return False

    def doe():
        _activity().stopLockTask()

    try:
        _op_ui_thread(doe)
        Logger.info("Kiosk: uitgezet")
        return True
    except Exception as fout:
        Logger.warning(f"Kiosk: uitzetten lukte niet: {fout}")
        return False
