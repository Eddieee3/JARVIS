import os
import threading

import numpy as np
import pyttsx3
import speech_recognition as sr
import sounddevice as sd


def _es_voz_espanol(voz):
    # Los tokens SAPI5 traen el idioma en el id (TTS_MS_ES-MX_SABINA_11.0) y el
    # nombre completo dice "Spanish (Mexico)" / "Español".
    nombre = (voz.name or "").lower()
    ident = (voz.id or "").upper()
    return "_ES-" in ident or "spanish" in nombre or "español" in nombre or "espanol" in nombre


def _elegir_voz_espanol(voces):
    """Devuelve la mejor voz en español instalada, o None si no hay ninguna.

    Orden de preferencia: la indicada en JARVIS_VOZ (fragmento del nombre),
    luego español latinoamericano (es-MX), luego cualquier otra en español.
    """
    candidatas = [v for v in voces if _es_voz_espanol(v)]
    if not candidatas:
        return None
    pedida = os.environ.get("JARVIS_VOZ", "").strip().lower()
    if pedida:
        for v in candidatas:
            if pedida in (v.name or "").lower():
                return v
    for v in candidatas:
        if "_ES-MX_" in (v.id or "").upper():
            return v
    return candidatas[0]


class VoiceInterface:
    """Entrada por voz (STT) y salida por voz (TTS) para JARVIS.

    La captura de micrófono usa `sounddevice` en vez de PyAudio (que requiere
    compilar con Microsoft C++ Build Tools en Windows y no siempre tiene rueda
    binaria disponible). El audio grabado se envuelve como `sr.AudioData` para
    reutilizar los motores de reconocimiento de `SpeechRecognition` sin depender
    de su clase `Microphone`.
    """

    SAMPLE_RATE = 16000
    SAMPLE_WIDTH = 2  # bytes por muestra (int16)

    def __init__(self, idioma="es-ES"):
        self.idioma = idioma
        self.recognizer = sr.Recognizer()
        self._bloqueo_tts = threading.Lock()

    def hablar(self, texto):
        """Sintetiza voz a partir de texto usando el motor TTS local (SAPI5 en Windows)."""
        if not texto:
            return
        # Un engine de pyttsx3 queda atado al hilo que lo creó: reutilizarlo desde
        # otro hilo hace que runAndWait() vuelva al instante sin hablar. La app
        # llama a hablar() desde un hilo nuevo por respuesta, así que se crea un
        # engine por llamada, y el lock evita que dos respuestas se solapen.
        with self._bloqueo_tts:
            motor = pyttsx3.init()
            try:
                voz = _elegir_voz_espanol(motor.getProperty("voices"))
                if voz is not None:
                    motor.setProperty("voice", voz.id)
                else:
                    print("[Voz] Advertencia: no hay ninguna voz en español instalada en Windows; "
                          "se usa la voz por defecto (JARVIS hablará con acento extranjero).")
                motor.setProperty("rate", 175)
                motor.say(texto)
                motor.runAndWait()
            finally:
                try:
                    motor.stop()
                except Exception:
                    pass

    def escuchar(self, duracion_segundos=5):
        """Graba audio del micrófono por defecto y lo transcribe a texto.

        Devuelve una tupla (texto, error). Si el reconocimiento falla, texto es
        None y error trae el motivo; no lanza excepciones, para que la GUI no
        se caiga por un problema de micrófono o de red.
        """
        try:
            grabacion = sd.rec(
                int(duracion_segundos * self.SAMPLE_RATE),
                samplerate=self.SAMPLE_RATE,
                channels=1,
                dtype="int16",
            )
            sd.wait()
        except Exception as e:
            return None, f"No se pudo acceder al micrófono: {e}"

        audio_bytes = grabacion.astype(np.int16).tobytes()
        audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, self.SAMPLE_WIDTH)

        try:
            texto = self.recognizer.recognize_google(audio_data, language=self.idioma)
            return texto, None
        except sr.UnknownValueError:
            return None, "No se entendió el audio."
        except sr.RequestError as e:
            return None, f"Servicio de reconocimiento no disponible: {e}"
