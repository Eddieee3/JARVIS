import numpy as np
import pyttsx3
import speech_recognition as sr
import sounddevice as sd


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
        self._tts_engine = None

    def _obtener_motor_tts(self):
        # pyttsx3 no es seguro para hilos si se reutiliza el mismo engine entre
        # llamadas concurrentes; se crea uno por invocación de hablar().
        if self._tts_engine is None:
            self._tts_engine = pyttsx3.init()
        return self._tts_engine

    def hablar(self, texto):
        """Sintetiza voz a partir de texto usando el motor TTS local (SAPI5 en Windows)."""
        if not texto:
            return
        motor = self._obtener_motor_tts()
        motor.say(texto)
        motor.runAndWait()

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
