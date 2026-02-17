"""
Module d'extraction de profils étudiants depuis PDF

Ce module extrait à la fois :
1. Le texte complet du formulaire pour la recherche sémantique
2. Les métadonnées structurées (contraintes) pour le filtrage

Utilisation :
    from src.pdf_extractor import extraire_profil_complet
    
    profil = extraire_profil_complet('data/profiles/formulaire.pdf')
    print(profil['metadonnees']['ville'])
    print(profil['texte_complet'])
"""

import re
from pathlib import Path
from typing import Dict, Any

try:
    import pdfplumber
except ImportError:
    raise ImportError(
        "pdfplumber n'est pas installé. "
        "Installez-le avec : pip install pdfplumber"
    )


def extraire_texte_pdf(pdf_path: str | Path) -> str:
    """
    Extrait tout le texte d'un PDF.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        
    Returns:
        Le texte complet extrait du PDF
        
    Raises:
        FileNotFoundError: Si le PDF n'existe pas
        Exception: Si l'extraction échoue
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"Fichier PDF introuvable : {pdf_path}")
    
    texte_complet = ""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texte_page = page.extract_text()
                if texte_page:
                    texte_complet += texte_page + "\n"
    except Exception as e:
        raise Exception(f"Erreur lors de l'extraction du PDF : {e}")
    
    return texte_complet.strip()


def parser_contraintes(texte: str) -> Dict[str, str]:
    """
    Parse les contraintes structurées depuis le texte du formulaire.
    
    Le formulaire contient une section "CONTRAINTES DE RECHERCHE" avec :
    - Ville souhaitée : ...
    - Niveau visé : ...
    - Type de formation : ...
    - Budget : ...
    
    Args:
        texte: Texte complet extrait du PDF
        
    Returns:
        Dictionnaire avec les contraintes extraites
    """
    contraintes = {}
    
    # Pattern pour extraire : "Clé : Valeur"
    patterns = {
        'ville': r'Ville souhait[eé]e\s*:\s*(.+?)(?:\n|$)',
        'niveau_vise': r'Niveau vis[eé]\s*:\s*(.+?)(?:\n|$)',
        'type_formation': r'Type de formation\s*:\s*(.+?)(?:\n|$)',
        'budget': r'Budget\s*:\s*(.+?)(?:\n|$)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, texte, re.IGNORECASE | re.MULTILINE)
        if match:
            contraintes[key] = match.group(1).strip()
    
    return contraintes


def parser_informations_personnelles(texte: str) -> Dict[str, str]:
    """
    Extrait les informations personnelles basiques.
    
    Args:
        texte: Texte complet extrait du PDF
        
    Returns:
        Dictionnaire avec nom, email, téléphone
    """
    infos = {}
    
    # Email
    email_match = re.search(r'[\w\.\-]+@[\w\.\-]+\.\w+', texte)
    if email_match:
        infos['email'] = email_match.group(0)
    
    # Téléphone
    tel_match = re.search(r'\+?\d{1,3}[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}', texte)
    if tel_match:
        infos['telephone'] = tel_match.group(0)
    
    # Nom (première ligne avant l'email)
    lignes = texte.split('\n')
    if lignes and email_match:
        # La première ligne contient souvent "Nom Email"
        premiere_ligne = lignes[0]
        # Séparer par l'email
        if infos['email'] in premiere_ligne:
            nom_partie = premiere_ligne.split(infos['email'])[0].strip()
            if nom_partie:
                infos['nom'] = nom_partie
    
    # Niveau actuel (ligne avec "Étudiant en ...")
    niveau_match = re.search(r'[ÉE]tudiant en (.+?)(?:\n|—|$)', texte, re.IGNORECASE)
    if niveau_match:
        infos['niveau_actuel'] = niveau_match.group(1).strip()
    
    return infos


def parser_sections_thematiques(texte: str) -> Dict[str, str]:
    """
    Extrait les sections thématiques du CV (objectif, compétences, etc.).
    
    Args:
        texte: Texte complet extrait du PDF
        
    Returns:
        Dictionnaire avec les sections identifiées
    """
    sections = {}
    
    # Liste des sections à extraire
    section_patterns = {
        'objectif': r'OBJECTIF PROFESSIONNEL\s*\n(.+?)(?=\n[A-ZÀÉÈÊ]{3,}|\Z)',
        'competences': r'COMP[ÉE]TENCES TECHNIQUES\s*\n(.+?)(?=\n[A-ZÀÉÈÊ]{3,}|\Z)',
        'langues': r'LANGUES\s*\n(.+?)(?=\n[A-ZÀÉÈÊ]{3,}|\Z)',
    }
    
    for key, pattern in section_patterns.items():
        match = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
    
    return sections


def extraire_profil_complet(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Extrait le profil complet d'un étudiant depuis un PDF de formulaire.
    
    Cette fonction combine :
    - Le texte intégral (pour vectorisation/recherche sémantique)
    - Les métadonnées structurées (pour filtrage)
    
    Args:
        pdf_path: Chemin vers le formulaire PDF
        
    Returns:
        Dictionnaire avec :
        - texte_complet: str - Texte brut du PDF
        - metadonnees: dict - Contraintes et infos extraites
        
    Example:
        >>> profil = extraire_profil_complet('data/profiles/formulaire.pdf')
        >>> print(profil['metadonnees']['ville'])
        'Paris ou Île-de-France'
        >>> print(profil['metadonnees']['budget'])
        'Public uniquement'
    """
    # 1. Extraire le texte complet
    texte_complet = extraire_texte_pdf(pdf_path)
    
    # 2. Parser les différentes sections
    contraintes = parser_contraintes(texte_complet)
    infos_perso = parser_informations_personnelles(texte_complet)
    sections = parser_sections_thematiques(texte_complet)
    
    # 3. Combiner toutes les métadonnées
    metadonnees = {
        **infos_perso,
        **contraintes,
        **sections,
    }
    
    return {
        'texte_complet': texte_complet,
        'metadonnees': metadonnees,
    }


# =============================================================================
# Script de test
# =============================================================================

if __name__ == "__main__":
    import json
    from pathlib import Path
    
    # Chemin du PDF de test
    pdf_test = Path(__file__).parent.parent / "data" / "profiles" / "formulaire_karim_messaoudi.pdf"
    
    if not pdf_test.exists():
        print(f"[ERREUR] PDF de test introuvable : {pdf_test}")
        exit(1)
    
    print(f"Test d'extraction sur : {pdf_test.name}")
    print("=" * 60)
    
    try:
        profil = extraire_profil_complet(pdf_test)
        
        print("\n[OK] Extraction reussie !")
        print("\n--- METADONNEES EXTRAITES ---")
        print(json.dumps(profil['metadonnees'], indent=2, ensure_ascii=False))
        
        print(f"\n--- TEXTE COMPLET ---")
        print(f"Longueur : {len(profil['texte_complet'])} caracteres")
        print(f"Apercu : {profil['texte_complet'][:300]}...")
        
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
