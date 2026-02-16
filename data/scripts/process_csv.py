import pandas as pd
import json
from pathlib import Path
import numpy as np

def fix_encoding(text):
    """Réépare les doubles encodages (mojibake)"""
    if not isinstance(text, str): return text
    try:
        # Tente de corriger cp1252 -> utf-8 mal interprété
        return text.encode('cp1252').decode('utf-8')
    except:
        return text

def clean_text(text):
    if pd.isna(text) or text == 'nan':
        return ""
    text = str(text).strip()
    return fix_encoding(text)

def get_niveau_entree_sortie(row, type_fichier):
    """
    Détermine les niveaux d'entrée et de sortie selon le type de fichier et le nom de la formation.
    """
    nom = clean_text(row.get('Filière de formation détaillée bis', '')) + " " + clean_text(row.get('Filière de formation très agrégée', ''))
    nom = nom.lower()
    
    if type_fichier == 'licence':
        # Par défaut : Entrée Bac (0) -> Sortie Bac+3 (3)
        entree = 0
        sortie = 3
        
        # Cas Spéciaux
        if 'ingénieur' in nom or 'ingenieur' in nom:
            sortie = 5 # Ecoles d'ingé post-bac
        elif 'cpge' in nom or 'prepa' in nom or 'prépa' in nom:
            sortie = 2 # Prépas (Bac+2)
        elif 'bts' in nom:
            sortie = 2 # BTS (Bac+2)
            
        return entree, sortie
    
    elif type_fichier == 'master':
        # Master : Entrée Bac+3 (3) -> Sortie Bac+5 (5)
        return 3, 5
        
    return 0, 0 # Valeur par défaut de sécurité

def clean_taux(val):
    try:
        if pd.isna(val): return None
        return float(str(val).replace(',', '.'))
    except:
        return None

def find_col(df, keywords):
    """Trouve une colonne qui contient un des mots-clés"""
    for col in df.columns:
        if any(k in col for k in keywords):
            return col
    return None

def detect_domain(nom_formation):
    """
    Détecte automatiquement le domaine académique depuis le nom de la formation.
    Cette fonction est CRITIQUE pour la pertinence du RAG.
    """
    if not nom_formation:
        return "Autre"
    
    nom_lower = nom_formation.lower()
    
    # Informatique & Technologies
    if any(kw in nom_lower for kw in [
        'informatique', 'intelligence artificielle', 'ia', 'data', 'développement',
        'web', 'cybersécurité', 'réseau', 'numérique', 'logiciel', 'machine learning',
        'deep learning', 'big data', 'cloud', 'devops', 'sécurité informatique',
        'programmation', 'software', 'génie logiciel', 'système', 'blockchain'
    ]):
        return "Informatique et Technologies"
    
    # Droit & Sciences Juridiques
    if any(kw in nom_lower for kw in [
        'droit', 'juridique', 'notarial', 'avocat', 'justice', 'contentieux',
        'affaires publiques', 'propriété intellectuelle', 'fiscal', 'immobilier',
        'pénal', 'international', 'européen', 'constitutionnel'
    ]):
        return "Droit et Sciences Juridiques"
    
    # Santé & Médecine
    if any(kw in nom_lower for kw in [
        'médecine', 'infirmier', 'santé', 'pharmacie', 'kiné', 'sage-femme',
        'orthoptiste', 'médical', 'ergothérapie', 'psychomotricien', 'pass',
        'dentaire', 'vétérinaire', 'biologie médicale', 'santé publique'
    ]):
        return "Santé et Médecine"
    
    # Sciences (Maths, Physique, Chimie, Biologie)
    if any(kw in nom_lower for kw in [
        'mathématiques', 'physique', 'chimie', 'biologie', 'sciences',
        'géologie', 'astronomie', 'astrophysique', 'sciences de la vie',
        'sciences de la terre', 'sciences exactes', 'biotech'
    ]):
        return "Sciences"
    
    # Ingénierie (hors informatique)
    if any(kw in nom_lower for kw in [
        'ingénieur', 'génie civil', 'mécanique', 'électrique', 'énergétique',
        'matériaux', 'industriel', 'aéronautique', 'robotique', 'automatique',
        'électronique', 'télécommunications', 'génie des procédés'
    ]):
        return "Ingénierie"
    
    # Arts, Culture & Création
    if any(kw in nom_lower for kw in [
        'art', 'design', 'musique', 'théâtre', 'cinéma', 'création',
        'graphique', 'audiovisuel', 'architecture', 'mode', 'stylisme',
        'photographie', 'création artistique', 'beaux-arts', 'arts plastiques'
    ]):
        return "Arts, Culture et Création"
    
    # Économie, Gestion & Commerce
    if any(kw in nom_lower for kw in [
        'économie', 'gestion', 'management', 'commerce', 'finance',
        'marketing', 'comptabilité', 'entrepreneuriat', 'business',
        'rh', 'ressources humaines', 'administration', 'banque', 'assurance'
    ]):
        return "Économie et Gestion"
    
    # Sciences Humaines & Sociales
    if any(kw in nom_lower for kw in [
        'psychologie', 'sociologie', 'philosophie', 'histoire', 'géographie',
        'anthropologie', 'sciences sociales', 'sciences humaines', 'lettres',
        'linguistique', 'littérature', 'langues', 'lea', 'llce', 'fle'
    ]):
        return "Sciences Humaines et Sociales"
    
    # Éducation & Enseignement
    if any(kw in nom_lower for kw in [
        'enseignement', 'éducation', 'professorat', 'meef', 'professeur',
        'pédagogie', 'sciences de l\'éducation', 'formation des enseignants'
    ]):
        return "Éducation et Enseignement"
    
    # Sport & STAPS
    if any(kw in nom_lower for kw in [
        'sport', 'staps', 'activités physiques', 'éducation physique',
        'entraînement', 'management sportif'
    ]):
        return "Sport et STAPS"
    
    # Environnement & Développement Durable
    if any(kw in nom_lower for kw in [
        'environnement', 'écologie', 'développement durable', 'agronomie',
        'agriculture', 'foresterie', 'biodiversité', 'climat', 'énergies renouvelables'
    ]):
        return "Environnement et Développement Durable"
    
    # Communication & Journalisme
    if any(kw in nom_lower for kw in [
        'communication', 'journalisme', 'médias', 'information',
        'relations publiques', 'publicité'
    ]):
        return "Communication et Journalisme"
    
    return "Autre"



