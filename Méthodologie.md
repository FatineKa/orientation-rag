# Plan Détaillé — Génération de Parcours Personnalisé (RAG)

## 1. Rappel du Contexte

Ta partie du projet consiste à développer le module de **génération de parcours personnalisé**. Ce module :
- Reçoit le **profil de l'étudiant** (intérêts, niveau, objectif professionnel, etc.)
- Récupère des **données pertinentes** sur les formations via un système **RAG** (Retrieval-Augmented Generation)
- Génère un **parcours détaillé et personnalisé** : étapes chronologiques, prérequis, défis, alternatives

Le premier module (recommandation de formations) est déjà réalisé par ton collègue. Ton module se branche dessus : une fois qu'une formation est choisie (ou qu'un objectif est défini), tu génères le parcours.

---

## 2. Architecture Globale

```
Profil étudiant ──► Embedding du profil ──► Recherche vectorielle (RAG)
                                                    │
                                    Documents pertinents récupérés
                                                    │
                                          ┌─────────▼──────────┐
                                          │   Prompt enrichi    │
                                          │  (profil + docs)    │
                                          └─────────┬──────────┘
                                                    │
                                              API LLM (ex: GPT)
                                                    │
                                          Parcours personnalisé
```

### Deux cas d'utilisation :
1. **Étudiant en exploration** → il choisit une formation parmi les recommandations → ton module génère le parcours
2. **Étudiant avec objectif défini** → ton module génère directement le parcours complet

---

## 3. Les Étapes à Suivre

### Étape 1 : Collecte et Préparation des Données

C'est la **fondation** du RAG. Sans bonnes données, le système ne peut pas générer des parcours fiables.

#### Quelles données collecter ?

| Type de données | Description | Sources possibles |
|---|---|---|
| **Fiches formations** | Nom, durée, niveau requis, débouchés, contenu, établissement | Sites des universités, Parcoursup, Onisep, MonMaster |
| **Prérequis académiques** | Diplômes nécessaires, notes minimales, matières obligatoires | Règlements des formations, sites officiels |
| **Prérequis administratifs** | Dossiers à fournir, dates limites, procédures de candidature | Sites des établissements, Parcoursup |
| **Parcours types** | Enchaînements de formations classiques (Licence → Master → ...) | Enquêtes d'insertion, annuaires alumni |
| **Métiers et débouchés** | Fiches métiers, compétences requises, salaires moyens | Onisep, Pôle Emploi, APEC, LinkedIn |
| **Témoignages / retours** | Avis d'anciens étudiants, difficultés rencontrées | Forums, enquêtes |
| **Calendrier académique** | Dates de rentrée, périodes de candidature, examens | Sites officiels |

#### Format des données

Chaque document doit être structuré de manière cohérente. Exemple de fiche formation en JSON :

```json
{
  "id": "master-ia-paris-saclay",
  "nom": "Master Intelligence Artificielle",
  "etablissement": "Université Paris-Saclay",
  "niveau_entree": "Licence Informatique ou équivalent",
  "duree": "2 ans",
  "prerequis_academiques": [
    "Licence en Informatique, Mathématiques ou équivalent",
    "Bases solides en programmation Python",
    "Connaissances en statistiques et algèbre linéaire"
  ],
  "prerequis_administratifs": [
    "Dossier de candidature via MonMaster",
    "Lettre de motivation",
    "CV académique",
    "Relevés de notes L1-L3"
  ],
  "dates_cles": {
    "ouverture_candidatures": "Mars",
    "cloture_candidatures": "Mai",
    "resultats": "Juin",
    "rentree": "Septembre"
  },
  "competences_acquises": ["Machine Learning", "Deep Learning", "NLP", "Vision par ordinateur"],
  "debouches": ["Data Scientist", "Ingénieur ML", "Chercheur en IA"],
  "defis_courants": [
    "Forte sélectivité (taux d'acceptation ~15%)",
    "Charge de travail élevée",
    "Stage obligatoire à trouver"
  ],
  "alternatives": [
    "Master Data Science - Université de Lyon",
    "Master MIAGE - Université Paris Dauphine"
  ]
}
```

#### Comment collecter les données ?

- **Web scraping** (si autorisé) : avec `BeautifulSoup` ou `Scrapy` sur les sites universitaires
- **APIs publiques** : API Parcoursup, API Onisep (si disponibles)
- **Collecte manuelle** : pour les données de qualité, créer un jeu de données de référence
- **Fichiers CSV/JSON** : organiser les données dans des fichiers structurés

> **Conseil** : Commence par un jeu de données réduit (10-20 formations bien documentées) pour tester le pipeline, puis étends progressivement.

---

### Étape 2 : Mise en Place de la Base Vectorielle (Vector Store)

