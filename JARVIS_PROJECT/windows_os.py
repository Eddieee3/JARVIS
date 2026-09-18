import os
import pyautogui
import pywinauto
import psutil
from PIL import Image

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
        return "Acción de interfaz gráfica no válida."

    def escanear_hardware(self):
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        procesos = sorted(psutil.process_iter(['name', 'cpu_percent']), 
                          key=lambda x: x.info['cpu_percent'], reverse=True)[:3]
        top_apps = ", ".join([f"{p.info['name']} ({p.info['cpu_percent']}% CPU)" for p in procesos])
        return f"Diagnóstico actual: Carga de CPU al {cpu}%, memoria RAM al {ram}%. Procesos críticos: {top_apps}."

    def clasificar_directorio(self, ruta_directorio):
        if not os.path.exists(ruta_directorio):
            return "Error: Ruta de acceso local no encontrada."
        
        archivos = os.listdir(ruta_directorio)
        for archivo in archivos:
            ruta_completa = os.path.join(ruta_directorio, archivo)
            if os.path.isfile(ruta_completa):
                ext = archivo.split('.')[-1].lower() if '.' in archivo else 'otros'
                carpeta_destino = os.path.join(ruta_directorio, ext.upper())
                os.makedirs(carpeta_destino, exist_ok=True)
                os.rename(ruta_completa, os.path.join(carpeta_destino, archivo))
        return f"Clasificación completada en la ruta {ruta_directorio}. Archivos organizados por subtipos."