def process_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "data" / "raw"
    if not (raw_dir / "licences_300_lignes.csv").exists():
        raw_dir = base_dir / "data"
    
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    formations_list = []
    
    # 1. Traitement des Licences
    licence_path = raw_dir / "licences_300_lignes.csv"
    if licence_path.exists():
        print("Lecture des Licences...")
        df = pd.read_csv(licence_path, sep=',', on_bad_lines='skip', encoding='cp1252')
        # Normalize columns
        df.columns = df.columns.str.strip().str.replace('\xa0', 'à')
        print(f"DEBUG LICENCE COLS: {df.columns.tolist()}")
        
        # Mapping des colonnes (Licence)
        c_nom = find_col(df, ['bis'])  # "détaillée bis" (safer encoding)
        c_etab = find_col(df, ['tablissement'])  # Match Établissement or Etablissement
        c_ville = find_col(df, ['Commune'])
        c_type = find_col(df, ['très agrégée'])
        c_url = find_col(df, ['Lien', 'Parcoursup'])
        c_taux = find_col(df, ['Taux'])

        for _, row in df.iterrows():
            entree, sortie = get_niveau_entree_sortie(row, 'licence')
            
            nom_formation = clean_text(row.get(c_nom))
            formation = {
                "nom": nom_formation,
                "etablissement": clean_text(row.get(c_etab)),
                "ville": clean_text(row.get(c_ville)),
                "type_diplome": clean_text(row.get(c_type, 'Licence')),
                "modalite": "Formation initiale",
                "url": clean_text(row.get(c_url)),
                "taux_acces": clean_taux(row.get(c_taux)),
                "niveau_entree": entree,
                "niveau_sortie": sortie,
                "domaine": detect_domain(nom_formation)  # AJOUT CRITIQUE
            }
            formations_list.append(formation)

    # 2. Traitement des Masters
    master_path = raw_dir / "master_300_lignes.csv"
    if master_path.exists():
        print("Lecture des Masters...")
        df = pd.read_csv(master_path, sep=',', on_bad_lines='skip', encoding='cp1252')
        # Normalize columns
        df.columns = df.columns.str.strip().str.replace('\xa0', 'à')
        print(f"DEBUG MASTER COLS: {df.columns.tolist()}")
        
        # Mapping Colonnes (Master)
        c_mention = find_col(df, ['mention de master'])
        c_parcours = find_col(df, ['parcours'])
        c_etab = find_col(df, ['Nom officiel', 'eta_nom'])
        c_ville = find_col(df, ['Ville', 'ville'])
        c_mod = find_col(df, ['Modalités', 'modalite'])
        c_url = find_col(df, ['URL', 'fiche relative'])
        c_dom = find_col(df, ['Domaine', 'domaine'])

        for _, row in df.iterrows():
            entree, sortie = get_niveau_entree_sortie(row, 'master')
            mention = clean_text(row.get(c_mention))
            parcours = clean_text(row.get(c_parcours))
            
            nom_formation = f"Master {mention} - {parcours}".strip(' -')
            domaine_csv = clean_text(row.get(c_dom))  # Domaine du CSV (souvent vide)
            formation = {
                "nom": nom_formation,
                "etablissement": clean_text(row.get(c_etab)),
                "ville": clean_text(row.get(c_ville)),
                "type_diplome": "Master",
                "modalite": clean_text(row.get(c_mod)),
                "url": clean_text(row.get(c_url)),
                "domaine": domaine_csv if domaine_csv else detect_domain(nom_formation),  # Détection auto si vide
                "taux_acces": None, # Souvent absent ou à calculer différemment
                "niveau_entree": entree,
                "niveau_sortie": sortie
            }
            formations_list.append(formation)
            
    # 3. Export
    output_path = processed_dir / "formations.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formations_list, f, indent=4, ensure_ascii=False)
        
    print(f"[OK] Termine ! {len(formations_list)} formations exportees dans {output_path}")

if __name__ == "__main__":
    process_data()
