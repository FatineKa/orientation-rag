import requests
import json
import time
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

class ParcoursupFetcher:
    """Récupère des formations depuis l'API Parcoursup officielle."""
    
    BASE_URL = "https://data.enseignementsup-recherche.gouv.fr/api/records/1.0/search/"
    DATASET = "fr-esr-parcoursup"
    
    def __init__(self):
        self.session = requests.Session()
    
    def fetch_formations(self, max_formations=1000, types_diplomes=None):
        """
        Récupère des formations depuis Parcoursup.
        
        Args:
            max_formations: Nombre max de formations à récupérer
            types_diplomes: Liste de types (ex: ['Licence', 'Master'])
        
        Returns:
            Liste de dictionnaires de formations
        """
        formations = []
        rows_per_page = 100  # API limite à 1000, mais on fait par batch
        start = 0
        
        print(f"Récupération de {max_formations} formations depuis Parcoursup...")
        
        with tqdm(total=max_formations) as pbar:
            while len(formations) < max_formations:
                params = {
                    "dataset": self.DATASET,
                    "rows": min(rows_per_page, max_formations - len(formations)),
                    "start": start,
                }
                
                # NOTE: On ne filtre PAS par l'API car refine.fili ne supporte pas les listes
                # On récupère tout et on filtre après conversion
                
                try:
                    response = self.session.get(self.BASE_URL, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get('records'):
                        print("\nPlus de formations disponibles")
                        break
                    
                    # Convertir les records en format compatible
                    for record in data['records']:
                        formation = self._convert_record(record)
                        if formation:  # Si conversion réussie
                            # Filtrer par type si spécifié
                            if types_diplomes is None or formation['type_diplome'] in types_diplomes:
                                formations.append(formation)
                                pbar.update(1)
                    
                    start += rows_per_page
                    time.sleep(0.2)  # Rate limiting respectueux
                    
                except requests.exceptions.RequestException as e:
                    print(f"\nErreur API: {e}")
                    break
        
        print(f"\nTotal récupéré: {len(formations)} formations")
        return formations
    
    def _convert_record(self, record: Dict) -> Dict:
        """Convertit un record Parcoursup vers le format formations.json"""
        fields = record.get('fields', {})
        
        # Validation minimale
        nom = fields.get('lib_for_voe_ins') or fields.get('lib_for_voe')
        if not nom:
            return None
        
        # Détection du type de diplôme
        fili = fields.get('fili', '')
        type_diplome = self._map_filiere(fili)
        
        # Détection du niveau
        niveau_entree, niveau_sortie = self._detect_niveau(type_diplome, nom)
        
        # Détection du domaine (réutilise votre logique)
        domaine = self._detect_domain(nom)
        
        formation = {
            "nom": nom.strip(),
            "etablissement": fields.get('g_ea_lib_vx', '').strip(),
            "ville": fields.get('ville_etab', '').strip(),
            "type_diplome": type_diplome,
            "modalite": fields.get('form_lib_aff', 'Formation initiale'),
            "url": fields.get('lien_form_psup', ''),
            "taux_acces": self._clean_taux(fields.get('taux_acces_ens')),
            "niveau_entree": niveau_entree,
            "niveau_sortie": niveau_sortie,
            "domaine": domaine,
            
            # Champs bonus Parcoursup
            "capacite": fields.get('capa_fin'),
            "selectivite": fields.get('select_form', ''),
            "academie": fields.get('acad_mies', ''),
        }
        
        return formation
    
    def _map_filiere(self, fili: str) -> str:
        """Mapper filière Parcoursup vers type_diplome"""
        mapping = {
            'Licence': 'Licence',
            'BUT': 'BUT',
            'BTS': 'BTS',
            'CPGE': 'CPGE',
            'Master': 'Master',
            'Ecole d\'ingénieurs': 'Ecole',
            'Ecole de commerce': 'Ecole',
            'Formation d\'ingénieur': 'Ecole',
        }
        
        for key, value in mapping.items():
            if key.lower() in fili.lower():
                return value
        
        return 'Autre'
    
    def _detect_niveau(self, type_diplome: str, nom: str) -> tuple:
        """Détecte niveau entrée/sortie"""
        nom_lower = nom.lower()
        
        if type_diplome == 'Licence':
            return (0, 3)
        elif type_diplome == 'Master':
            return (3, 5)
        elif type_diplome == 'BUT':
            return (0, 3)
        elif type_diplome == 'BTS':
            return (0, 2)
        elif type_diplome == 'CPGE':
            return (0, 2)
        elif type_diplome == 'Ecole':
            if 'post-bac' in nom_lower or 'bac+5' in nom_lower:
                return (0, 5)
            return (2, 5)
        
        return (0, 3)  # Default
    
    def _detect_domain(self, nom: str) -> str:
        """Détection améliorée de domaine avec couverture complète"""
        nom_lower = nom.lower()
        
        # LANGUES ET COMMUNICATION (PRIORITÉ 1 - très fréquent)
        if any(kw in nom_lower for kw in ['langue', 'langues', 'anglais', 'espagnol', 
                                            'allemand', 'italien', 'chinois', 'japonais',
                                            'russe', 'arabe', 'lea', 'llcer', 'llce',
                                            'étrangères', 'appliquées', 'traduction',
                                            'interprétation', 'civilisations', 'littératures',
                                            'régionales']):
            return "Langues et Communication"
        
        # COMMUNICATION, MÉDIAS, INFORMATION
        if any(kw in nom_lower for kw in ['communication', 'média', 'journalisme', 
                                            'information', 'publicité', 'journalistique']):
            return "Communication et Médias"
        
        # GÉOGRAPHIE, ENVIRONNEMENT, AMÉNAGEMENT
        if any(kw in nom_lower for kw in ['géographie', 'aménagement', 'urbanisme', 
                                            'territoire', 'environnement', 'géomatique',
                                            'cartographie']):
            return "Géographie et Environnement"
        
        # Informatique & Tech
        if any(kw in nom_lower for kw in ['informatique', 'ia', 'intelligence artificielle',
                                            'data', 'cyber', 'numérique', 'tech', 'réseaux',
                                            'développement', 'logiciel', 'web']):
            return "Informatique et Technologies"
        
        # Droit
        if any(kw in nom_lower for kw in ['droit', 'juridique', 'notarial']):
            return "Droit et Sciences Juridiques"
        
        # Santé
        if any(kw in nom_lower for kw in ['médecine', 'santé', 'infirmier', 'kiné', 'pass',
                                            'orthophonie', 'sage-femme', 'pharmacie', 'dentaire']):
            return "Santé et Médecine"
        
        # Sciences
        if any(kw in nom_lower for kw in ['mathématiques', 'physique', 'chimie', 'biologie']):
            return "Sciences"
        
        # Ingénierie
        if any(kw in nom_lower for kw in ['ingénieur', 'génie', 'mécanique', 'électrique']):
            return "Ingénierie"
        
        # Arts
        if any(kw in nom_lower for kw in ['art', 'design', 'musique', 'cinéma', 'création']):
            return "Arts, Culture et Création"
        
        # Économie & Gestion
        if any(kw in nom_lower for kw in ['économie', 'gestion', 'management', 'commerce']):
            return "Économie et Gestion"
        
        # SHS élargi
        if any(kw in nom_lower for kw in ['psychologie', 'sociologie', 'histoire', 'lettres',
                                            'philosophie', 'anthropologie', 'archéologie']):
            return "Sciences Humaines et Sociales"
        
        # ÉDUCATION ET SOCIAL
        if any(kw in nom_lower for kw in ['éducation', 'enseignement', 'social', 
                                            'travail social', 'animation']):
            return "Éducation et Sciences Sociales"
        
        # Sport
        if any(kw in nom_lower for kw in ['sport', 'staps']):
            return "Sport et STAPS"
        
        return "Autre"
    
    def _clean_taux(self, taux) -> float:
        """Nettoie le taux d'accès"""
        if not taux:
            return None
        try:
            return float(taux)
        except:
            return None


def merge_formations(existing_path: Path, new_formations: List[Dict], output_path: Path):
    """Fusionne les formations existantes avec les nouvelles"""
    
    # Charger existantes
    if existing_path.exists():
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"Formations existantes: {len(existing)}")
    else:
        existing = []
    
    # Déduplication par (nom, ville, etablissement)
    seen = set()
    merged = []
    
    for formation in existing + new_formations:
        key = (
            formation['nom'].lower(),
            formation.get('ville', '').lower(),
            formation.get('etablissement', '').lower()
        )
        
        if key not in seen:
            seen.add(key)
            merged.append(formation)
    
    print(f"Formations après déduplication: {len(merged)}")
    
    # Sauvegarder
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=4, ensure_ascii=False)
    
    print(f"Sauvegardé dans: {output_path}")
    return merged


