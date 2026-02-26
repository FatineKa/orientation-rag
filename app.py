# app.py
# Interface Streamlit pour le systeme d'orientation RAG
# Lance avec : streamlit run app.py

import sys
import os
import json
import streamlit as st

# Ajouter le dossier du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.rag_pipeline import PipelineRAG


# Configuration de la page
st.set_page_config(
    page_title="Systeme d'Orientation Intelligent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #4a6fa5 0%, #6b4f8a 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #ddd; margin: 0.3rem 0 0 0; }
    .step-card {
        background: #f5f7ff;
        border-left: 3px solid #4a6fa5;
        padding: 1rem;
        border-radius: 0 6px 6px 0;
        margin: 0.5rem 0;
        color: #1a1a2e;
    }
    .defi-card {
        background: #fffaf0;
        border-left: 3px solid #d97706;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        margin: 0.4rem 0;
        color: #1a1a2e;
    }
    .alt-card {
        background: #f0fdf4;
        border-left: 3px solid #16a34a;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        margin: 0.4rem 0;
        color: #1a1a2e;
    }
    .stat-box {
        background: white;
        padding: 0.8rem;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .stat-box h3 { margin: 0; font-size: 1.5rem; color: #4a6fa5; }
    .stat-box p { margin: 0; color: #666; font-size: 0.8rem; }
    .change-indicator {
        background: #e0f2fe;
        border: 1px solid #7dd3fc;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin-bottom: 1rem;
        color: #0369a1;
        font-size: 0.85rem;
    }
    .base-card {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        margin: 0.4rem 0;
        color: #1a1a2e;
    }
    .badge-ia {
        display: inline-block;
        background: #e9d5ff;
        color: #6b21a8;
        padding: 1px 7px;
        border-radius: 9999px;
        font-size: 0.68rem;
        font-weight: bold;
        margin-bottom: 4px;
    }
    .badge-base {
        display: inline-block;
        background: #dbeafe;
        color: #1d4ed8;
        padding: 1px 7px;
        border-radius: 9999px;
        font-size: 0.68rem;
        font-weight: bold;
        margin-bottom: 4px;
    }
    .formation-choisie-banner {
        background: linear-gradient(135deg, #4a6fa5 0%, #6b4f8a 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .formation-choisie-banner h3 { color: white; margin: 0 0 0.3rem 0; font-size: 1.1rem; }
    .formation-choisie-banner p { color: #e0d5f5; margin: 0; font-size: 0.85rem; }
    .objectif-banner {
        background: #f0fdf4;
        border: 1px solid #86efac;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        color: #14532d;
        font-size: 0.85rem;
    }
    .section-options-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #374151;
        margin: 0.5rem 0 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Chargement du pipeline (mis en cache)
@st.cache_resource(show_spinner="Chargement du pipeline RAG...")
def charger_pipeline():
    pipeline = PipelineRAG()
    pipeline.initialiser(rebuild=False)
    return pipeline


# En-tete
st.markdown("""
<div class="main-header">
    <h1>Systeme d'Orientation Intelligent</h1>
    <p>Generation de parcours academiques personnalises avec RAG + GPT-4o-mini</p>
</div>
""", unsafe_allow_html=True)


# --- Barre laterale - Formulaire du profil etudiant ---
with st.sidebar:
    st.header("Profil Etudiant")
    st.caption("Modifie ton profil, le parcours se met a jour automatiquement")

    st.subheader("Academique")
    niveau_actuel = st.selectbox(
        "Niveau actuel",
        ["Terminale Generale", "Terminale Technologique", "Terminale Professionnelle",
         "L1", "L2", "L3", "M1", "M2", "BTS", "BUT / DUT", "Prepa"],
    )
    # Liste des objectifs professionnels par domaine — extraite des débouchés réels de la base Parcoursup
    OBJECTIFS_PAR_DOMAINE = {
        "Arts, Culture et Création": [
            "Conservateur de musée", "Critique d'art", "Guide conférencier",
            "Réalisateur", "Artiste plasticien", "Designer",
            "Critique de cinéma", "Metteur en scène", "Directeur artistique",
            "Monteur vidéo", "Musicologue", "Historien de l'art",
            "Chargé de projet culturel", "Médiateur culturel", "Graphiste",
        ],
        "Communication et Médias": [
            "Chargé de communication", "Community manager", "Journaliste",
            "Webdesigner", "Designer graphique", "Attaché de presse",
            "Webmaster", "Chargé de communication digitale",
            "Consultant en communication", "Développeur web",
            "Bibliothécaire", "Rédacteur web", "Documentaliste",
        ],
        "Droit et Sciences Juridiques": [
            "Avocat", "Notaire", "Juriste d'entreprise", "Juriste",
            "Conseiller juridique", "Assistant juridique", "Magistrat",
            "Fonctionnaire", "Politologue", "Juriste en droit européen",
            "Juriste en propriété intellectuelle", "Responsable juridique",
        ],
        "Économie et Gestion": [
            "Gestionnaire de projet", "Consultant en gestion", "Économiste",
            "Responsable marketing", "Entrepreneur", "Consultant en management",
            "Analyste financier", "Assistant de direction",
            "Responsable logistique", "Contrôleur de gestion",
            "Responsable administratif", "Chef de projet",
            "Expert-comptable", "Responsable e-commerce",
        ],
        "Éducation et Sciences Sociales": [
            "Formateur", "Enseignant", "Conseiller pédagogique",
            "Éducateur spécialisé", "Professeur des écoles", "Éducateur",
            "Animateur socioculturel", "Coordinateur pédagogique",
            "Conseiller d'orientation", "Conseiller en insertion professionnelle",
        ],
        "Géographie et Environnement": [
            "Urbaniste", "Géographe", "Chargé d'études environnementales",
            "Consultant en environnement", "Chargé de mission environnement",
            "Technicien en environnement", "Consultant en développement durable",
            "Conseiller en aménagement", "Écologue", "Biologiste",
            "Chargé de mission en aménagement", "Paysagiste",
        ],
        "Informatique et Technologies": [
            "Développeur", "Ingénieur en informatique", "Data analyst",
            "Développeur web", "Responsable qualité", "Chef de produit",
            "Technicien de laboratoire", "Administrateur systèmes",
            "Ingénieur télécommunications", "Consultant en cybersécurité",
            "Data scientist", "Chef de projet informatique",
            "Consultant en systèmes d'information", "Développeur logiciel",
        ],
        "Ingénierie": [
            "Ingénieur en mécanique", "Responsable qualité",
            "Technicien de production", "Responsable de production",
            "Technicien de maintenance", "Chef de projet",
            "Ingénieur civil", "Conducteur de travaux",
            "Ingénieur en génie civil", "Consultant en ingénierie",
            "Ingénieur en électronique", "Ingénieur en systèmes",
        ],
        "Langues et Communication": [
            "Traducteur", "Chargé de communication", "Professeur de langues",
            "Interprète", "Enseignant de langues", "Responsable export",
            "Diplomate", "Chargé de relations internationales",
            "Éditeur", "Journaliste", "Chercheur en linguistique",
            "Chargé de communication internationale",
        ],
        "Santé et Médecine": [
            "Médecin", "Pharmacien", "Infirmier", "Chercheur en santé",
            "Technicien de laboratoire", "Consultant en santé",
            "Kinésithérapeute", "Chercheur en biologie",
            "Orthoptiste", "Ergothérapeute", "Gestionnaire de santé",
        ],
        "Sciences": [
            "Technicien de laboratoire", "Chercheur", "Ingénieur",
            "Ingénieur chimiste", "Analyste de données",
            "Chercheur en physique", "Professeur de mathématiques",
            "Statisticien", "Chercheur en chimie", "Chimiste",
            "Chercheur en biologie", "Chercheur en mathématiques",
            "Ingénieur en chimie", "Économiste",
        ],
        "Sciences Humaines et Sociales": [
            "Éditeur", "Historien", "Professeur de lettres", "Journaliste",
            "Archiviste", "Enseignant", "Psychologue",
            "Professeur d'histoire", "Philosophe", "Chargé d'études",
            "Sociologue", "Écrivain", "Conseiller d'orientation",
            "Consultant en ressources humaines",
        ],
    }

    # Construire la liste plate triee
    tous_objectifs = []
    for domaine, objectifs in OBJECTIFS_PAR_DOMAINE.items():
        for obj in objectifs:
            tous_objectifs.append(obj)
    tous_objectifs.sort()
    tous_objectifs.append("Autre (preciser)")

    objectif = st.selectbox(
        "Objectif professionnel",
        tous_objectifs,
    )

    # Si "Autre", afficher un champ texte
    if objectif == "Autre (preciser)":
        objectif = st.text_input(
            "Preciser l'objectif",
            placeholder="Ex: Devenir oceanographe...",
        )
    st.subheader("Competences")
    competences = st.text_input(
        "Competences techniques",
        value="Python, SQL",
    )
    qualites = st.text_input(
        "Qualites personnelles",
        value="Rigoureux, Curieux",
    )
    experiences = st.text_input(
        "Experiences / Stages",
        value="Stage dev web 2 mois",
    )

    st.subheader("Preferences")

    # Detecter si lycee ou universite
    est_lyceen = niveau_actuel.startswith("Terminale")

    # Matieres lycee (programme commun + specialites)
    MATIERES_LYCEE = ["Maths", "Physique-Chimie", "SVT", "SES", "NSI",
                      "Francais", "Philosophie", "Anglais", "Histoire-Geo",
                      "Litterature", "Arts"]

    # Matieres universite par domaine (noms reels des UE)
    DOMAINES_MATIERES_UNIV = {
        "Arts, Culture et Création": ["Pratique artistique", "Culture artistique", "Histoire de l'art", "Projet creatif", "Anglais"],
        "Communication et Médias": ["Theories de la communication", "Ecriture journalistique", "Sociologie des medias", "Anglais", "Culture generale"],
        "Droit et Sciences Juridiques": ["Droit civil", "Droit constitutionnel", "Histoire du droit", "Introduction au droit", "Methodologie juridique"],
        "Économie et Gestion": ["Microeconomie", "Macroeconomie", "Comptabilite", "Finance", "Statistiques"],
        "Éducation et Sciences Sociales": ["Sciences de l'education", "Psychologie du developpement", "Sociologie", "Didactique", "Anglais"],
        "Géographie et Environnement": ["Geographie physique", "Ecologie", "Geomatique", "Climatologie", "Anglais"],
        "Informatique et Technologies": ["Algorithmique", "Programmation", "Bases de donnees", "Algebre", "Analyse"],
        "Ingénierie": ["Algebre", "Analyse", "Physique", "Chimie", "Informatique"],
        "Langues et Communication": ["Litterature francaise", "Anglais", "Langue vivante 2", "Linguistique", "Civilisation"],
        "Santé et Médecine": ["Biologie cellulaire", "Chimie organique", "Physique", "Anatomie", "Biochimie"],
        "Sciences": ["Algebre", "Analyse", "Physique", "Chimie", "Statistiques"],
        "Sciences Humaines et Sociales": ["Psychologie generale", "Sociologie", "Histoire", "Philosophie", "Anglais"],
    }

    if est_lyceen:
        # Lyceen : pas besoin de choisir un domaine, les matieres sont standard
        domaine_choisi = st.text_input(
            "Domaine d'etudes vise",
            value="Data Science / IA",
            placeholder="Ex: Medecine, Informatique, Droit...",
        )
        matieres_domaine = MATIERES_LYCEE
    else:
        # Etudiant universitaire : domaine specifique
        domaine_choisi = st.selectbox(
            "Domaine d'etudes actuel",
            list(DOMAINES_MATIERES_UNIV.keys()),
        )
        matieres_domaine = DOMAINES_MATIERES_UNIV[domaine_choisi]

    centres_interet = st.text_input(
        "Centres d'interet",
        value="Machine Learning, Environnement",
    )
    type_formation = st.selectbox(
        "Type de formation",
        ["Formation initiale", "Alternance", "A distance"],
    )

    st.subheader("Contraintes")
    geo = st.text_input(
        "Contraintes geographiques",
        value="Paris ou Lyon",
    )
    budget = st.selectbox(
        "Budget",
        ["Public uniquement", "Public ou prive", "Peu importe"],
    )

    # Notes par matiere (adaptees au niveau)
    if est_lyceen:
        st.subheader("Notes par matiere")
        st.caption("Matieres du lycee - entre tes notes actuelles")
        st.caption("Laisse 0 pour les matieres que tu ne suis pas")
    else:
        st.subheader("Notes par matiere")
        st.caption(f"Matieres de ta filiere : {domaine_choisi}")

    notes = {}
    col1, col2 = st.columns(2)
    for i, matiere in enumerate(matieres_domaine):
        with col1 if i % 2 == 0 else col2:
            defaut = 12 if not est_lyceen else 0
            notes[matiere] = st.number_input(f"{matiere}", 0, 20, defaut, key=f"note_{matiere}")


# --- Construction du profil a partir du formulaire ---
profil = {
    "niveau_actuel": niveau_actuel,
    "objectif_professionnel": objectif,
    "notes_par_matiere": notes,
    "competences_techniques": [c.strip() for c in competences.split(",") if c.strip()],
    "qualites_personnelles": [q.strip() for q in qualites.split(",") if q.strip()],
    "langues": [{"langue": "Francais", "niveau": "C2"}],
    "experiences_stages": [e.strip() for e in experiences.split(",") if e.strip()],
    "domaines_etudes_preferes": [domaine_choisi],
    "centres_interet": [c.strip() for c in centres_interet.split(",") if c.strip()],
    "type_formation_prefere": type_formation,
    "contraintes_geographiques": geo,
    "budget": budget,
}


# --- Session state ---
if "formations_recommandees" not in st.session_state:
    st.session_state["formations_recommandees"] = None
if "info_geo" not in st.session_state:
    st.session_state["info_geo"] = None
if "formation_choisie" not in st.session_state:
    st.session_state["formation_choisie"] = None
if "parcours" not in st.session_state:
    st.session_state["parcours"] = None
if "choix_etapes" not in st.session_state:
    st.session_state["choix_etapes"] = {}


# --- PHASE 1 : Explorer les formations ---
st.markdown("---")

if st.button("Explorer les formations", type="primary", use_container_width=True):
    # Reinitialiser les etats
    st.session_state["formation_choisie"] = None
    st.session_state["parcours"] = None
    st.session_state["choix_etapes"] = {}

    pipeline = charger_pipeline()
    top_k = int(os.getenv("TOP_K_DOCUMENTS", "8"))

    with st.spinner("Recherche des formations adaptees a ton profil..."):
        try:
            formations, info_geo = pipeline.recommander_formations(profil, top_k=top_k)
            st.session_state["formations_recommandees"] = formations
            st.session_state["info_geo"] = info_geo
        except Exception as e:
            st.error(f"Erreur lors de la recherche : {str(e)}")
            st.session_state["formations_recommandees"] = None


# --- Affichage des formations recommandees ---
formations = st.session_state.get("formations_recommandees")
info_geo = st.session_state.get("info_geo")

if formations and not st.session_state.get("parcours"):
    # Info geographique
    if info_geo and info_geo.get("type") == "proximite":
        villes_dem = ", ".join(info_geo.get("ville_demandee", []))
        villes_pr = ", ".join(info_geo.get("villes_proches", []))
        st.info(
            f"Aucune formation trouvee a **{villes_dem}**. "
            f"Formations proposees dans les villes proches : **{villes_pr}**"
        )
    elif info_geo and info_geo.get("type") == "aucune":
        villes_dem = ", ".join(info_geo.get("villes", []))
        st.warning(
            f"Aucune formation trouvee a **{villes_dem}** ni dans les villes proches. "
            f"Formations basees sur la pertinence academique."
        )

    st.markdown(f"### {len(formations)} formations recommandees pour ton profil")
    st.caption(
        f"Formations selectionnees dans notre base de {3354} formations Parcoursup "
        f"en fonction de ton profil, ton objectif ({profil.get('objectif_professionnel', '')}) "
        f"et ta zone ({profil.get('contraintes_geographiques', 'France')}). "
        "**Choisis une formation pour generer ton parcours complet vers ton objectif de carriere.**"
    )

    for i, f in enumerate(formations):
        with st.container():
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(f"""
<div class="step-card">
    <strong>{f.get('nom', 'Formation')}</strong>
    <br><em>{f.get('type', '')} &nbsp;&bull;&nbsp; {f.get('domaine', '')}</em>
    <br><small>Etablissement : {f.get('etablissement', '?')} &nbsp;|&nbsp; Ville : {f.get('ville', '?')} &nbsp;|&nbsp; Duree : {f.get('duree', '?')}</small>
</div>
                """, unsafe_allow_html=True)
                if f.get("extrait"):
                    with st.expander("Voir les details"):
                        st.markdown(f["extrait"])
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Choisir →", key=f"choisir_{i}", use_container_width=True):
                    st.session_state["formation_choisie"] = f
                    pipeline = charger_pipeline()
                    with st.spinner(f"Generation du parcours complet vers '{f['nom']}' (+ recherche formations reelles par etape)..."):
                        try:
                            st.session_state["parcours"] = pipeline.generer_parcours(profil, f)
                        except Exception as e:
                            st.error(f"Erreur : {str(e)}")
                            st.session_state["parcours"] = None
                    st.rerun()


# --- PHASE 2 : Affichage du parcours ---
parcours = st.session_state.get("parcours")
formation_choisie = st.session_state.get("formation_choisie")

if parcours and formation_choisie:
    # Bouton retour
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Changer de formation", use_container_width=True):
            st.session_state["parcours"] = None
            st.session_state["formation_choisie"] = None
            st.session_state["choix_etapes"] = {}
            st.rerun()

    # Banniere formation choisie + objectif
    fc = formation_choisie
    st.markdown(f"""
<div class="formation-choisie-banner">
    <h3>Formation choisie : {fc.get('nom', '')}</h3>
    <p>{fc.get('type', '')} &bull; {fc.get('etablissement', '')} &bull; {fc.get('ville', '')} &bull; {fc.get('duree', '')}</p>
</div>
<div class="objectif-banner">
    Objectif : <strong>{profil.get('objectif_professionnel', '')}</strong>
    &nbsp;|&nbsp; Niveau actuel : <strong>{profil.get('niveau_actuel', '')}</strong>
    &nbsp;|&nbsp; Domaine : <strong>{profil.get('domaines_etudes_preferes', [''])[0]}</strong>
    &nbsp;|&nbsp; Zone : <strong>{profil.get('contraintes_geographiques', 'France')}</strong>
</div>
    """, unsafe_allow_html=True)

    # Resume
    if parcours.get("resume"):
        st.info(parcours["resume"])

    # Adequation profil
    if parcours.get("adequation_profil"):
        with st.expander("Analyse de ton profil par rapport a cette formation"):
            st.markdown(parcours["adequation_profil"])

    # Etapes du parcours
    if parcours.get("etapes"):
        etapes = parcours["etapes"]
        nb_etapes = len(etapes)
        choix = st.session_state.get("choix_etapes", {})

        st.markdown(f"### Ton parcours — {nb_etapes} etapes")
        st.caption("A chaque etape, choisis la formation qui te correspond pour adapter la suite du parcours")

        for idx, etape in enumerate(etapes):
            num = etape.get("numero", idx + 1)
            choix_fait = choix.get(str(num))

            # Indicateur de progression
            if choix_fait:
                indicateur = "✅"
            else:
                indicateur = f"**{num}**"

            with st.container():
                # Formation réelle recommandée pour cette étape (1ère de la liste)
                options = etape.get("options", [])
                formation_recommandee = options[0] if options else None

                if formation_recommandee:
                    nom_f   = formation_recommandee.get("nom", etape.get("titre", ""))
                    type_f  = formation_recommandee.get("type_diplome", "")
                    etab_f  = formation_recommandee.get("etablissement", "")
                    ville_f = formation_recommandee.get("ville", "")
                    desc_f  = formation_recommandee.get("description", "")
                    type_badge = f"<span style='background:#e8f4fd;color:#1a73e8;padding:2px 8px;border-radius:10px;font-size:0.75em;font-weight:600;'>{type_f}</span>&nbsp;" if type_f else ""
                    etab_html  = f"<br><small>🏛️ <strong>{etab_f}</strong> &nbsp;|&nbsp; 📍 {ville_f}</small>" if etab_f else ""
                    desc_html  = f"<br><small style='color:#555;font-style:italic;'>{desc_f}</small>" if desc_f else ""
                    st.markdown(f"""
<div class="step-card">
    <small>Etape {num} &nbsp;|&nbsp; {etape.get('duree', '')} &nbsp;|&nbsp; {etape.get('periode', '')}</small>
    <br>{type_badge}<strong>{nom_f}</strong>
    {etab_html}{desc_html}
</div>
                    """, unsafe_allow_html=True)
                    # Autres formations disponibles dans un expander
                    if len(options) > 1:
                        with st.expander(f"Voir {len(options)-1} autre(s) formation(s) disponible(s)"):
                            for opt in options[1:]:
                                type_o = opt.get("type_diplome", "")
                                st.markdown(
                                    f"- **{opt.get('nom','')}** — {type_o} &nbsp;|&nbsp; "
                                    f"🏛️ {opt.get('etablissement','?')} &nbsp;|&nbsp; 📍 {opt.get('ville','?')}"
                                )
                else:
                    st.markdown(f"""
<div class="step-card">
    <strong>Etape {indicateur} — {etape.get('titre', '')}</strong>
    <br><small>Duree : {etape.get('duree', '?')} &nbsp;|&nbsp; {etape.get('periode', '')}</small>
</div>
                    """, unsafe_allow_html=True)

                if etape.get("description"):
                    st.markdown(etape["description"])

                elif etape.get("formation_ou_action"):
                    # Fallback ancien format
                    st.markdown(f"**Formation** : {etape['formation_ou_action']}")

                # Competences et objectifs
                col1, col2 = st.columns(2)
                with col1:
                    if etape.get("competences_visees"):
                        st.markdown("**Competences visees**")
                        for c in etape["competences_visees"]:
                            st.markdown(f"- {c}")
                with col2:
                    if etape.get("objectifs"):
                        st.markdown("**Objectifs**")
                        for o in etape["objectifs"]:
                            st.markdown(f"- {o}")

                if etape.get("conseils_etape"):
                    st.success("**Conseils pour reussir cette etape :**")
                    for conseil in etape["conseils_etape"]:
                        st.markdown(f"- {conseil}")

                if etape.get("defis_etape"):
                    st.warning("**Defis a anticiper :**")
                    for d in etape["defis_etape"]:
                        if isinstance(d, dict):
                            st.markdown(f"- **{d.get('defi', '')}** — {d.get('solution', '')}")
                        else:
                            st.markdown(f"- {d}")

                st.divider()

    # Prerequis globaux
    if parcours.get("prerequis"):
        st.markdown("### Prerequis et demarches")
        prereqs = parcours["prerequis"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Academiques**")
            for p in prereqs.get("academiques", []):
                st.markdown(f"- {p}")
        with col2:
            st.markdown("**Administratifs**")
            for p in prereqs.get("administratifs", []):
                st.markdown(f"- {p}")
        with col3:
            st.markdown("**Calendrier**")
            for p in prereqs.get("calendrier", []):
                st.markdown(f"- {p}")

    # Defis
    if parcours.get("defis"):
        st.markdown("### Defis a anticiper")
        for d in parcours["defis"]:
            st.markdown(f"""
<div class="defi-card">
    <strong>Defi :</strong> {d.get('defi', '')}
    <br><strong>Solution :</strong> {d.get('solution', '')}
</div>
            """, unsafe_allow_html=True)


    # Conseils
    if parcours.get("conseils_personnalises"):
        st.markdown("### Conseils personnalises")
        for c in parcours["conseils_personnalises"]:
            st.markdown(f"- {c}")

    # Debouches
    if parcours.get("debouches_vises"):
        st.markdown("### Debouches vises")
        nb = len(parcours["debouches_vises"])
        cols = st.columns(min(nb, 4))
        for i, deb in enumerate(parcours["debouches_vises"]):
            with cols[i % len(cols)]:
                st.markdown(f"""
<div class="stat-box">
    <h3>-</h3>
    <p>{deb}</p>
</div>
                """, unsafe_allow_html=True)

    # JSON brut
    with st.expander("Voir le JSON brut"):
        st.json(parcours)


# --- Page d'accueil (aucune recherche lancee) ---
if not formations and not parcours:
    st.markdown("### Trouve les formations qui te correspondent")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
<div class="stat-box">
    <h3>3354</h3>
    <p>Formations indexees</p>
</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="stat-box">
    <h3>20</h3>
    <p>Variables par formation</p>
</div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
<div class="stat-box">
    <h3>14</h3>
    <p>Variables profil etudiant</p>
</div>
        """, unsafe_allow_html=True)

    st.markdown("""
    ---
    **Comment ca marche ?**

    **1. Remplis ton profil** dans la barre laterale (niveau, objectif, notes, contraintes geographiques...)

    **2. Explore les formations** — le systeme cherche dans 3354 formations Parcoursup celles qui correspondent le mieux a ton profil

    **3. Choisis une formation** qui t'interesse comme point de depart

    **4. Genere ton parcours complet** — le modele planifie toutes les etapes de ton niveau actuel jusqu'a ton objectif de carriere, avec a chaque etape :
    - Les formations suggérees par l'IA (logique de progression)
    - Les formations disponibles dans la vraie base Parcoursup
    - Des conseils personnalises selon tes notes et forces

    **5. Personnalise etape par etape** — choisis ta formation a chaque etape pour adapter la suite du parcours
    """)

