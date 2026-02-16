"""
api.py — API FastAPI pour la génération de parcours personnalisés

Endpoints :
- POST /generer-parcours : Génère un parcours complet pour un étudiant
- POST /rechercher-formations : Recherche des formations pertinentes
- GET /health : Vérification que l'API fonctionne
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from src.rag_pipeline import PipelineRAG


# =============================================================================
# Instance globale du pipeline
# =============================================================================

pipeline = PipelineRAG()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise le pipeline au démarrage de l'API."""
    print("\n🚀 Démarrage de l'API...")
    pipeline.initialiser(rebuild=False)
    yield
    print("\n👋 Arrêt de l'API")


# =============================================================================
# Application FastAPI
# =============================================================================

app = FastAPI(
    title="API Orientation — Génération de Parcours",
    description=(
        "Système intelligent de génération de parcours académiques "
        "personnalisés basé sur RAG (Retrieval-Augmented Generation)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Autoriser les requêtes depuis n'importe quelle origine (utile en développement)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Modèles de données (Pydantic)
# =============================================================================

class ProfilEtudiant(BaseModel):
    """Profil de l'étudiant utilisé pour la génération du parcours."""
    nom: str = Field(..., description="Nom de l'étudiant", examples=["Alice Dupont"])
    niveau_actuel: str = Field(
        ..., description="Niveau d'études actuel",
        examples=["Licence 3 Informatique"]
    )
    objectif: str = Field(
        ..., description="Objectif professionnel ou formation visée",
        examples=["Devenir Data Scientist"]
    )
    formation_choisie: str | None = Field(
        None, description="Formation spécifique choisie (optionnel)",
        examples=["Master Data Science - Toulouse"]
    )
    matieres_fortes: list[str] = Field(
        default=[], description="Matières dans lesquelles l'étudiant excelle",
        examples=[["Programmation", "Mathématiques"]]
    )
    matieres_faibles: list[str] = Field(
        default=[], description="Matières où l'étudiant a des difficultés",
        examples=[["Anglais"]]
    )
    contraintes: str | None = Field(
        None, description="Contraintes géographiques, financières, etc.",
        examples=["Rester en Île-de-France"]
    )
    experiences: str | None = Field(
        None, description="Expériences professionnelles ou stages",
        examples=["Stage de 2 mois en développement web"]
    )


class RechercheFormation(BaseModel):
    """Requête de recherche de formations."""
    query: str = Field(
        ..., description="Texte de recherche",
        examples=["intelligence artificielle master"]
    )
    top_k: int = Field(
        default=5, description="Nombre de résultats", ge=1, le=20
    )


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Vérifie que l'API et le pipeline fonctionnent."""
    return {
        "status": "ok",
        "pipeline_initialise": pipeline._initialise,
        "message": "L'API de génération de parcours est opérationnelle."
    }


@app.post("/generer-parcours")
async def generer_parcours(profil: ProfilEtudiant):
    """
    Génère un parcours personnalisé pour un étudiant.

    Le système :
    1. Recherche les formations pertinentes via RAG
    2. Combine le profil avec les données récupérées
    3. Génère un parcours détaillé via le LLM
    """
    if not pipeline._initialise:
        raise HTTPException(
            status_code=503,
            detail="Le pipeline n'est pas encore initialisé. Réessayez dans quelques secondes."
        )

    try:
        parcours = pipeline.generer_parcours(profil.model_dump())
        return {
            "success": True,
            "profil": profil.model_dump(),
            "parcours": parcours,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du parcours : {str(e)}"
        )


@app.post("/rechercher-formations")
async def rechercher_formations(recherche: RechercheFormation):
    """
    Recherche des formations pertinentes dans la base vectorielle.
    Utile pour l'exploration avant la génération d'un parcours.
    """
    if not pipeline._initialise:
        raise HTTPException(
            status_code=503,
            detail="Le pipeline n'est pas encore initialisé."
        )

    try:
        resultats = pipeline.rechercher_formations(recherche.query, recherche.top_k)
        return {
            "success": True,
            "query": recherche.query,
            "resultats": resultats,
            "nb_resultats": len(resultats),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche : {str(e)}"
        )


@app.post("/rebuild-vectorstore")
async def rebuild_vectorstore():
    """
    Reconstruit la base vectorielle à partir des données.
    Utile après avoir mis à jour les fichiers JSON dans data/.
    """
    try:
        pipeline.initialiser(rebuild=True)
        return {
            "success": True,
            "message": "Base vectorielle reconstruite avec succès."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la reconstruction : {str(e)}"
        )
