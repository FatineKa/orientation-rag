from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional

class Formation(BaseModel):
    """
    Modèle de données unifié pour les formations (Licence, Master, etc.)
    """
    # Identifiants
    nom: str = Field(..., description="Nom complet de la formation (ex: Licence Droit, Master IA)")
    etablissement: str = Field(..., description="Nom de l'établissement")
    ville: str = Field(..., description="Ville du site de formation")
    
    # Caractéristiques Académiques (Niveaux Logiques)
    niveau_entree: int = Field(..., description="Niveau d'entrée (0=Bac, 2=Bac+2, 3=Bac+3, 4=Bac+4)")
    niveau_sortie: int = Field(..., description="Niveau de sortie (2=CPGE, 3=Licence/BUT, 5=Master/Ingé)")
    duree: Optional[int] = Field(None, description="Durée en années")
    type_diplome: str = Field(..., description="Type de diplôme (Licence, Master, BUT, CPGE, Ingénieur...)")
    
    # Modalités
    modalite: Optional[str] = Field(None, description="Initial, Alternance, Continue...")
    url: Optional[str] = Field(None, description="Lien vers la fiche formation")
    
    # Matching & Qualité
    selectivite: Optional[str] = Field("Non renseigné", description="Niveau de sélectivité (ex: 'Formation sélective')")
    taux_acces: Optional[float] = Field(None, description="Taux d'accès en pourcentage (0-100)")
    domaine: Optional[str] = Field(None, description="Domaine disciplinaire (ex: Sciences, Droit...)")
    
    # Validation Logique
    @validator('niveau_sortie')
    def valider_progression(cls, v, values):
        if 'niveau_entree' in values and v <= values['niveau_entree']:
            raise ValueError(f"Le niveau de sortie ({v}) doit être supérieur au niveau d'entrée ({values['niveau_entree']})")
        return v

    @validator('taux_acces')
    def valider_taux(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Le taux d'accès doit être compris entre 0 et 100")
        return v