Le RAG nécessite de stocker les documents sous forme de **vecteurs** (embeddings) pour pouvoir les rechercher efficacement.

#### Technologies recommandées :

| Outil | Rôle | Pourquoi ? |
|---|---|---|
| **ChromaDB** ou **FAISS** | Base de données vectorielle | Gratuit, simple, fonctionne en local |
| **LangChain** | Framework RAG | Simplifie toute la chaîne RAG (chunking, embedding, retrieval, generation) |
| **Sentence-Transformers** ou **OpenAI Embeddings** | Modèle d'embedding | Transforme le texte en vecteurs numériques |

#### Processus :

```
Documents (JSON/texte) 
    → Découpage en chunks (morceaux de texte)
    → Calcul des embeddings pour chaque chunk
    → Stockage dans la base vectorielle (ChromaDB)
```

#### Code simplifié (exemple avec LangChain + ChromaDB) :

```python
from langchain.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# 1. Charger les documents
loader = JSONLoader("data/formations.json", jq_schema=".[]")
documents = loader.load()

# 2. Découper en chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# 3. Créer les embeddings et stocker
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")
```

---

### Étape 3 : Configuration de l'API LLM

Le LLM (Large Language Model) sera utilisé pour **générer** le parcours personnalisé à partir du contexte récupéré.

#### Options d'API :

| Option | Avantages | Inconvénients |
|---|---|---|
| **OpenAI API (GPT-4o)** | Très performant, facile à utiliser | Payant (~$0.01/requête) |
| **Mistral AI API** | Modèle français, bon rapport qualité/prix | Moins de communauté |
| **Ollama (local)** | Gratuit, pas de dépendance réseau | Nécessite un GPU, moins performant |
| **Groq API** | Très rapide, gratuit (tier limité) | Limites de requêtes |

> **Recommandation** : Commence avec **OpenAI API** (GPT-4o-mini, très bon marché) ou **Groq** (gratuit) pour le développement. Passe à un modèle local (Ollama) pour la production si nécessaire.

#### Configuration basique :

```python
from langchain.chat_models import ChatOpenAI

# Option 1 : OpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key="ta-clé-api")

# Option 2 : Ollama (local)
from langchain.llms import Ollama
llm = Ollama(model="mistral")
```

---

### Étape 4 : Construction du Pipeline RAG

C'est le cœur du système : assembler la recherche vectorielle et la génération.

#### Le flux complet :

```
1. L'étudiant fournit son profil + formation choisie (ou objectif)
2. Le système construit une requête de recherche
3. La base vectorielle retourne les documents les plus pertinents
4. Un prompt structuré est construit avec le profil + les documents
5. Le LLM génère le parcours personnalisé
```

#### Le Prompt (crucial !) :

```python
PROMPT_TEMPLATE = """
Tu es un conseiller d'orientation expert dans le système éducatif français.
À partir du profil de l'étudiant et des informations sur les formations,
génère un parcours personnalisé détaillé.

=== PROFIL DE L'ÉTUDIANT ===
{profil_etudiant}

=== INFORMATIONS SUR LES FORMATIONS (récupérées via RAG) ===
{documents_rag}

=== PARCOURS À GÉNÉRER ===
Génère un parcours complet et structuré contenant :

1. **Résumé du parcours** : Vue d'ensemble en 2-3 phrases
2. **Étapes chronologiques** : Liste ordonnée de chaque étape avec :
   - Formation/action à suivre
   - Durée estimée
   - Période (ex: "Septembre 2026 - Juin 2027")
3. **Prérequis à valider** :
   - Académiques (diplômes, matières, notes)
   - Administratifs (dossiers, dates limites)
4. **Défis prévisibles** : Difficultés courantes et comment s'y préparer
5. **Alternatives** : Plans B en cas d'obstacle à chaque étape
6. **Conseils personnalisés** : Basés sur le profil spécifique de l'étudiant

Sois précis, concret et bienveillant dans tes recommandations.
"""
```

#### Assemblage avec LangChain :

```python
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Créer le retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Créer la chaîne RAG
prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["profil_etudiant", "documents_rag"]
)

rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt}
)
```

---

### Étape 5 : Développement de l'Interface (API Backend)

Tu as besoin d'une API pour exposer ton module.

#### Technologies :

| Outil | Rôle |
|---|---|
| **FastAPI** | Framework API Python (léger, rapide, documentation auto) |
| **Pydantic** | Validation des données d'entrée/sortie |
| **Uvicorn** | Serveur ASGI pour exécuter FastAPI |

#### Exemple d'endpoint :

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="API Orientation - Génération de Parcours")

