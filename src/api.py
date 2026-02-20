# api.py
# API FastAPI pour le systeme d'orientation
# Expose les endpoints pour generer des parcours et rechercher des formations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from contextlib import asynccontextmanager

from src.rag_pipeline import PipelineRAG


# Instance globale du pipeline
pipeline = PipelineRAG()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise le pipeline au demarrage de l'API."""
    print("\nDemarrage de l'API...")
    pipeline.initialiser(rebuild=False)
    yield
    print("\nArret de l'API")


# Application FastAPI
app = FastAPI(
    title="API Orientation - Generation de Parcours",
    description=(
        "Systeme de generation de parcours academiques "
        "personnalises base sur RAG."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modeles de donnees - Profil etudiant avec 14 variables
class ProfilEtudiant(BaseModel):
    """Profil complet de l'etudiant (14 variables)."""

    # Academique
    niveau_actuel: str = Field(
        ..., description="Niveau d'etudes actuel",
        examples=["Etudiant en L3 Informatique"]
    )
    matieres_fortes: list[str] = Field(
        default=[], description="Matieres ou l'etudiant excelle",
        examples=[["Maths", "Programmation"]]
    )
    matieres_faibles: list[str] = Field(
        default=[], description="Matieres a renforcer",
        examples=[["Physique", "Anglais"]]
    )
    notes_par_matiere: Optional[dict] = Field(
        None, description="Notes par matiere",
        examples=[{"Maths": 15, "Info": 14}]
    )

    # Competences
    competences_techniques: list[str] = Field(
        default=[], description="Competences techniques acquises",
        examples=[["Python", "SQL", "Git"]]
    )
    qualites_personnelles: list[str] = Field(
        default=[], description="Qualites personnelles",
        examples=[["Travail en equipe", "Rigoureux"]]
    )
    langues: Optional[list[dict]] = Field(
        None, description="Langues et niveaux",
        examples=[[{"langue": "Anglais", "niveau": "B2"}]]
    )
    experiences_stages: list[str] = Field(
        default=[], description="Experiences professionnelles et projets",
        examples=[["Stage dev web 2 mois"]]
    )

    # Objectif et preferences
    objectif_professionnel: str = Field(
        ..., description="Metier ou domaine vise",
        examples=["Devenir Data Scientist"]
    )
    domaines_etudes_preferes: list[str] = Field(
        default=[], description="Domaines d'etudes souhaites",
        examples=[["Economie", "Finance"]]
    )
    centres_interet: list[str] = Field(
        default=[], description="Interets personnels",
        examples=[["Intelligence Artificielle"]]
    )
    type_formation_prefere: Optional[str] = Field(
        None, description="Alternance / Initial / A distance",
        examples=["Alternance"]
    )

    # Contraintes
    contraintes_geographiques: Optional[str] = Field(
        None, description="Zone geographique acceptable",
        examples=["Lyon ou Paris"]
    )
    budget: Optional[str] = Field(
        None, description="Capacite financiere",
        examples=["Public uniquement"]
    )


class RechercheFormation(BaseModel):
    """Requete de recherche de formations."""
    query: str = Field(
        ..., description="Texte de recherche",
        examples=["intelligence artificielle master"]
    )
    top_k: int = Field(
        default=5, description="Nombre de resultats", ge=1, le=20
    )


# Endpoints

@app.get("/health")
async def health_check():
    """Verifie que l'API et le pipeline fonctionnent."""
    return {
        "status": "ok",
        "pipeline_initialise": pipeline._initialise,
        "message": "L'API de generation de parcours est operationnelle.",
    }


@app.post("/generer-parcours")
async def generer_parcours(profil: ProfilEtudiant):
    """
    Genere un parcours personnalise pour un etudiant.
    Recherche les formations pertinentes via RAG puis
    genere le parcours avec le LLM.
    """
    if not pipeline._initialise:
        raise HTTPException(
            status_code=503,
            detail="Le pipeline n'est pas encore initialise.",
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
            detail=f"Erreur lors de la generation : {str(e)}",
        )


@app.post("/rechercher-formations")
async def rechercher_formations(recherche: RechercheFormation):
    """Recherche des formations dans la base vectorielle."""
    if not pipeline._initialise:
        raise HTTPException(
            status_code=503,
            detail="Le pipeline n'est pas encore initialise.",
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
            detail=f"Erreur lors de la recherche : {str(e)}",
        )


@app.post("/rebuild-vectorstore")
async def rebuild_vectorstore():
    """Reconstruit la base vectorielle a partir des donnees enrichies."""
    try:
        pipeline.initialiser(rebuild=True)
        return {
            "success": True,
            "message": "Base vectorielle reconstruite avec succes.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la reconstruction : {str(e)}",
        )
