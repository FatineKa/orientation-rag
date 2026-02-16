# Variables Essentielles — Module Génération de Parcours (RAG)

> **Document de référence** pour l'alignement entre le module de recommandation et le module de génération de parcours.
> Dernière mise à jour : 11/02/2026

---

## Objectif du module

> **Point de départ** (profil actuel de l'étudiant) → **Point d'arrivée** (objectif professionnel)
>
> Le rôle du RAG est de **déterminer les étapes pertinentes entre les deux**, en s'appuyant sur les données des formations et le profil de l'étudiant.

---

## 1. Variables du Profil Étudiant (14 variables)

Ces variables sont collectées auprès de l'étudiant et servent d'entrée au système RAG pour générer un parcours personnalisé.

### Bloc Académique (4 variables)

| # | Variable | Type | Exemple | Description |
|---|---|---|---|---|
| 1 | `niveau_actuel` | `str` | "Étudiant en L3 Informatique" / "Salarié Bac+3 en reconversion" | Niveau académique + situation actuelle |
| 2 | `matieres_fortes` | `list[str]` | ["Maths", "Programmation"] | Matières où l'étudiant excelle |
| 3 | `matieres_faibles` | `list[str]` | ["Physique", "Anglais"] | Matières à renforcer |
| 4 | `notes_par_matiere` | `dict` | {"Maths": 15, "Info": 14, "Anglais": 11} | Notes pour évaluer l'admissibilité |

### Bloc Compétences (4 variables)

| # | Variable | Type | Exemple | Description |
|---|---|---|---|---|
| 5 | `competences_techniques` | `list[str]` | ["Python", "SQL", "Git"] | Compétences techniques acquises |
| 6 | `qualites_personnelles` | `list[str]` | ["Travail en équipe", "Autonome", "Rigoureux"] | Soft skills — enrichissent les conseils du LLM |
| 7 | `langues` | `list[dict]` | [{"langue": "Anglais", "niveau": "B2"}] | Niveau de langue (certaines formations exigent B2/C1) |
| 8 | `experiences_stages` | `list[str]` | ["Stage dev web 2 mois", "Projet perso app mobile"] | Expériences professionnelles et projets |

### Bloc Objectif & Préférences (4 variables)

| # | Variable | Type | Exemple | Description |
|---|---|---|---|---|
| 9 | `objectif_professionnel` | `str` | "Devenir Data Scientist" | Métier ou domaine visé — **guide tout le parcours** |
| 10 | `domaines_etudes_preferes` | `list[str]` | ["Économie", "Finance"] | Domaines d'études souhaités — **oriente le chemin** (ex: Data Scientist via Économie ≠ via Informatique) |
| 11 | `centres_interet` | `list[str]` | ["Intelligence Artificielle", "Environnement"] | Intérêts personnels — personnalise les recommandations |
| 12 | `type_formation_prefere` | `str` | "Alternance" / "Initial" / "À distance" | Modalité de formation souhaitée |

### Bloc Contraintes (2 variables)

| # | Variable | Type | Exemple | Description |
|---|---|---|---|---|
| 13 | `contraintes_geographiques` | `str` | "Lyon" / "Île-de-France uniquement" | Zone géographique acceptable (ville/région préférée) |
| 14 | `budget` | `str` | "Public uniquement" / "Jusqu'à 5000€/an" | Capacité financière |

### Exemple JSON complet d'un profil étudiant :

```json
{
  "niveau_actuel": "Étudiant en Licence 3 Informatique à l'Université Lyon 1",
  "matieres_fortes": ["Mathématiques", "Programmation", "Statistiques"],
  "matieres_faibles": ["Physique", "Communication orale"],
  "notes_par_matiere": {
    "Mathématiques": 15,
    "Algorithmique": 14,
    "Bases de données": 13,
    "Anglais": 12
  },
  "competences_techniques": ["Python", "SQL", "Git", "Pandas"],
  "qualites_personnelles": ["Rigoureux", "Curieux", "Travail en équipe"],
  "langues": [
    {"langue": "Anglais", "niveau": "B2"},
    {"langue": "Espagnol", "niveau": "A2"}
  ],
  "experiences_stages": [
    "Stage développeur Python - 2 mois - Startup Lyon",
    "Projet universitaire : analyse de données COVID"
  ],
  "objectif_professionnel": "Devenir Data Scientist",
  "domaines_etudes_preferes": ["Économie", "Finance"],
  "centres_interet": ["Intelligence Artificielle", "Trading", "Sport"],
  "type_formation_prefere": "Alternance",
  "contraintes_geographiques": "Lyon ou Paris",
  "budget": "Public uniquement ou alternance"
}
```

---

## 2. Variables des Formations (20 variables)

Ces variables décrivent chaque formation dans la base de données. Elles sont indexées dans le vector store pour la recherche RAG.

### Identification (4 variables)

| # | Variable | Type | Exemple |
|---|---|---|---|
| 1 | `nom` | `str` | "Master Intelligence Artificielle" |
| 2 | `etablissement` | `str` | "Université Paris-Saclay" |
| 3 | `ville` | `str` | "Gif-sur-Yvette" |
| 4 | `type_etablissement` | `str` | "Public" / "Privé" / "Consulaire" |

### Caractéristiques (4 variables)

| # | Variable | Type | Exemple |
|---|---|---|---|
| 5 | `niveau_diplome` | `str` | "Master" / "Licence" / "BUT" / "BTS" |
| 6 | `duree` | `str` | "2 ans" |
| 7 | `modalite` | `str` | "Présentiel" / "Alternance" / "À distance" / "Hybride" |
| 8 | `langue_enseignement` | `str` | "Français" / "Anglais" / "Bilingue" |

### Admission (4 variables)

| # | Variable | Type | Exemple |
|---|---|---|---|
| 9 | `niveau_entree` | `str` | "Bac+3" / "Bac" / "Bac+5" |
| 10 | `prerequis_academiques` | `list[str]` | ["Algèbre linéaire", "Python", "Statistiques"] |
| 11 | `selectivite` | `str` | "Très sélectif (~15%)" / "Sélectif" / "Accessible" |
| 12 | `frais_scolarite` | `float` | 243.0 / 8500.0 (en €/an) |

### Administratif (3 variables)

| # | Variable | Type | Exemple |
|---|---|---|---|
| 13 | `plateforme_candidature` | `str` | "MonMaster" / "Parcoursup" / "Dossier direct" |
| 14 | `documents_requis` | `list[str]` | ["CV", "Lettre de motivation", "Relevés de notes L1-L3"] |
| 15 | `dates_candidature` | `dict` | {"ouverture": "Mars", "cloture": "Mai", "rentree": "Septembre"} |

### Débouchés (2 variables)

| # | Variable | Type | Exemple |
|---|---|---|---|
| 16 | `competences_acquises` | `list[str]` | ["Machine Learning", "Deep Learning", "NLP"] |
| 17 | `debouches_metiers` | `list[str]` | ["Data Scientist", "ML Engineer", "Chercheur IA"] |

### Contexte RAG (3 variables)

| # | Variable | Type | Exemple |
|---|---|---|---|
| 18 | `defis_courants` | `list[str]` | ["Forte sélectivité", "Stage difficile à trouver"] |
| 19 | `conseils_candidature` | `list[str]` | ["Avoir un projet perso en ML", "Lettre ciblée"] |
| 20 | `alternatives` | `list[str]` | ["Master Data Science Lyon", "Master MIAGE Dauphine"] |

### Exemple JSON complet d'une formation :

```json
{
  "nom": "Master Intelligence Artificielle",
  "etablissement": "Université Paris-Saclay",
  "ville": "Gif-sur-Yvette",
  "type_etablissement": "Public",

  "niveau_diplome": "Master",
  "duree": "2 ans",
  "modalite": "Présentiel",
  "langue_enseignement": "Français et Anglais",

  "niveau_entree": "Bac+3",
  "prerequis_academiques": [
    "Licence en Informatique ou Mathématiques",
    "Programmation Python",
    "Statistiques et algèbre linéaire"
  ],
  "selectivite": "Très sélectif (~15% d'acceptation)",
  "frais_scolarite": 243.0,

  "plateforme_candidature": "MonMaster",
  "documents_requis": [
    "CV académique",
    "Lettre de motivation",
    "Relevés de notes L1 à L3",
    "Attestation de niveau d'anglais (B2 minimum)"
  ],
  "dates_candidature": {
    "ouverture": "Mars",
    "cloture": "Mai",
    "resultats": "Juin",
    "rentree": "Septembre"
  },

  "competences_acquises": ["Machine Learning", "Deep Learning", "NLP", "Vision par ordinateur"],
  "debouches_metiers": ["Data Scientist", "Ingénieur ML", "Chercheur en IA"],

  "defis_courants": [
    "Forte sélectivité",
    "Charge de travail très élevée",
    "Stage obligatoire de 5 mois à trouver"
  ],
  "conseils_candidature": [
    "Avoir un projet personnel en ML/IA sur GitHub",
    "Lettre de motivation très ciblée sur la recherche",
    "Bonne moyenne en maths (>13)"
  ],
  "alternatives": [
    "Master Data Science - Université de Lyon",
    "Master MIAGE - Université Paris Dauphine",
    "MSc AI - CentraleSupélec"
  ]
}
```

---

## 3. Mapping Étudiant ↔ Formation

Ce tableau montre comment chaque variable étudiant est utilisée pour matcher avec les formations :

| Variable Étudiant | → | Variable Formation | Logique de matching |
|---|---|---|---|
| `niveau_actuel` | → | `niveau_entree` | L'étudiant a-t-il le niveau requis ? |
| `objectif_professionnel` | → | `debouches_metiers` | La formation mène-t-elle au métier visé ? |
| `domaines_etudes_preferes` | → | `niveau_diplome` + `nom` | Oriente le chemin (Data Scientist via Éco ≠ via Info) |
| `matieres_fortes` / `faibles` | → | `prerequis_academiques` | L'étudiant a-t-il les bases ? Lacunes à combler ? |
| `notes_par_matiere` | → | `selectivite` | Le dossier est-il assez fort ? |
| `competences_techniques` | → | `competences_acquises` | Que va-t-il apprendre de nouveau ? |
| `qualites_personnelles` | → | `conseils_candidature` | Enrichit les conseils personnalisés |
| `centres_interet` | → | `debouches_metiers` | Affine les recommandations de spécialisation |
| `langues` | → | `langue_enseignement` | Peut-il suivre les cours ? |
| `experiences_stages` | → | `conseils_candidature` | Son profil est-il compétitif ? |
| `type_formation_prefere` | → | `modalite` | Alternance, initial ou à distance ? |
| `contraintes_geographiques` | → | `ville` | La formation est-elle dans sa zone ? |
| `budget` | → | `frais_scolarite` | C'est dans son budget ? |

---

## 4. Note pour l'intégration

> **À destination du module de recommandation** : Si ta base de données utilise des noms de champs différents, il suffit de créer un mapping (dictionnaire de correspondance) entre tes champs et ceux listés ici. L'important est que les **mêmes informations** soient présentes, pas que les noms soient identiques.
>
> Les variables marquées comme essentielles doivent être présentes dans la base de données pour que le RAG fonctionne correctement. Les deux modules doivent partager le même schéma de données pour les formations.
