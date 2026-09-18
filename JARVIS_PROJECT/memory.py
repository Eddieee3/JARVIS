import chromadb
from chromadb.utils import embedding_functions
import os

class JarvisMemory:
    def __init__(self):
        # Inicializa base de datos persistente en la carpeta local .jarvis_memory
        self.chroma_client = chromadb.PersistentClient(path="./.jarvis_memory")
        # Usamos el modelo embebido por defecto para no depender de APIs de pago en la memoria
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.chroma_client.get_or_create_collection(
            name="jarvis_episodic_memory", 
            embedding_function=self.emb_fn
        )

    def recordar_dato(self, clave_contexto, informacion):
        """Guarda un hábito o preferencia del usuario (sobrescribe si la clave ya existía)."""
        self.collection.upsert(
            documents=[informacion],
            metadatas=[{"type": "user_preference"}],
            ids=[clave_contexto]
        )
        return f"Entendido, señor. He registrado lo siguiente en mis bancos de datos: '{informacion}'."

    def recuperar_contexto(self, consulta, n_resultados=1):
        """Busca en la base vectorial similitudes con la orden actual."""
        if self.collection.count() == 0:
            return None
        results = self.collection.query(
            query_texts=[consulta],
            n_results=min(n_resultados, self.collection.count())
        )
        if results and results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0][0]
        return None