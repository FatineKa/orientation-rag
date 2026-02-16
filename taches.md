# 📋 Suivi des Tâches du Projet RAG (Orientation Étudiant)

Ce document liste toutes les étapes restantes pour transformer vos données CSV nettoyées en un Assistant d'Orientation Intelligent.

## ✅ Phase 1 : Préparation & Nettoyage des Données (ETL)
- [x] **Extraction** : Lire les fichiers CSV bruts (`licences.csv`, `master.csv`).
- [x] **Transformation** : Nettoyer les colonnes (Ville, Niveau, Nom).
    - *Script validé : `data/scripts/process_csv.py`* (Robustesse encodage/colonnes corrigée ✅)
- [x] **Validation** : Vérifier que le JSON de sortie respecte le bon format.
    - *Script validé : `data/scripts/validate_data.py`*
    - *Dépendances installées : `pydantic`* (✅ Fixed)

---

## 🚀 Phase 2 : Création de la Base Vectorielle (Embeddings & Indexation)
*Objectif : Rendre les données "recherchables" par le sens (ex: "Je veux faire des maths" → trouve "Licence Mathématiques").*

- [x] **Choisir le modèle d'Embedding** :
    - [x] Modèle Local : `sentence-transformers/all-MiniLM-L6-v2` (Free Search ✅).
- [x] **Script d'Ingestion (`ingest.py`)** :
    - [x] Charger le fichier `formations.json`.
    - [x] Créer les "Documents" LangChain :
        - *Contenu* : Description textuelle riche (Nom + Ville + Mots-clés).
        - *Métadonnées* : `{"ville": "...", "niveau": "..."}` pour le filtrage.
    - [x] Générer les embeddings et sauvegarder l'index FAISS localement (✅ Done).
    
---

## 🔍 Phase 3 : Le Moteur de Recherche (Retriever)
*Objectif : Connecter une question utilisateur aux bonnes formations.*

- [ ] **Retriever de base** :
    - [ ] Charger l'index FAISS existant.
    - [ ] Tester avec une requête simple (ex: "Formation informatique Paris").
- [ ] **Retriever Avancé (Filtres)** :
    - [ ] Extraire les critères de la question (ex: "à Lyon" -> `ville="Lyon"`).
    - [ ] Appliquer ces filtres à la recherche vectorielle (Self-Querying).

---

## 🤖 Phase 4 : Génération de la Réponse (LLM)
*Objectif : L'IA répond à l'étudiant en langage naturel.*

- [ ] **Configuration du LLM** :
    - [ ] Connecter `ChatOpenAI` (GPT-3.5/4) ou un modèle local (Mistral).
- [ ] **Prompt Engineering** :
    - [ ] Créer le template système : *"Tu es un conseiller d'orientation bienveillant..."*
    - [ ] Intégrer les documents retrouvés dans le prompt.
- [ ] **Chaîne RAG (Chain)** :
    - [ ] Assembler : Question -> Retrieval -> Prompt -> LLM -> Réponse.

---

## 💻 Phase 5 : Interface Utilisateur (Bonus)
- [ ] **Script Streamlit (`app.py`)** :
    - [ ] Créer une interface simple (Zone de texte + Bouton "Chercher").
    - [ ] Afficher la réponse de l'IA.
    - [ ] Afficher les sources (liens Parcoursup/MonMaster).
