"""
vectorstore.py — Gestion de la base vectorielle ChromaDB

Ce module gère la création, le chargement et la recherche dans la base
vectorielle qui stocke les embeddings des documents (formations, métiers).
"""

import os
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document

from dotenv import load_dotenv

load_dotenv()

# Configuration par défaut
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))


def get_embeddings(model_name: str = None) -> HuggingFaceEmbeddings:
    """
    Crée et retourne le modèle d'embedding.

    Le modèle all-MiniLM-L6-v2 est léger (~80MB) et gratuit.
    Il tourne en local, pas besoin d'API.
    """
    model_name = model_name or EMBEDDING_MODEL
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )


def decouper_documents(documents: list[Document]) -> list[Document]:
    """
    Découpe les documents en chunks plus petits pour une meilleure
    recherche vectorielle.

    Pour les fiches formations qui sont déjà assez courtes,
    on les garde telles quelles si elles font moins de CHUNK_SIZE caractères.
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
            # Le document est assez court, on le garde tel quel
            chunks.append(doc)
        else:
            # On découpe en morceaux
            sous_docs = splitter.split_documents([doc])
            # On propage les métadonnées du parent
            for sd in sous_docs:
                sd.metadata.update(doc.metadata)
            chunks.extend(sous_docs)

    print(f"→ {len(documents)} documents découpés en {len(chunks)} chunks")
    return chunks


def creer_vectorstore(
    documents: list[Document],
    persist_dir: str = None,
    embeddings=None,
) -> Chroma:
    """
    Crée une nouvelle base vectorielle ChromaDB à partir des documents.

    Args:
        documents: Liste de Documents LangChain à indexer
        persist_dir: Dossier où persister la base (par défaut: ./chroma_db)
        embeddings: Modèle d'embedding (par défaut: all-MiniLM-L6-v2)

    Returns:
        Instance ChromaDB prête pour la recherche
    """
    persist_dir = persist_dir or CHROMA_PERSIST_DIR
    embeddings = embeddings or get_embeddings()

    # Découper les documents
    chunks = decouper_documents(documents)

    # Créer la base vectorielle
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="orientation_formations",
    )

    print(f"✓ Base vectorielle créée avec {len(chunks)} chunks dans {persist_dir}")
    return vectorstore


def charger_vectorstore(
    persist_dir: str = None,
    embeddings=None,
) -> Chroma:
    """
    Charge une base vectorielle existante.

    Args:
        persist_dir: Dossier où la base est persistée
        embeddings: Modèle d'embedding (doit être le même que lors de la création)

    Returns:
        Instance ChromaDB chargée
    """
    persist_dir = persist_dir or CHROMA_PERSIST_DIR
    embeddings = embeddings or get_embeddings()

    if not Path(persist_dir).exists():
        raise FileNotFoundError(
            f"Base vectorielle introuvable dans {persist_dir}. "
            "Exécutez d'abord la création avec creer_vectorstore()."
        )

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="orientation_formations",
    )

    print(f"✓ Base vectorielle chargée depuis {persist_dir}")
    return vectorstore


def get_retriever(vectorstore: Chroma, top_k: int = None):
    """
    Crée un retriever à partir de la base vectorielle.

    Args:
        vectorstore: Instance ChromaDB
        top_k: Nombre de documents à retourner (par défaut: 5)

    Returns:
        Retriever LangChain configuré
    """
    top_k = top_k or int(os.getenv("TOP_K_DOCUMENTS", "5"))
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )


def initialiser_vectorstore(data_dir: str = None, persist_dir: str = None) -> Chroma:
    """
    Fonction utilitaire : charge les données et crée la base vectorielle.
    
    Si la base existe déjà, la recharge. Sinon, la crée depuis les données.
    """
    persist_dir = persist_dir or CHROMA_PERSIST_DIR

    if Path(persist_dir).exists():
        print("Base vectorielle existante trouvée, chargement...")
        return charger_vectorstore(persist_dir)
    
    print("Création d'une nouvelle base vectorielle...")
    from src.data_loader import charger_documents
    documents = charger_documents(data_dir)
    return creer_vectorstore(documents, persist_dir)
