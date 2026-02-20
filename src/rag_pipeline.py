# rag_pipeline.py
# Pipeline RAG pour generer des parcours academiques personnalises
# Ce fichier assemble le LLM, la base vectorielle et le prompt

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document

from src.vectorstore import initialiser_vectorstore, get_retriever, creer_vectorstore
from src.data_loader import charger_documents
from src.prompt_templates import PROMPT_PARCOURS

load_dotenv()


def get_llm():
    """
    Initialise le modele de langage en fonction du fournisseur
    configure dans le fichier .env (openai, groq ou ollama).
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
        from langchain_groq import ChatGroq
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
    Transforme le dictionnaire du profil etudiant en texte lisible
    pour l'envoyer au LLM. Gere les 14 variables du profil.
    """
    parties = [
        f"Niveau actuel : {profil.get('niveau_actuel', 'Non renseigne')}",
        f"Objectif professionnel : {profil.get('objectif_professionnel', profil.get('objectif', 'En exploration'))}",
    ]

    if profil.get("matieres_fortes"):
        parties.append(f"Matieres fortes : {', '.join(profil['matieres_fortes'])}")

    if profil.get("matieres_faibles"):
        parties.append(f"Matieres faibles : {', '.join(profil['matieres_faibles'])}")

    if profil.get("notes_par_matiere"):
        notes = ", ".join(f"{k}: {v}/20" for k, v in profil["notes_par_matiere"].items())
        parties.append(f"Notes : {notes}")

    if profil.get("competences_techniques"):
        parties.append(f"Competences techniques : {', '.join(profil['competences_techniques'])}")

    if profil.get("qualites_personnelles"):
        parties.append(f"Qualites personnelles : {', '.join(profil['qualites_personnelles'])}")

    if profil.get("langues"):
        langues = ", ".join(f"{l['langue']} ({l['niveau']})" for l in profil["langues"])
        parties.append(f"Langues : {langues}")

    if profil.get("experiences_stages"):
        parties.append(f"Experiences : {', '.join(profil['experiences_stages'])}")

    if profil.get("domaines_etudes_preferes"):
        parties.append(f"Domaines preferes : {', '.join(profil['domaines_etudes_preferes'])}")

    if profil.get("centres_interet"):
        parties.append(f"Centres d'interet : {', '.join(profil['centres_interet'])}")

    if profil.get("type_formation_prefere"):
        parties.append(f"Modalite preferee : {profil['type_formation_prefere']}")

    if profil.get("contraintes_geographiques") or profil.get("contraintes"):
        parties.append(f"Contraintes geo : {profil.get('contraintes_geographiques', profil.get('contraintes', ''))}")

    if profil.get("budget"):
        parties.append(f"Budget : {profil['budget']}")

    return "\n".join(parties)


def construire_requete(profil: dict) -> str:
    """
    Construit la requete de recherche pour la base vectorielle
    a partir des champs cles du profil etudiant.
    """
    elements = []

    if profil.get("objectif_professionnel"):
        elements.append(profil["objectif_professionnel"])
    elif profil.get("objectif"):
        elements.append(profil["objectif"])

    if profil.get("domaines_etudes_preferes"):
        elements.extend(profil["domaines_etudes_preferes"])

    if profil.get("niveau_actuel"):
        elements.append(profil["niveau_actuel"])

    if profil.get("centres_interet"):
        elements.extend(profil["centres_interet"][:2])

    if profil.get("type_formation_prefere"):
        elements.append(profil["type_formation_prefere"])

    if profil.get("contraintes_geographiques") or profil.get("contraintes"):
        elements.append(profil.get("contraintes_geographiques", profil.get("contraintes", "")))

    return " ".join(elements) if elements else "orientation formation"


