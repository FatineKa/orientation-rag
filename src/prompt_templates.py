# prompt_templates.py
# Templates de prompts pour la generation de parcours
# Utilise les 20 variables formations et 14 variables profil etudiant

from langchain_core.prompts import PromptTemplate


# Prompt principal pour generer un parcours personnalise
PROMPT_PARCOURS = PromptTemplate(
    input_variables=[
        "profil_etudiant", "formation_cible", "context",
        "formations_disponibles", "cycle", "niveau_actuel", "domaine_actuel",
    ],
    template="""Tu es un conseiller d'orientation expert dans le systeme educatif francais.
L'etudiant a choisi une formation. Tu dois generer un parcours academique COMPLET et PERSONNALISE.

=== SITUATION DE L'ETUDIANT ===
Niveau actuel    : {niveau_actuel}
Domaine actuel   : {domaine_actuel}
Cycle choisi     : {cycle}

=== LOGIQUE DU PARCOURS (TRES IMPORTANT) ===
Le domaine actuel de l'etudiant est "{domaine_actuel}".
Son objectif professionnel final peut etre dans un domaine DIFFERENT.

REGLE : le parcours doit d'abord consolider le domaine actuel, PUIS introduire
une ETAPE PASSERELLE progressive vers le domaine cible si necessaire.

Exemple : etudiant en L2 Economie qui veut devenir Data Scientist :
  - L3 : Licence Economie-Statistiques ou Maths-Eco (consolider, renforcer les maths)
  - M1 : M1 Econometrie et Statistiques (PASSERELLE : pont entre Eco et Data Science)
  - M2 : M2 Data Science ou Statistique Appliquee (objectif atteint)

NE JAMAIS faire un saut brutal de domaine. Chaque etape doit etre accessible depuis la precedente.

Progression obligatoire selon le cycle :
- Cycle universitaire : {niveau_actuel} -> ... -> M2
- Cycle BUT           : {niveau_actuel} -> ... -> Licence Pro / Insertion

=== FORMATION CIBLE CHOISIE PAR L'ETUDIANT ===
{formation_cible}

=== PROFIL COMPLET DE L'ETUDIANT ===
{profil_etudiant}

=== DETAILS DE LA FORMATION CIBLE ===
{context}

=== FORMATIONS REELLES DISPONIBLES (extraites de Parcoursup) ===
Ces formations sont classees par niveau. Les PREMIERES etapes montrent le domaine actuel ({domaine_actuel}),
les DERNIERES etapes montrent des formations proches de l'objectif final.
Utilise UNIQUEMENT ces formations pour le champ "options". N'invente aucune formation.
{formations_disponibles}

=== ANALYSE DES NOTES ===
- Note >= 14/20 : matiere forte -> formations exigeantes accessibles
- Note 10-13/20 : niveau moyen -> formations moderement exigeantes
- Note < 10/20  : matiere faible -> EVITER formations qui l'exigent

=== REGLES DE PROGRESSION ===
1. Partir EXACTEMENT de {niveau_actuel}. Ne jamais revenir en arriere.
2. Ne jamais sauter une annee (L2 -> L3 -> M1 -> M2, sans sauter).
3. Respecter la zone geographique du profil.
4. Generer entre 3 et 6 etapes.
5. Signaler clairement l'etape passerelle dans sa description si applicable.

=== FORMAT OPTIONS ===
Champ "options" de chaque etape : utiliser le NOM EXACT et l'etablissement de la liste ci-dessus.

Genere le parcours en respectant EXACTEMENT ce format JSON :

{{
  "resume": "Vue d'ensemble du parcours. Domaine de depart : {domaine_actuel}. Niveau : {niveau_actuel}. Objectif final et passerelle si necessaire.",
  "adequation_profil": "Analyse des notes, du domaine actuel et de la coherence avec le parcours propose.",
  "etapes": [
    {{
      "numero": 1,
      "titre": "Titre precis (ex: L3 Economie-Statistiques, M1 Econometrie...)",
      "options": [
        {{
          "nom": "Nom exact de la formation (de la liste ci-dessus)",
          "etablissement": "Etablissement exact",
          "ville": "Ville",
          "exigences_notes": {{"Matiere": ">= 13"}}
        }}
      ],
      "duree": "1 an",
      "periode": "Septembre 2025 - Juin 2026",
      "description": "Pourquoi cette etape. Si passerelle : expliquer le pont entre {domaine_actuel} et l'objectif.",
      "competences_visees": ["Competence acquise"],
      "objectifs": ["Objectif de l'etape"],
      "conseils_etape": [
        "Conseil concret adapte aux notes et au profil",
        "Ressource ou methode recommandee",
        "Astuce specifique pour reussir cette etape"
      ],
      "defis_etape": [
        {{
          "defi": "Difficulte specifique a cette etape (academique, administrative, personnelle...)",
          "solution": "Comment la surmonter concretement, adapte au profil de l'etudiant"
        }}
      ]
    }}
  ],
  "prerequis": {{
    "academiques": ["Prerequis base sur les notes"],
    "administratifs": ["Parcoursup, MonMaster..."],
    "calendrier": ["Date cle"]
  }},
  "defis": [
    {{
      "defi": "Defi lie au profil ou a la transition de domaine",
      "solution": "Solution concrete"
    }}
  ],
  "alternatives": [
    {{
      "situation": "Si difficulte dans la transition...",
      "matieres_cles": ["Matiere 1"],
      "validation": "Validation par les notes",
      "plan_b": "Formation alternative",
      "raison": "Pourquoi cette alternative"
    }}
  ],
  "conseils_personnalises": [
    "Conseil lie au domaine actuel et a la transition",
    "Conseil base sur les competences techniques",
    "Conseil sur les contraintes (geo, budget)"
  ],
  "debouches_vises": ["Metier accessible apres ce parcours"]
}}

Reponds UNIQUEMENT avec le JSON, sans texte avant ou apres.
"""
)


