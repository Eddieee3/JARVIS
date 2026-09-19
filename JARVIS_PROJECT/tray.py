import os
import sys
import winreg

import pystray
from PIL import Image

NOMBRE_APP = "JARVIS"
CLAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
ARGUMENTO_MINIMIZADO = "--minimizado"


def _comando_autostart():
    """Comando que Windows ejecutará al iniciar sesión."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" {ARGUMENTO_MINIMIZADO}'
    # Modo script: pythonw evita abrir una ventana de consola.
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    interprete = pythonw if os.path.exists(pythonw) else sys.executable
    script = os.path.abspath(sys.argv[0])
    return f'"{interprete}" "{script}" {ARGUMENTO_MINIMIZADO}'


def autostart_activo():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_RUN) as clave:
            valor, _ = winreg.QueryValueEx(clave, NOMBRE_APP)
        return valor == _comando_autostart()
    except OSError:
        return False


def fijar_autostart(activar):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_RUN, 0, winreg.KEY_SET_VALUE) as clave:
        if activar:
            winreg.SetValueEx(clave, NOMBRE_APP, 0, winreg.REG_SZ, _comando_autostart())
        else:
            try:
                winreg.DeleteValue(clave, NOMBRE_APP)
            except FileNotFoundError:
                pass


class BandejaSistema:
    """Ícono en la bandeja del sistema con menú: Mostrar / Iniciar con Windows / Salir."""

    def __init__(self, ruta_icono, al_mostrar, al_salir):
        self._al_mostrar = al_mostrar
        self._al_salir = al_salir
        imagen = Image.open(ruta_icono)
        self._icono = pystray.Icon(
            NOMBRE_APP,
            imagen,
            NOMBRE_APP,
            menu=pystray.Menu(
                pystray.MenuItem("Mostrar JARVIS", self._mostrar, default=True),
                pystray.MenuItem(
                    "Iniciar con Windows",
                    self._alternar_autostart,
                    checked=lambda item: autostart_activo(),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", self._salir),
            ),
        )

    def _mostrar(self, icono=None, item=None):
        self._al_mostrar()

    def _alternar_autostart(self, icono, item):
        fijar_autostart(not autostart_activo())

    def _salir(self, icono=None, item=None):
        self.detener()
        self._al_salir()

    def iniciar(self):
        # run_detached corre el bucle de la bandeja en su propio hilo, dejando
        # libre el hilo principal para pywebview.
        self._icono.run_detached()

    def detener(self):
        try:
            self._icono.stop()
        except Exception:
            pass