class PipelineRAG:
    """
    Classe principale du pipeline RAG.
    Elle gere l'initialisation de la base vectorielle,
    la recherche de documents et la generation de parcours.
    """

    def __init__(self):
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.chain = None
        self._initialise = False

    def initialiser(self, data_dir: str = None, rebuild: bool = False):
        """
        Initialise le pipeline : charge ou cree la base vectorielle
        et configure le LLM.
        """
        print("=== Initialisation du pipeline RAG ===\n")

        # Determiner le chemin de la base vectorielle
        project_root = Path(__file__).resolve().parent.parent
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
        if not Path(persist_dir).is_absolute():
            persist_dir = str(project_root / persist_dir)

        # Charger ou creer la base vectorielle
        if rebuild or not Path(persist_dir).exists():
            print("Creation de la base vectorielle...")
            documents = charger_documents(data_dir)
            self.vectorstore = creer_vectorstore(documents, persist_dir)
        else:
            print("Chargement de la base vectorielle existante...")
            self.vectorstore = initialiser_vectorstore(data_dir, persist_dir)

        # Configurer le retriever
        self.retriever = get_retriever(self.vectorstore)
        print("Retriever configure\n")

        # Configurer le LLM
        print("Configuration du LLM...")
        self.llm = get_llm()
        print(f"LLM configure ({os.getenv('LLM_PROVIDER', 'openai')})\n")

        self._initialise = True
        print("=== Pipeline pret ===\n")

    def generer_parcours(self, profil: dict) -> dict:
        """
        Genere un parcours personnalise a partir du profil etudiant.
        Etapes : formatage du profil, recherche vectorielle,
        construction du prompt, appel LLM, parsing du JSON.
        """
        if not self._initialise:
            raise RuntimeError(
                "Le pipeline n'est pas initialise. "
                "Appelez pipeline.initialiser() d'abord."
            )

        # Formater le profil en texte
        profil_texte = formater_profil(profil)
        print(f"Profil de l'etudiant :\n{profil_texte}\n")

        # Rechercher les documents pertinents
        requete = construire_requete(profil)
        print(f"Requete de recherche : {requete}")
        
        docs = self.retriever.invoke(requete)
        print(f"{len(docs)} documents pertinents recuperes\n")

        # Construire le contexte a partir des documents
        contexte = "\n\n---\n\n".join([doc.page_content for doc in docs])

        # Construire le prompt final
        prompt_final = PROMPT_PARCOURS.format(
            profil_etudiant=profil_texte,
            context=contexte
        )

        # Appeler le LLM
        print("Generation du parcours en cours...\n")
        reponse = self.llm.invoke(prompt_final)
        
        # Extraire le contenu texte
        contenu = reponse.content if hasattr(reponse, 'content') else str(reponse)

        # Parser le JSON de la reponse
        try:
            contenu_nettoye = contenu.strip()
            if contenu_nettoye.startswith("```json"):
                contenu_nettoye = contenu_nettoye[7:]
            if contenu_nettoye.startswith("```"):
                contenu_nettoye = contenu_nettoye[3:]
            if contenu_nettoye.endswith("```"):
                contenu_nettoye = contenu_nettoye[:-3]
            
            parcours = json.loads(contenu_nettoye.strip())
            print("Parcours genere avec succes\n")
            return parcours
        except json.JSONDecodeError:
            # Si le JSON n'est pas valide, on retourne le texte brut
            print("Le LLM n'a pas retourne du JSON valide\n")
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
        Recherche des formations dans la base vectorielle
        et retourne les resultats avec leur score de similarite.
        """
        if not self._initialise:
            raise RuntimeError("Le pipeline n'est pas initialise.")

        resultats = self.vectorstore.similarity_search_with_score(query, k=top_k)
        
        formations = []
        for doc, score in resultats:
            formations.append({
                "nom": doc.metadata.get("nom", ""),
                "type": doc.metadata.get("type", ""),
                "domaine": doc.metadata.get("domaine", ""),
                "score_similarite": round(1 - score, 3),
                "extrait": doc.page_content[:200] + "..."
            })
        
        return formations


# Test rapide
if __name__ == "__main__":
    pipeline = PipelineRAG()
    pipeline.initialiser(rebuild=True)

    # Profil de test avec les 14 variables
    profil_test = {
        "niveau_actuel": "Licence 3 Informatique",
        "objectif_professionnel": "Devenir Data Scientist",
        "matieres_fortes": ["Programmation", "Mathematiques", "Statistiques"],
        "matieres_faibles": ["Anglais"],
        "notes_par_matiere": {"Maths": 16, "Informatique": 15, "Anglais": 10},
        "competences_techniques": ["Python", "SQL", "Machine Learning"],
        "qualites_personnelles": ["Rigoureux", "Curieux", "Travail en equipe"],
        "langues": [{"langue": "Francais", "niveau": "C2"}, {"langue": "Anglais", "niveau": "B1"}],
        "experiences_stages": ["Stage 2 mois developpement web"],
        "domaines_etudes_preferes": ["Data Science", "Intelligence Artificielle"],
        "centres_interet": ["IA", "Analyse de donnees", "Environnement"],
        "type_formation_prefere": "Formation initiale",
        "contraintes_geographiques": "Sud de la France",
        "budget": "Public uniquement",
    }

    parcours = pipeline.generer_parcours(profil_test)
    print(json.dumps(parcours, indent=2, ensure_ascii=False))
