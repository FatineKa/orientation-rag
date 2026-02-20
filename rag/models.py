# models.py
# Modeles Pydantic pour les formations (20 variables)
# et le profil etudiant (14 variables)

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Formation(BaseModel):
    """Modele de donnees pour une formation (20 variables)."""

    # Identification
    nom: str = Field(..., description="Nom complet de la formation")
    etablissement: str = Field(..., description="Nom de l'etablissement")
    ville: str = Field(..., description="Ville du site de formation")
    type_etablissement: str = Field(
        "Non renseigne", description="Public / Prive / Consulaire"
    )

    # Caracteristiques
    niveau_diplome: str = Field(..., description="Licence / Master / BUT / BTS")
    duree: str = Field("Variable", description="Duree estimee (ex: 3 ans)")
    modalite: str = Field("Formation initiale", description="Presentiel / Alternance / A distance")
    langue_enseignement: Optional[str] = Field(
        None, description="Francais / Anglais / Bilingue"
    )

    # Admission
    niveau_entree: str = Field(..., description="Bac / Bac+3 / Bac+5")
    prerequis_academiques: Optional[list[str]] = Field(
        None, description="Prerequis d'admission"
    )
    selectivite: str = Field("Non renseigne", description="Accessible / Selectif / Tres selectif")
    frais_scolarite: Optional[float] = Field(None, description="Frais annuels en euros")

    # Administratif
    plateforme_candidature: Optional[str] = Field(
        None, description="Parcoursup / MonMaster / Candidature directe"
    )
    documents_requis: Optional[list[str]] = Field(None, description="Documents a fournir")
    dates_candidature: Optional[dict] = Field(
        None, description="ouverture, cloture, rentree"
    )

    # Debouches
    competences_acquises: Optional[list[str]] = Field(None, description="Competences developpees")
    debouches_metiers: Optional[list[str]] = Field(None, description="Metiers accessibles")

    # Contexte RAG
    defis_courants: Optional[list[str]] = Field(None, description="Difficultes frequentes")
    conseils_candidature: Optional[list[str]] = Field(None, description="Conseils pour candidater")
    alternatives: Optional[list[str]] = Field(None, description="Formations similaires")

    # Metadonnees
    domaine: Optional[str] = Field(None, description="Domaine disciplinaire")
    taux_acces: Optional[float] = Field(None, description="Taux d'acces (0-100)")
    url: Optional[str] = Field(None, description="Lien fiche formation")
    academie: Optional[str] = Field(None)
    capacite: Optional[int] = Field(None)
    licences_conseillees: Optional[str] = Field(None)

    @field_validator("taux_acces")
    @classmethod
    def valider_taux(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Le taux d'acces doit etre entre 0 et 100")
        return v


class ProfilEtudiant(BaseModel):
    """Modele de donnees pour le profil etudiant (14 variables)."""

    # Academique
    niveau_actuel: str = Field(
        ..., description="Niveau academique actuel",
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
        examples=[["Travail en equipe", "Autonome"]]
    )
    langues: Optional[list[dict]] = Field(
        None, description="Langues et niveaux",
        examples=[[{"langue": "Anglais", "niveau": "B2"}]]
    )
    experiences_stages: list[str] = Field(
        default=[], description="Experiences pro et projets",
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
        examples=[["Intelligence Artificielle", "Environnement"]]
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