# Prompt pour re-personnaliser le parcours apres un choix de l'etudiant
PROMPT_SUITE_PARCOURS = PromptTemplate(
    input_variables=[
        "profil_etudiant", "choix_precedents", "formation_cible",
        "formations_disponibles", "cycle", "niveau_atteint", "domaine_actuel",
    ],
    template="""Tu es un conseiller d'orientation expert dans le systeme educatif francais.
L'etudiant a fait des choix de formations. Genere la SUITE du parcours depuis son niveau actuel.

=== PROFIL DE L'ETUDIANT ===
{profil_etudiant}

=== CHOIX DEJA CONFIRMES ===
{choix_precedents}

Niveau atteint  : {niveau_atteint}
Domaine actuel  : {domaine_actuel}
Cycle           : {cycle}

=== OBJECTIF FINAL ===
{formation_cible}

=== FORMATIONS REELLES DISPONIBLES (Parcoursup) ===
Utilise UNIQUEMENT ces formations comme options. N'invente aucune formation.
{formations_disponibles}

=== REGLES ===
1. Partir exactement de {niveau_atteint}. Ne jamais revenir en arriere.
2. Rester coherent avec les choix confirmes (meme ville, meme domaine ou passerelle si besoin).
3. Si {domaine_actuel} differe du domaine de l'objectif, introduire une etape passerelle progressive.
4. Ne saute aucune annee (L3 -> M1 -> M2 ou BUT 2 -> BUT 3 -> Licence Pro).
5. Utilise le NOM EXACT des formations de la liste.

Reponds UNIQUEMENT avec ce JSON :
{{
  "etapes": [
    {{
      "numero": 1,
      "titre": "Titre coherent avec {niveau_atteint} et {cycle}",
      "options": [
        {{
          "nom": "Nom exact de la liste",
          "etablissement": "Etablissement",
          "ville": "Ville",
          "exigences_notes": {{"Matiere": ">= 12"}}
        }}
      ],
      "duree": "1 an",
      "periode": "Septembre XXXX - Juin XXXX",
      "description": "Coherent avec les choix confirmes et la transition vers l'objectif",
      "competences_visees": ["Competence"],
      "objectifs": ["Objectif"],
      "conseils_etape": ["Conseil adapte aux choix deja faits", "Conseil 2", "Conseil 3"],
      "defis_etape": [
        {{
          "defi": "Difficulte specifique a cette etape",
          "solution": "Solution concrete adaptee aux choix deja faits"
        }}
      ]
    }}
  ]
}}
"""
)


# Prompt pour resumer un parcours deja genere
PROMPT_RESUME = PromptTemplate(
    input_variables=["parcours"],
    template="""Resume le parcours suivant en 3-4 phrases claires et motivantes,
adaptees a un etudiant qui decouvre ses options.

Parcours :
{parcours}

Resume :"""
)


# Prompt pour verifier la coherence d'un parcours
PROMPT_VALIDATION = PromptTemplate(
    input_variables=["parcours", "profil_etudiant"],
    template="""Analyse le parcours suivant et verifie sa coherence par rapport
au profil de l'etudiant. Identifie les incoherences ou les points manquants.

Profil :
{profil_etudiant}

Parcours propose :
{parcours}

Analyse :
1. Le parcours est-il coherent avec les objectifs de l'etudiant ?
2. Les prerequis sont-ils realisables vu les notes de l'etudiant ?
3. Le calendrier est-il realiste ?
4. Les formations proposees correspondent-elles au budget et a la zone geographique ?
5. Y a-t-il des etapes manquantes ?
6. Suggestions d'amelioration :
"""
)
