import json
from pathlib import Path

class ProfilEtudiant:
    """Gère le chargement et l'accès au profil étudiant."""
    
    def __init__(self, profil_path=None):
        if profil_path is None:
            # Chemin par défaut
            base_dir = Path(__file__).resolve().parent.parent.parent
            profil_path = base_dir / "data" / "profiles" / "profil_exemple.json"
        
        self.profil_path = Path(profil_path)
        self.profil = self.load_profil()
    
    def load_profil(self):
        """Charge le profil depuis le fichier JSON."""
        if not self.profil_path.exists():
            raise FileNotFoundError(f"Profil introuvable : {self.profil_path}")
        
        with open(self.profil_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('profil_etudiant', {})
    
    def get_niveau_actuel(self):
        """Retourne le niveau académique actuel."""
        return self.profil.get('academique', {}).get('niveau_actuel', '')
    
    def get_niveau_sortie_souhaite(self):
        """Détermine le niveau de sortie souhaité basé sur le profil."""
        niveau = self.get_niveau_actuel().lower()
        
        # L3 -> cherche Master (niveau 5)
        if 'l3' in niveau or 'licence 3' in niveau:
            return 5
        # L1/L2 -> cherche Licence (niveau 3)
        elif 'l1' in niveau or 'l2' in niveau or 'licence' in niveau:
            return 3
        # Master 1 -> cherche Master 2 (niveau 5)
        elif 'm1' in niveau or 'master 1' in niveau:
            return 5
        # Bac -> cherche Licence (niveau 3)
        elif 'bac' in niveau or 'terminale' in niveau:
            return 3
        
        return 5  # Par défaut: Master
    
    def get_contraintes_geo(self):
        """Retourne les contraintes géographiques."""
        contraintes = self.profil.get('contraintes', {}).get('contraintes_geographiques', '')
        # Normalise en lowercase pour matching
        return contraintes.lower().strip()
    
    def get_domaines_prioritaires(self):
        """Retourne les domaines d'études préférés."""
        return self.profil.get('objectifs', {}).get('domaines_etudes_preferes', [])
    
    def get_objectif_pro(self):
        """Retourne l'objectif professionnel."""
        return self.profil.get('objectifs', {}).get('objectif_professionnel', '')
    
    def get_type_formation(self):
        """Retourne le type de formation préféré."""
        return self.profil.get('objectifs', {}).get('type_formation_prefere', '')
    
    def generer_requete_enrichie(self, requete_base=""):
        """
        Enrichit une requête avec le contexte du profil.
        Cette requête sera envoyée à ChromaDB pour la recherche sémantique.
        """
        objectif = self.get_objectif_pro()
        domaines = self.get_domaines_prioritaires()
        
        # Construction de la requête enrichie
        if requete_base:
            requete = requete_base
        else:
            requete = f"Je veux {objectif}"
        
        # Ajoute les domaines préférés
        if domaines:
            requete += f". Domaines d'intérêt : {', '.join(domaines)}"
        
        return requete
    
    def get_filtres_stricts(self):
        """
        Retourne les filtres stricts à appliquer (contraintes obligatoires).
        Ces filtres seront utilisés pour filtrer les résultats de ChromaDB.
        """
        filtres = {}
        
        # Contrainte géographique
        geo = self.get_contraintes_geo()
        if geo and geo != "partout" and geo != "france":
            # Extrait la ville principale (ex: "Paris ou Île-de-France" -> "paris")
            if 'paris' in geo or 'île-de-france' in geo or 'idf' in geo:
                filtres['zone'] = 'paris'  # On gérera ça dans le filtrage
            else:
                # Extrait le premier mot (souvent la ville)
                ville = geo.split()[0]
                filtres['ville_keyword'] = ville
        
        return filtres
    
    def __str__(self):
        """Représentation textuelle du profil."""
        return f"""
Profil Étudiant
---------------
Niveau: {self.get_niveau_actuel()}
Objectif: {self.get_objectif_pro()}
Domaines: {', '.join(self.get_domaines_prioritaires())}
Localisation: {self.get_contraintes_geo()}
Type formation: {self.get_type_formation()}
        """.strip()


if __name__ == "__main__":
    # Test du chargement
    profil = ProfilEtudiant()
    print(profil)
    print("\nRequête enrichie:")
    print(profil.generer_requete_enrichie())
    print("\nFiltres stricts:")
    print(profil.get_filtres_stricts())
