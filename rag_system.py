"""
Sistema RAG usando LangChain + FAISS.
Construye un índice local la primera vez; lo carga en los siguientes arranques.
"""
import shutil
from pathlib import Path
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Config


class RAGSystem:
    """Recuperación semántica con FAISS y embeddings multilingüe."""

    def __init__(self) -> None:
        print("Cargando embeddings (primera vez puede tardar ~30 s)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vector_store: FAISS | None = None
        self._load_or_build_index()

    # ------------------------------------------------------------------ #
    #  Índice                                                             #
    # ------------------------------------------------------------------ #

    def _load_or_build_index(self) -> None:
        index_path = Path(Config.FAISS_INDEX_PATH)
        if index_path.exists():
            print(f"✓ Índice FAISS cargado desde {index_path}")
            self.vector_store = FAISS.load_local(
                str(index_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            print("Construyendo índice FAISS por primera vez...")
            self.build_index()

    def build_index(self) -> None:
        """Construye (o reconstruye) el índice a partir de knowledge_base.py."""
        from knowledge_base import FACTUFACIL_DOCUMENTS

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", ", ", " "],
        )

        raw_docs = [
            Document(page_content=item["content"], metadata=item["metadata"])
            for item in FACTUFACIL_DOCUMENTS
        ]
        chunks = splitter.split_documents(raw_docs)
        print(f"  {len(raw_docs)} documentos → {len(chunks)} chunks")

        self.vector_store = FAISS.from_documents(chunks, self.embeddings)

        index_path = Path(Config.FAISS_INDEX_PATH)
        index_path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(index_path))
        print(f"✓ Índice guardado en {index_path}")

    def reindex(self) -> None:
        """Elimina el índice existente y lo reconstruye."""
        index_path = Path(Config.FAISS_INDEX_PATH)
        if index_path.exists():
            shutil.rmtree(str(index_path))
            print("Índice anterior eliminado.")
        self.build_index()

    # ------------------------------------------------------------------ #
    #  Recuperación                                                       #
    # ------------------------------------------------------------------ #

    def retrieve(self, query: str, k: int | None = None) -> List[Document]:
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k or Config.TOP_K)

    def retrieve_with_scores(
        self, query: str, k: int | None = None
    ) -> List[Tuple[Document, float]]:
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search_with_score(query, k=k or Config.TOP_K)

    def get_context(self, query: str) -> str:
        """Devuelve el contexto recuperado como texto plano."""
        docs = self.retrieve(query)
        return "\n\n---\n\n".join(doc.page_content for doc in docs) if docs else ""

    def get_stats(self) -> dict:
        if not self.vector_store:
            return {"indexed": False}
        return {
            "indexed": True,
            "index_path": Config.FAISS_INDEX_PATH,
            "embedding_model": Config.EMBEDDING_MODEL,
        }
