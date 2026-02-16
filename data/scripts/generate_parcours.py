import json
from pathlib import Path
from profil_manager import ProfilEtudiant
from retrieve import load_index, detect_filters

class ParcoursProgramme:
    """Génère un parcours d'études personnalisé basé sur le profil étudiant."""
    
    def __init__(self, profil: ProfilEtudiant, vectorstore):
        self.profil = profil
        self.vectorstore = vectorstore
    
    def determiner_etapes_parcours(self):
        """
        Détermine les étapes du parcours selon le niveau actuel.
        Retourne une liste d'étapes avec leurs caractéristiques.
        """
        niveau_actuel_str = self.profil.get_niveau_actuel().lower()
        etapes = []
        
        # Analyse du niveau actuel
        if 'bac' in niveau_actuel_str or 'terminale' in niveau_actuel_str:
            # Parcours complet: Bac -> Licence -> Master
            etapes = [
                {
                    'nom': 'Licence (Bac+3)',
                    'niveau_sortie': 3,
                    'type_diplome': 'Licence',
                    'description': 'Formation de base dans votre domaine'
                },
                {
                    'nom': 'Master (Bac+5)',
                    'niveau_sortie': 5,
                    'type_diplome': 'Master',
                    'description': 'Spécialisation pour atteindre votre objectif professionnel'
                }
            ]
        elif 'l1' in niveau_actuel_str or 'l2' in niveau_actuel_str:
            # Licence en cours -> continuer puis Master
            etapes = [
                {
                    'nom': 'Fin de Licence (Bac+3)',
                    'niveau_sortie': 3,
                    'type_diplome': 'Licence',
                    'description': 'Compléter votre licence actuelle ou réorientation'
                },
                {
                    'nom': 'Master (Bac+5)',
                    'niveau_sortie': 5,
                    'type_diplome': 'Master',
                    'description': 'Spécialisation dans votre domaine cible'
                }
            ]
        elif 'l3' in niveau_actuel_str or 'licence 3' in niveau_actuel_str:
            # L3 -> directement Master
            etapes = [
                {
                    'nom': 'Master (Bac+5)',
                    'niveau_sortie': 5,
                    'type_diplome': 'Master',
                    'description': 'Spécialisation pour votre objectif professionnel'
                }
            ]
        elif 'm1' in niveau_actuel_str or 'master 1' in niveau_actuel_str:
            # M1 -> Master 2
            etapes = [
                {
                    'nom': 'Master 2 (Bac+5)',
                    'niveau_sortie': 5,
                    'type_diplome': 'Master',
                    'description': 'Finaliser votre Master'
                }
            ]
        else:
            # Par défaut: Master
            etapes = [
                {
                    'nom': 'Master (Bac+5)',
                    'niveau_sortie': 5,
                    'type_diplome': 'Master',
                    'description': 'Formation avancée'
                }
            ]
        
        return etapes
    
    def rechercher_formations_pour_etape(self, etape, k=5):
        """
        Recherche les formations adaptées pour une étape du parcours.
        """
        # Construction de la requête enrichie
        requete_base = self.profil.generer_requete_enrichie()
        
        # Recherche sémantique
        results = self.vectorstore.similarity_search_with_score(requete_base, k=k*10)
        
        # Filtrage selon l'étape et le profil
        filtered_results = []
        geo_constraint = self.profil.get_contraintes_geo()
        
        for doc, score in results:
            # Filtre par type de diplôme
            doc_type = doc.metadata.get('type_diplome', '').lower()
            if etape['type_diplome'].lower() not in doc_type:
                continue
            
            # Filtre géographique
            if geo_constraint:
                ville = doc.metadata.get('ville', '').lower()
                if 'paris' in geo_constraint or 'île-de-france' in geo_constraint:
                    # Accepte Paris et sa région
                    if not ('paris' in ville or 'cergy' in ville or 'versailles' in ville 
                            or 'nanterre' in ville or 'créteil' in ville or 'orsay' in ville
                            or 'evry' in ville or 'bobigny' in ville):
                        continue
                else:
                    # Vérifie si la ville correspond
                    ville_cible = geo_constraint.split()[0]  # Premier mot
                    if ville_cible not in ville:
                        continue
            
            filtered_results.append((doc, score))
        
        # Prend les k meilleurs
        return filtered_results[:k]
    
    def generer_parcours_complet(self):
        """
        Génère un parcours complet avec toutes les étapes.
        """
        print("=" * 80)
        print("GÉNÉRATION DE PARCOURS PERSONNALISÉ")
        print("=" * 80)
        print(f"\nProfil: {self.profil.get_niveau_actuel()}")
        print(f"Objectif: {self.profil.get_objectif_pro()}")
        print(f"Localisation: {self.profil.get_contraintes_geo()}")
        print("-" * 80)
        
        etapes = self.determiner_etapes_parcours()
        parcours = []
        
        for i, etape in enumerate(etapes, 1):
            print(f"\n{'=' * 80}")
            print(f"ÉTAPE {i}: {etape['nom']}")
            print(f"Description: {etape['description']}")
            print(f"{'=' * 80}\n")
            
            formations = self.rechercher_formations_pour_etape(etape, k=5)
            
            if not formations:
                print("[!] Aucune formation trouvee pour cette etape.")
                continue
            
            print(f"Top {len(formations)} formations recommandées:\n")
            
            etape_formations = []
            for j, (doc, score) in enumerate(formations, 1):
                formation_info = {
                    'rang': j,
                    'score': score,
                    'nom': doc.page_content.split('.')[0].replace('Formation: ', ''),
                    'ville': doc.metadata.get('ville', 'Non spécifié'),
                    'etablissement': doc.metadata.get('etablissement', 'Non spécifié'),
                    'url': doc.metadata.get('url', '')
                }
                
                print(f"  {j}. [Score: {score:.3f}] {formation_info['nom']}")
                print(f"     Lieu: {formation_info['ville']}")
                print(f"     Etablissement: {formation_info['etablissement']}")
                if formation_info['url']:
                    print(f"     URL: {formation_info['url']}")
                print()
                
                etape_formations.append(formation_info)
            
            parcours.append({
                'etape': etape,
                'formations': etape_formations
            })
        
        print("=" * 80)
        print("FIN DU PARCOURS")
        print("=" * 80)
        
        return parcours


def main():
    """Test du générateur de parcours."""
    # 1. Charger le profil
    print("Chargement du profil étudiant...")
    profil = ProfilEtudiant()
    
    # 2. Charger l'index ChromaDB
    print("Chargement de l'index vectoriel...")
    vectorstore = load_index()
    if not vectorstore:
        print("Erreur: impossible de charger l'index.")
        return
    
    # 3. Générer le parcours
    generateur = ParcoursProgramme(profil, vectorstore)
    parcours = generateur.generer_parcours_complet()
    
    # 4. Optionnel: sauvegarder le parcours en JSON
    output_path = Path(__file__).parent.parent / "output" / "parcours_genere.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parcours, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Parcours sauvegarde dans: {output_path}")


if __name__ == "__main__":
    main()
