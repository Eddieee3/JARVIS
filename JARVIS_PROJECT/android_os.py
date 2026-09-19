import os
from ppadb.client import Client as AdbClient

class AndroidController:
    def __init__(self):
        self.device = self._inicializar_conexion()

    def _inicializar_conexion(self):
        try:
            client = AdbClient(host="127.0.0.1", port=5037)
            devices = client.devices()
            if len(devices) > 0:
                print(f"[Sistema] Enlace ADB establecido con dispositivo móvil: {devices[0].serial}")
                return devices[0]
            print("[Sistema] Advertencia: No se detectaron terminales Android activas en el puerto de depuración.")
            return None
        except Exception:
            return None

    def ejecutar_comando(self, accion, texto_inyectar=None):
        if not self.device:
            return "No se puede ejecutar la orden: El terminal Android no responde o no está vinculado vía ADB."
        
        if accion == "abrir_spotify":
            self.device.shell("am start -n com.spotify.music/com.spotify.music.MainActivity")
            self.device.shell("input keyevent 126") # Inyecta la constante global de hardware 'MEDIA_PLAY'
            return "Unidad de audio multimedia móvil activada."
            
        elif accion == "capturar_pantalla_movil":
            imagen_binaria = self.device.screencap()
            ruta_guardado = os.path.abspath("phone_runtime_capture.png")
            with open(ruta_guardado, "wb") as f:
                f.write(imagen_binaria)
            return f"Captura del terminal móvil almacenada exitosamente en la raíz del entorno: {ruta_guardado}"
            
        elif accion == "escribir" and texto_inyectar:
            texto_seguro = texto_inyectar.replace(" ", "%s") # Protocolo ADB requiere escapar espacios vacíos
            self.device.shell(f"input text {texto_seguro}")
            return "Carga útil de texto enviada al dispositivo."
            
        raise ValueError(
            f"Instrucción móvil no válida: accion={accion!r}. "
            "Usa 'abrir_spotify', 'capturar_pantalla_movil' o 'escribir' (con texto_inyectar)."
        )