class ProfilEtudiant(BaseModel):
    nom: str
    niveau_actuel: str          # ex: "Licence 3 Informatique"
    objectif: str               # ex: "Devenir Data Scientist"
    matieres_fortes: list[str]  # ex: ["Maths", "Programmation"]
    matieres_faibles: list[str]
    contraintes: str            # ex: "Rester en Île-de-France"

class ParcoursResponse(BaseModel):
    resume: str
    etapes: list[dict]
    prerequis: dict
    defis: list[str]
    alternatives: list[dict]
    conseils: list[str]

@app.post("/generer-parcours", response_model=ParcoursResponse)
async def generer_parcours(profil: ProfilEtudiant):
    # 1. Construire la requête de recherche
    query = f"{profil.objectif} {profil.niveau_actuel} {' '.join(profil.matieres_fortes)}"
    
    # 2. Récupérer les documents pertinents via RAG
    docs = retriever.get_relevant_documents(query)
    
    # 3. Générer le parcours avec le LLM
    result = rag_chain.run(
        profil_etudiant=profil.dict(),
        documents_rag=docs
    )
    
    # 4. Parser et retourner le résultat structuré
    return parse_parcours(result)
```

---

### Étape 6 : Tests et Validation

| Test | Description |
|---|---|
| **Test unitaire** | Vérifier que chaque composant fonctionne isolément (embedding, retrieval, generation) |
| **Test d'intégration** | Vérifier le pipeline complet de bout en bout |
| **Test de qualité** | Évaluer la pertinence des parcours générés (manuellement + métriques) |
| **Test de performance** | Mesurer le temps de réponse du système |

#### Métriques d'évaluation :
- **Pertinence** : Les documents récupérés sont-ils utiles ?
- **Complétude** : Le parcours couvre-t-il toutes les étapes ?
- **Précision** : Les informations sont-elles correctes ?
- **Personnalisation** : Le parcours est-il adapté au profil ?

---

### Étape 7 : Intégration avec le Module de Recommandation

Connecter ton module avec celui de ton collègue :

```
Module Recommandation (collègue)
    │
    │  L'étudiant choisit une formation
    │  ou arrive avec un objectif défini
    │
    ▼
Module Génération de Parcours (toi)
    │
    │  Parcours personnalisé complet
    │
    ▼
Interface utilisateur (si applicable)
```

---

## 4. Stack Technologique Complète

| Catégorie | Technologie | Usage |
|---|---|---|
| **Langage** | Python 3.10+ | Langage principal |
| **Framework RAG** | LangChain | Orchestration du pipeline RAG |
| **Base vectorielle** | ChromaDB (ou FAISS) | Stockage et recherche des embeddings |
| **Embeddings** | Sentence-Transformers / OpenAI | Vectorisation des textes |
| **LLM** | GPT-4o-mini / Mistral / Ollama | Génération des parcours |
| **API Backend** | FastAPI + Uvicorn | Exposer le service |
| **Validation** | Pydantic | Validation des entrées/sorties |
| **Tests** | pytest | Tests automatisés |
| **Gestion dépendances** | pip + requirements.txt | Reproductibilité |
| **Versioning** | Git + GitHub | Collaboration |

---

## 5. Planning Suggéré

| Semaine | Tâche |
|---|---|
| **Semaine 1** | Collecte et structuration des données (fiches formations, prérequis) |
| **Semaine 2** | Mise en place de la base vectorielle (ChromaDB + embeddings) |
| **Semaine 3** | Configuration de l'API LLM + construction du prompt |
| **Semaine 4** | Assemblage du pipeline RAG complet |
| **Semaine 5** | Développement de l'API FastAPI |
| **Semaine 6** | Tests, validation et optimisation |
| **Semaine 7** | Intégration avec le module de recommandation |
| **Semaine 8** | Documentation et préparation de la présentation |

---

## 6. Dépendances Python (requirements.txt)

```txt
langchain>=0.1.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
openai>=1.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pytest>=7.0.0
```

---

## 7. Structure du Projet Proposée

```
TER/
├── data/
│   ├── formations.json          # Données des formations
│   ├── metiers.json             # Fiches métiers
│   └── parcours_types.json      # Parcours types
├── src/
│   ├── __init__.py
│   ├── data_loader.py           # Chargement et préparation des données
│   ├── vectorstore.py           # Gestion de la base vectorielle
│   ├── rag_pipeline.py          # Pipeline RAG complet
│   ├── prompt_templates.py      # Templates de prompts
│   └── api.py                   # Endpoints FastAPI
├── tests/
│   ├── test_data_loader.py
│   ├── test_vectorstore.py
│   └── test_rag_pipeline.py
├── chroma_db/                   # Base vectorielle persistée
├── .env                         # Clés API (ne pas commit !)
├── requirements.txt
├── Méthodologie.md              # Ce fichier
└── README.md
```
