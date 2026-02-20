# vectorstore.py
# Gestion de la base vectorielle ChromaDB
# Permet de creer, charger et interroger l'index des formations

import os
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from dotenv import load_dotenv

load_dotenv()

# Chemins et parametres par defaut
_PROJECT_DIR = Path(__file__).parent.parent
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(_PROJECT_DIR / "data" / "chroma_db"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))


def get_embeddings(model_name: str = None) -> HuggingFaceEmbeddings:
    """
    Charge le modele d'embedding multilingue.
    Le modele tourne en local, pas besoin d'API externe.
    """
    model_name = model_name or EMBEDDING_MODEL
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )


def decouper_documents(documents: list[Document]) -> list[Document]:
    """
    Decoupe les documents longs en morceaux (chunks) plus petits
    pour ameliorer la recherche vectorielle.
    Les documents courts sont gardes tels quels.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )

    chunks = []
    for doc in documents:
        if len(doc.page_content) <= CHUNK_SIZE:
            chunks.append(doc)
        else:
            sous_docs = splitter.split_documents([doc])
            for sd in sous_docs:
                sd.metadata.update(doc.metadata)
            chunks.extend(sous_docs)

    print(f"  {len(documents)} documents decoupes en {len(chunks)} chunks")
    return chunks


def creer_vectorstore(
    documents: list[Document],
    persist_dir: str = None,
    embeddings=None,
) -> Chroma:
    """
    Cree une nouvelle base vectorielle ChromaDB a partir des documents.
    Les embeddings sont generes et stockes sur disque.
    """
    persist_dir = persist_dir or CHROMA_PERSIST_DIR
    embeddings = embeddings or get_embeddings()

    # Decouper les documents
    chunks = decouper_documents(documents)

    # Creer la base vectorielle
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="orientation_formations",
    )

    print(f"  Base vectorielle creee avec {len(chunks)} chunks dans {persist_dir}")
    return vectorstore


def charger_vectorstore(
    persist_dir: str = None,
    embeddings=None,
) -> Chroma:
    """
    Charge une base vectorielle existante depuis le disque.
    Le modele d'embedding doit etre le meme que lors de la creation.
    """
    persist_dir = persist_dir or CHROMA_PERSIST_DIR
    embeddings = embeddings or get_embeddings()

    if not Path(persist_dir).exists():
        raise FileNotFoundError(
            f"Base vectorielle introuvable dans {persist_dir}. "
            "Executez d'abord la creation avec creer_vectorstore()."
        )

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="orientation_formations",
    )

    print(f"  Base vectorielle chargee depuis {persist_dir}")
    return vectorstore


def get_retriever(vectorstore: Chroma, top_k: int = None):
    """
    Cree un retriever LangChain a partir de la base vectorielle.
    Le retriever retourne les top_k documents les plus similaires.
    """
    top_k = top_k or int(os.getenv("TOP_K_DOCUMENTS", "5"))
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )


def initialiser_vectorstore(data_dir: str = None, persist_dir: str = None) -> Chroma:
    """
    Charge la base vectorielle si elle existe,
    sinon la cree a partir des donnees.
    """
    persist_dir = persist_dir or CHROMA_PERSIST_DIR

    if Path(persist_dir).exists():
        print("Base vectorielle existante trouvee, chargement...")
        return charger_vectorstore(persist_dir)
    
    print("Creation d'une nouvelle base vectorielle...")
    from src.data_loader import charger_documents
    documents = charger_documents(data_dir)
    return creer_vectorstore(documents, persist_dir)
