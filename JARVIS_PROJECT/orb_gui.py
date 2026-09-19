import os
import sys
import threading

import webview

from jarvis import JarvisCore
from tray import ARGUMENTO_MINIMIZADO, BandejaSistema
from voice import VoiceInterface


def _ruta_recursos(*partes):
    """Resuelve una ruta tanto en modo script como empaquetada (PyInstaller).

    PyInstaller extrae los datos incluidos (--add-data) a una carpeta temporal
    expuesta en sys._MEIPASS; en modo script normal, __file__ apunta aquí.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *partes)


class OrbAPI:
    """Puente entre la interfaz web (esfera animada) y el núcleo de JARVIS."""

    def __init__(self):
        self.jarvis = None
        self.voice = VoiceInterface()

    # Cada método aquí es invocado por pywebview en su propio hilo cuando lo
    # llama el JavaScript (window.pywebview.api.*), así que las llamadas
    # bloqueantes (red, micrófono, TTS) no congelan la ventana.

    def iniciar_nucleo(self):
        try:
            self.jarvis = JarvisCore()
        except Exception as e:
            return {"ok": False, "mensaje": str(e)}
        return {"ok": True, "mensaje": "Todos los sistemas se encuentran operativos, Señor."}

    def enviar_texto(self, texto, leer_en_voz_alta=True):
        if self.jarvis is None:
            return {"ok": False, "mensaje": "JARVIS no está inicializado."}
        try:
            respuesta = self.jarvis.procesar_orden(texto)
        except Exception as e:
            return {"ok": False, "mensaje": f"Fallo de núcleo: {e}"}

        if leer_en_voz_alta and respuesta:
            threading.Thread(target=self.voice.hablar, args=(respuesta,), daemon=True).start()
        return {"ok": True, "respuesta": respuesta}

    def escuchar(self):
        texto, error = self.voice.escuchar()
        return {"texto": texto, "error": error}


def _fijar_identidad_windows():
    # AppUserModelID propio: la barra de tareas agrupa la ventana como "JARVIS"
    # con su propio ícono, en vez de agruparla bajo python.exe.
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("JARVIS.Asistente")
    except Exception:
        pass


def main():
    _fijar_identidad_windows()
    api = OrbAPI()
    directorio_ui = _ruta_recursos("orb_ui", "index.html")
    iniciar_oculto = ARGUMENTO_MINIMIZADO in sys.argv
    saliendo = threading.Event()

    ventana = webview.create_window(
        "JARVIS",
        directorio_ui,
        js_api=api,
        width=1000,
        height=720,
        min_size=(640, 480),
        background_color="#030814",
        hidden=iniciar_oculto,
    )

    def al_cerrando():
        # Cerrar la ventana la oculta a la bandeja; solo "Salir" termina la app.
        if saliendo.is_set():
            return True
        ventana.hide()
        return False

    def al_cerrar():
        if api.jarvis is not None:
            try:
                api.jarvis.scheduler.shutdown(wait=False)
            except Exception:
                pass

    def salir():
        saliendo.set()
        ventana.destroy()

    bandeja = BandejaSistema(_ruta_recursos("orb_ui", "icon.ico"), ventana.show, salir)

    ventana.events.closing += al_cerrando
    ventana.events.closed += al_cerrar
    bandeja.iniciar()
    # Sin icon=, pywebview extrae el ícono de python.exe (el logo de Python) para
    # la barra de título y la barra de tareas.
    webview.start(icon=_ruta_recursos("orb_ui", "icon.ico"))
    bandeja.detener()


if __name__ == "__main__":
    main()
