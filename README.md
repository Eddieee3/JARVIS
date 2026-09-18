# JARVIS (prototipo)

Asistente de consola con function-calling (OpenAI), memoria semántica persistente
(ChromaDB) y control de Windows / Android (ADB).

## Instalación

```bash
cd JARVIS_PROJECT
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y coloca tu clave de OpenAI:

```bash
copy .env.example .env
```

## Ejecución

```bash
python jarvis.py
```

Escribe una orden en la consola. Escribe `salir`, `apagar` o `shutdown` para
terminar. `Ctrl+C` también cierra la sesión de forma controlada.

## Subsistemas

- **windows_os.py** — control de ventanas (`pyautogui`), diagnóstico de
  CPU/RAM/procesos (`psutil`) y clasificación automática de carpetas por
  extensión. Requiere un entorno de escritorio con display; si no está
  disponible, JARVIS lo desactiva automáticamente y sigue funcionando.
- **android_os.py** — control de un dispositivo Android enlazado por ADB
  (`adb start-server`, depuración USB activada). Si no hay un dispositivo
  conectado, las órdenes móviles responden con un aviso en vez de fallar.
- **memory.py** — memoria episódica persistente en `.jarvis_memory/` (ChromaDB
  local, sin dependencias de pago) para recordar preferencias del usuario
  entre sesiones.

## Notas

- Requiere Python 3.10+ y una clave de API de OpenAI con acceso a `gpt-4o`.
- El control de Android es opcional: sin `adb` y sin un dispositivo enlazado,
  esas órdenes simplemente informan que el subsistema no está disponible.
