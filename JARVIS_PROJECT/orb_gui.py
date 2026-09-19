import os
import threading

import webview

from jarvis import JarvisCore
from voice import VoiceInterface


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


def main():
    api = OrbAPI()
    directorio_ui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orb_ui", "index.html")
    ventana = webview.create_window(
        "JARVIS",
        directorio_ui,
        js_api=api,
        width=1000,
        height=720,
        min_size=(640, 480),
        background_color="#030814",
    )

    def al_cerrar():
        if api.jarvis is not None:
            try:
                api.jarvis.scheduler.shutdown(wait=False)
            except Exception:
                pass

    ventana.events.closed += al_cerrar
    webview.start()


if __name__ == "__main__":
    main()