def main():
    """Script principal"""
    
    # Configuration
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    EXISTING_JSON = BASE_DIR / "data" / "processed" / "formations.json"
    OUTPUT_JSON = BASE_DIR / "data" / "processed" / "formations_enrichies.json"
    
    MAX_FORMATIONS = 9999 
    TYPES_DIPLOMES = ['Licence', 'BUT', 'Master']
    
    print("=" * 80)
    print("ENRICHISSEMENT AVEC API PARCOURSUP")
    print("=" * 80)
    
    # Récupérer depuis Parcoursup
    fetcher = ParcoursupFetcher()
    new_formations = fetcher.fetch_formations(
        max_formations=MAX_FORMATIONS,
        types_diplomes=TYPES_DIPLOMES
    )
    
    if not new_formations:
        print("Aucune formation récupérée. Arrêt.")
        return
    
    # Fusionner avec existantes
    merged = merge_formations(EXISTING_JSON, new_formations, OUTPUT_JSON)
    
    # Statistiques
    print("\n" + "=" * 80)
    print("STATISTIQUES")
    print("=" * 80)
    
    types = {}
    domaines = {}
    for f in merged:
        types[f['type_diplome']] = types.get(f['type_diplome'], 0) + 1
        domaines[f['domaine']] = domaines.get(f['domaine'], 0) + 1
    
    print("\nRépartition par type:")
    for type_dip, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {type_dip}: {count}")
    
    print("\nRépartition par domaine:")
    for domaine, count in sorted(domaines.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {domaine}: {count}")
    
    print(f"\n[OK] Fichier enrichi créé: {OUTPUT_JSON}")
    print("\nProchaine étape:")
    print("  1. Vérifier formations_enrichies.json")
    print("  2. Renommer en formations.json si OK")
    print("  3. Relancer: python data/scripts/ingest.py")


if __name__ == "__main__":
    main()
