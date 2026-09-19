import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

# Importaciones de los módulos locales que creaste arriba
from memory import JarvisMemory
from windows_os import WindowsController
from android_os import AndroidController

# Empaquetado (PyInstaller): busca .env junto al .exe, no en el directorio
# temporal de extracción, para que se pueda editar sin reconstruir el binario.
if getattr(sys, "frozen", False):
    load_dotenv(os.path.join(os.path.dirname(sys.executable), ".env"))
else:
    load_dotenv()


class JarvisCore:
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY no está configurada. Copia .env.example a .env "
                "y coloca tu clave antes de iniciar JARVIS."
            )
        self.openai_client = OpenAI(api_key=api_key)

        # Instanciación de subsistemas de hardware y almacenamiento
        self.memoria = JarvisMemory()

        # El control de ventanas requiere un entorno de escritorio con display;
        # si no está disponible (p. ej. sesión remota o servidor), JARVIS sigue
        # operativo pero informa que ese subsistema está inactivo.
        try:
            self.windows = WindowsController()
        except Exception as e:
            print(f"[Sistema] Advertencia: subsistema de Windows no disponible ({e}).")
            self.windows = None

        self.android = AndroidController()

        # Motor de Automatizaciones en segundo plano (Cron-Jobs)
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def obtener_esquema_herramientas(self):
        """Mapeo estructurado para indicarle al modelo qué herramientas puede autogestionar."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "gestionar_ventanas",
                    "description": "Controla interfaces visuales o programas abiertos en Windows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["minimizar_todo", "abrir"]},
                            "programa": {"type": "string", "description": "Nombre de la aplicación, ej: 'chrome', 'notepad'"}
                        },
                        "required": ["accion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escanear_hardware",
                    "description": "Devuelve lecturas métricas en tiempo real de la CPU, RAM y procesos de Windows."
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clasificar_directorio",
                    "description": "Organiza automáticamente carpetas de archivos de forma masiva según su extensión.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ruta_directorio": {"type": "string", "description": "Ruta de la carpeta absoluta a ordenar"}
                        },
                        "required": ["ruta_directorio"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ejecutar_comando_android",
                    "description": "Controla el teléfono móvil enlazado (música, capturas, inyección de datos).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["abrir_spotify", "capturar_pantalla_movil", "escribir"]},
                            "texto_inyectar": {"type": "string", "description": "Texto si la acción requiere escritura"}
                        },
                        "required": ["accion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recordar_dato",
                    "description": "Guarda explícitamente información crítica sobre hábitos del usuario o preferencias para el futuro.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "clave_contexto": {"type": "string", "description": "ID único simplificado, ej: 'preferencia_cafe'"},
                            "informacion": {"type": "string", "description": "El dato puro que hay que almacenar en la base de datos"}
                        },
                        "required": ["clave_contexto", "informacion"]
                    }
                }
            }
        ]

    def _ejecutar_herramienta(self, nombre_funcion, argumentos):
        """Enrutamiento dinámico hacia los módulos importados. Puede lanzar excepciones."""
        if nombre_funcion in ("gestionar_ventanas", "escanear_hardware", "clasificar_directorio") and self.windows is None:
            return "El subsistema de Windows no está disponible en este entorno."
        elif nombre_funcion == "gestionar_ventanas":
            return self.windows.gestionar_ventanas(**argumentos)
        elif nombre_funcion == "escanear_hardware":
            return self.windows.escanear_hardware()
        elif nombre_funcion == "clasificar_directorio":
            return self.windows.clasificar_directorio(**argumentos)
        elif nombre_funcion == "ejecutar_comando_android":
            return self.android.ejecutar_comando(**argumentos)
        elif nombre_funcion == "recordar_dato":
            return self.memoria.recordar_dato(**argumentos)
        else:
            return "Error de enlace en la matriz de funciones."

    def procesar_orden(self, entrada_usuario, max_reintentos=2):
        """Procesa una orden de punta a punta y devuelve la respuesta final en texto.

        Si una herramienta falla, el fallo se registra en la memoria de errores y se
        le devuelve a la IA en la misma conversación para que reintente con un
        enfoque distinto antes de responder al usuario (hasta max_reintentos veces).
        """
        # 1. Recuperación automática de memoria semántica de fondo: preferencias y
        # fallos pasados relevantes, para no repetir errores conocidos.
        contexto_pasado = self.memoria.recuperar_contexto(entrada_usuario)
        errores_pasados = self.memoria.recuperar_errores_relevantes(entrada_usuario)

        system_prompt = "Eres JARVIS, un asistente inteligente autónomo avanzado integrado en los sistemas operativos del usuario. Responde de manera sofisticada, concisa y caballerosa."
        if contexto_pasado:
            system_prompt += f" Contexto recuperado de la base de datos de hábitos del usuario: {contexto_pasado}"
        if errores_pasados:
            system_prompt += (
                " Fallos registrados en el pasado con órdenes similares que debes evitar repetir: "
                + " | ".join(errores_pasados)
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": entrada_usuario},
        ]

        intentos_restantes = max_reintentos
        while True:
            # 2. Análisis semántico de la orden por el LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.obtener_esquema_herramientas(),
                tool_choice="auto",
            )
            mensaje_respuesta = response.choices[0].message
            tool_calls = mensaje_respuesta.tool_calls

            # 3. Si la IA no necesita herramientas, esta es la respuesta final.
            if not tool_calls:
                return mensaje_respuesta.content

            # Todas las tool_calls de este turno deben resolverse antes del próximo
            # turno: la API rechaza el turno si falta alguna.
            messages.append(mensaje_respuesta)
            hubo_fallo = False
            for tool_call in tool_calls:
                nombre_funcion = tool_call.function.name
                try:
                    argumentos = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    argumentos = {}

                try:
                    resultado_ejecucion = self._ejecutar_herramienta(nombre_funcion, argumentos)
                except Exception as e:
                    hubo_fallo = True
                    resultado_ejecucion = f"Fallo al ejecutar '{nombre_funcion}': {e}"
                    self.memoria.registrar_error(nombre_funcion, argumentos, e)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(resultado_ejecucion),
                })

            # 4. Si algo falló y quedan reintentos, se le devuelve el error a la IA
            # para que corrija su enfoque en la siguiente vuelta del bucle.
            if hubo_fallo and intentos_restantes > 0:
                intentos_restantes -= 1
                messages.append({
                    "role": "system",
                    "content": "Una o más herramientas fallaron. Corrige los argumentos o intenta un enfoque distinto antes de responder al usuario.",
                })
                continue

            # 5. Sin fallos (o reintentos agotados): pide la respuesta final en texto.
            # No se pasan `tools` aquí para evitar más tool_calls sin control.
            final_response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return final_response.choices[0].message.content

# =====================================================================
# INICIALIZADOR DE INTERFAZ POR CONSOLA (Listo para acoplar entrada de audio)
# =====================================================================
if __name__ == "__main__":
    print("[Matriz Central] Inicializando sistemas periféricos de JARVIS...")
    try:
        jarvis = JarvisCore()
    except RuntimeError as e:
        print(f"[Falla de Arranque]: {e}")
        raise SystemExit(1)
    print("[Matriz Central] Todos los sistemas se encuentran operativos, Señor.")
    
    while True:
        try:
            orden = input("\nInterfaz de comando activa: ")
            if orden.lower() in ['salir', 'shutdown', 'apagar']:
                print("[JARVIS]: Desactivando módulos locales de procesamiento. Buenas noches, señor.")
                jarvis.scheduler.shutdown()
                break
            if not orden.strip():
                continue

            respuesta = jarvis.procesar_orden(orden)
            print(f"\n[JARVIS]: {respuesta}")

        except KeyboardInterrupt:
            jarvis.scheduler.shutdown()
            break
        except Exception as e:
            print(f"[Falla de Núcleo]: {e}")