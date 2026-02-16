"""
rag_pipeline.py — Pipeline RAG complet pour la génération de parcours

Ce module assemble toutes les briques :
1. Chargement du LLM (OpenAI, Groq, ou Ollama)
2. Récupération des documents pertinents via ChromaDB
3. Génération du parcours personnalisé via le LLM
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.schema import Document

from src.vectorstore import initialiser_vectorstore, get_retriever, creer_vectorstore
from src.data_loader import charger_documents
from src.prompt_templates import PROMPT_PARCOURS

load_dotenv()


def get_llm():
    """
    Crée et retourne le modèle de langage selon la configuration .env.
    
    Supporte 3 fournisseurs :
    - openai : GPT-4o-mini (payant mais très performant)
    - groq : Llama 3 (gratuit, tier limité)
    - ollama : Mistral en local (gratuit, nécessite installation)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    
    elif provider == "groq":
        from langchain_community.chat_models import ChatGroq
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    
    elif provider == "ollama":
        from langchain_community.llms import Ollama
        return Ollama(
            model=os.getenv("OLLAMA_MODEL", "mistral"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.3,
        )
    
    else:
        raise ValueError(
            f"Fournisseur LLM inconnu : '{provider}'. "
            "Utilisez 'openai', 'groq' ou 'ollama' dans .env"
        )


def formater_profil(profil: dict) -> str:
    """
    Formate le profil de l'étudiant en texte lisible pour le prompt.
    """
    parties = [
        f"Nom : {profil.get('nom', 'Non renseigné')}",
        f"Niveau actuel : {profil.get('niveau_actuel', 'Non renseigné')}",
        f"Objectif professionnel : {profil.get('objectif', 'En exploration')}",
    ]

    if profil.get("formation_choisie"):
        parties.append(f"Formation choisie : {profil['formation_choisie']}")

    if profil.get("matieres_fortes"):
        parties.append(f"Matières fortes : {', '.join(profil['matieres_fortes'])}")

    if profil.get("matieres_faibles"):
        parties.append(f"Matières faibles : {', '.join(profil['matieres_faibles'])}")

    if profil.get("contraintes"):
        parties.append(f"Contraintes : {profil['contraintes']}")

    if profil.get("experiences"):
        parties.append(f"Expériences : {profil['experiences']}")

    return "\n".join(parties)


def construire_requete(profil: dict) -> str:
    """
    Construit la requête de recherche vectorielle à partir du profil.
    L'objectif est de récupérer les documents les plus pertinents.
    """
    elements = []
    
    if profil.get("objectif"):
        elements.append(profil["objectif"])
    
    if profil.get("formation_choisie"):
        elements.append(profil["formation_choisie"])
    
    if profil.get("niveau_actuel"):
        elements.append(profil["niveau_actuel"])
    
    if profil.get("matieres_fortes"):
        elements.extend(profil["matieres_fortes"])
    
    return " ".join(elements) if elements else "orientation formation"


class PipelineRAG:
    """
    Pipeline RAG complet pour la génération de parcours personnalisés.

    Usage :
        pipeline = PipelineRAG()
        pipeline.initialiser()
        resultat = pipeline.generer_parcours(profil_etudiant)
    """

    def __init__(self):
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.chain = None
        self._initialise = False

    def initialiser(self, data_dir: str = None, rebuild: bool = False):
        """
        Initialise le pipeline : charge les données, crée/charge la base
        vectorielle, configure le LLM.

        Args:
            data_dir: Dossier des données (par défaut: data/)
            rebuild: Si True, reconstruit la base vectorielle même si elle existe
        """
        print("=== Initialisation du pipeline RAG ===\n")

        # 1. Base vectorielle
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        if rebuild or not Path(persist_dir).exists():
            print("📦 Création de la base vectorielle...")
            documents = charger_documents(data_dir)
            self.vectorstore = creer_vectorstore(documents, persist_dir)
        else:
            print("📦 Chargement de la base vectorielle existante...")
            self.vectorstore = initialiser_vectorstore(data_dir, persist_dir)

        # 2. Retriever
        self.retriever = get_retriever(self.vectorstore)
        print("✓ Retriever configuré\n")

        # 3. LLM
        print("🤖 Configuration du LLM...")
        self.llm = get_llm()
        print(f"✓ LLM configuré ({os.getenv('LLM_PROVIDER', 'openai')})\n")

        self._initialise = True
        print("=== Pipeline prêt ! ===\n")

    def generer_parcours(self, profil: dict) -> dict:
        """
        Génère un parcours personnalisé pour un étudiant.

        Args:
            profil: Dictionnaire contenant le profil de l'étudiant.
                    Clés attendues : nom, niveau_actuel, objectif,
                    formation_choisie, matieres_fortes, matieres_faibles,
                    contraintes, experiences

        Returns:
            Dictionnaire structuré contenant le parcours complet.
        """
        if not self._initialise:
            raise RuntimeError(
                "Le pipeline n'est pas initialisé. "
                "Appelez pipeline.initialiser() d'abord."
            )

        # 1. Formater le profil
        profil_texte = formater_profil(profil)
        print(f"👤 Profil de l'étudiant :\n{profil_texte}\n")

        # 2. Construire la requête et récupérer les documents
        requete = construire_requete(profil)
        print(f"🔍 Requête de recherche : {requete}")
        
        docs = self.retriever.invoke(requete)
        print(f"📄 {len(docs)} documents pertinents récupérés\n")

        # 3. Construire le contexte à partir des documents récupérés
        contexte = "\n\n---\n\n".join([doc.page_content for doc in docs])

        # 4. Construire le prompt final
        prompt_final = PROMPT_PARCOURS.format(
            profil_etudiant=profil_texte,
            context=contexte
        )

        # 5. Appeler le LLM
        print("🧠 Génération du parcours en cours...\n")
        reponse = self.llm.invoke(prompt_final)
        
        # Extraire le contenu texte de la réponse
        contenu = reponse.content if hasattr(reponse, 'content') else str(reponse)

        # 6. Parser le JSON de la réponse
        try:
            # Nettoyer le contenu (enlever les balises markdown si présentes)
            contenu_nettoye = contenu.strip()
            if contenu_nettoye.startswith("```json"):
                contenu_nettoye = contenu_nettoye[7:]
            if contenu_nettoye.startswith("```"):
                contenu_nettoye = contenu_nettoye[3:]
            if contenu_nettoye.endswith("```"):
                contenu_nettoye = contenu_nettoye[:-3]
            
            parcours = json.loads(contenu_nettoye.strip())
            print("✓ Parcours généré avec succès !\n")
            return parcours
        except json.JSONDecodeError:
            # Si le LLM ne retourne pas du JSON valide, on retourne le texte brut
            print("⚠ Le LLM n'a pas retourné du JSON valide. Retour du texte brut.\n")
            return {
                "resume": contenu,
                "etapes": [],
                "prerequis": {},
                "defis": [],
                "alternatives": [],
                "conseils_personnalises": [],
                "_raw_response": True
            }

    def rechercher_formations(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Recherche des formations pertinentes dans la base vectorielle.
        Utile pour explorer les options avant de générer un parcours.

        Args:
            query: Requête de recherche (ex: "intelligence artificielle master")
            top_k: Nombre de résultats à retourner

        Returns:
            Liste de formations pertinentes avec leurs scores
        """
        if not self._initialise:
            raise RuntimeError("Le pipeline n'est pas initialisé.")

        resultats = self.vectorstore.similarity_search_with_score(query, k=top_k)
        
        formations = []
        for doc, score in resultats:
            formations.append({
                "nom": doc.metadata.get("nom", ""),
                "type": doc.metadata.get("type", ""),
                "domaine": doc.metadata.get("domaine", ""),
                "score_similarite": round(1 - score, 3),  # Convertir distance en similarité
                "extrait": doc.page_content[:200] + "..."
            })
        
        return formations


# =============================================================================
# Script de test rapide
# =============================================================================

if __name__ == "__main__":
    # Exemple d'utilisation
    pipeline = PipelineRAG()
    pipeline.initialiser(rebuild=True)

    # Profil de test
    profil_test = {
        "nom": "Alice Dupont",
        "niveau_actuel": "Licence 3 Informatique",
        "objectif": "Devenir Data Scientist",
        "matieres_fortes": ["Programmation", "Mathématiques", "Statistiques"],
        "matieres_faibles": ["Anglais"],
        "contraintes": "Préfère rester dans le sud de la France",
        "experiences": "Stage de 2 mois en développement web",
    }

    parcours = pipeline.generer_parcours(profil_test)
    print(json.dumps(parcours, indent=2, ensure_ascii=False))
