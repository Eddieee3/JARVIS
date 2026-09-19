import os
import shutil

import pyautogui
import psutil


def _norm(ruta):
    return os.path.normcase(os.path.realpath(ruta))


def _es_ruta_protegida(ruta):
    """Raíces de disco, la carpeta de usuario en sí y el árbol del sistema no se reorganizan."""
    ruta = _norm(ruta)
    if os.path.dirname(ruta) == ruta:  # raíz de disco, p. ej. C:\
        return True
    perfil = os.environ.get("USERPROFILE")
    if perfil and ruta == _norm(perfil):
        return True
    for variable in ("WINDIR", "SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        valor = os.environ.get(variable)
        if valor:
            sistema = _norm(valor)
            if ruta == sistema or ruta.startswith(sistema + os.sep):
                return True
    return False


def _destino_libre(carpeta, nombre):
    destino = os.path.join(carpeta, nombre)
    if not os.path.exists(destino):
        return destino
    base, ext = os.path.splitext(nombre)
    n = 1
    while os.path.exists(os.path.join(carpeta, f"{base} ({n}){ext}")):
        n += 1
    return os.path.join(carpeta, f"{base} ({n}){ext}")


class WindowsController:
    def __init__(self):
        pyautogui.FAILSAFE = True  # Mover el mouse a la esquina detiene fallos mecánicos

    def gestionar_ventanas(self, accion, programa=None):
        if accion == "minimizar_todo":
            pyautogui.hotkey('win', 'd')
            return "Escritorio despejado."
        elif accion == "abrir" and programa:
            pyautogui.press('win')
            pyautogui.write(programa, interval=0.05)
            pyautogui.press('enter')
            return f"Ejecutando la directiva de apertura para {programa}."
        raise ValueError(
            f"Acción de interfaz gráfica no válida: accion={accion!r}, programa={programa!r}. "
            "Usa 'minimizar_todo', o 'abrir' indicando el programa."
        )

    def escanear_hardware(self):
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        procesos = sorted(psutil.process_iter(['name', 'cpu_percent']),
                          key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:3]
        top_apps = ", ".join([f"{p.info['name']} ({p.info['cpu_percent']}% CPU)" for p in procesos])
        return f"Diagnóstico actual: Carga de CPU al {cpu}%, memoria RAM al {ram}%. Procesos críticos: {top_apps}."

    def clasificar_directorio(self, ruta_directorio):
        if not os.path.exists(ruta_directorio):
            raise FileNotFoundError(f"La ruta '{ruta_directorio}' no existe.")
        if not os.path.isdir(ruta_directorio):
            raise NotADirectoryError(f"'{ruta_directorio}' no es una carpeta.")
        if _es_ruta_protegida(ruta_directorio):
            raise PermissionError(
                f"'{ruta_directorio}' es una carpeta del sistema, una raíz de disco o tu carpeta de usuario; "
                "por seguridad no se reorganiza. Indica una subcarpeta concreta."
            )

        movidos = 0
        for archivo in os.listdir(ruta_directorio):
            ruta_completa = os.path.join(ruta_directorio, archivo)
            if os.path.isfile(ruta_completa):
                ext = archivo.rsplit('.', 1)[-1].lower() if '.' in archivo else 'otros'
                carpeta_destino = os.path.join(ruta_directorio, ext.upper())
                os.makedirs(carpeta_destino, exist_ok=True)
                shutil.move(ruta_completa, _destino_libre(carpeta_destino, archivo))
                movidos += 1
        return f"Clasificación completada en la ruta {ruta_directorio}: {movidos} archivos organizados por extensión."
