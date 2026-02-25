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
    # Liste des objectifs professionnels par domaine
    OBJECTIFS_PAR_DOMAINE = {
        "Data Science / IA": [
            "Data Scientist", "Data Analyst", "Data Engineer",
            "Ingenieur Machine Learning", "Ingenieur IA",
            "Chercheur en IA", "Analyste Business Intelligence",
        ],
        "Informatique / Dev": [
            "Developpeur Web", "Developpeur Mobile", "Developpeur Full Stack",
            "Ingenieur Logiciel", "DevOps Engineer", "Architecte Logiciel",
            "Administrateur Systemes et Reseaux", "Ingenieur Cybersecurite",
            "Chef de Projet IT", "Testeur / QA Engineer",
        ],
        "Economie": [
            "Economiste", "Analyste Financier", "Charge d'etudes economiques",
            "Conseiller en politique economique", "Statisticien economiste",
        ],
        "Gestion / Comptabilite": [
            "Comptable", "Expert-Comptable", "Controleur de gestion",
            "Auditeur financier", "Directeur Administratif et Financier",
            "Gestionnaire de patrimoine", "Tresorier",
        ],
        "Droit": [
            "Avocat", "Juriste d'entreprise", "Notaire", "Magistrat",
            "Huissier de justice", "Juriste en droit public",
            "Juriste en droit social", "Mediateur juridique",
        ],
        "Sciences Politiques": [
            "Diplomate", "Charge de mission en collectivite",
            "Analyste en relations internationales", "Journaliste politique",
            "Conseiller politique", "Charge de communication politique",
            "Fonctionnaire international",
        ],
        "Sante / Medecine": [
            "Medecin generaliste", "Medecin specialiste", "Chirurgien",
            "Pharmacien", "Dentiste", "Sage-femme", "Kinesitherapeute",
            "Infirmier", "Orthophoniste", "Psychomotricien",
            "Manipulateur en radiologie", "Opticien",
        ],
        "Lettres / Langues": [
            "Enseignant de lettres", "Traducteur", "Interprete",
            "Redacteur / Correcteur", "Editeur", "Bibliothecaire",
            "Professeur de langues", "Linguiste",
        ],
        "Commerce / Marketing": [
            "Chef de produit", "Responsable Marketing", "Commercial",
            "Responsable e-commerce", "Chef de publicite",
            "Directeur Commercial", "Charge de communication",
            "Community Manager", "Responsable CRM",
        ],
        "Sciences / Ingenierie": [
            "Ingenieur en genie civil", "Ingenieur en mecanique",
            "Ingenieur en electronique", "Ingenieur en energie",
            "Chercheur en physique", "Chercheur en chimie",
            "Ingenieur en materiaux", "Technicien de laboratoire",
        ],
        "Arts / Design": [
            "Graphiste", "Designer UX/UI", "Directeur Artistique",
            "Illustrateur", "Architecte d'interieur", "Animateur 3D",
            "Photographe", "Webdesigner",
        ],
        "Communication / Media": [
            "Journaliste", "Attache de presse", "Charge de communication",
            "Responsable editorial", "Redacteur web",
            "Responsable relations publiques", "Planneur strategique",
        ],
        "Psychologie / Sciences Sociales": [
            "Psychologue clinicien", "Psychologue du travail",
            "Sociologue", "Conseiller d'orientation",
            "Charge d'etudes sociologiques", "Mediateur social",
        ],
        "Sciences de l'Education": [
            "Professeur des ecoles", "Conseiller pedagogique",
            "Formateur pour adultes", "Ingenieur pedagogique",
            "Educateur specialise", "Responsable de formation",
        ],
        "Environnement / Geographie": [
            "Ingenieur environnement", "Charge de mission developpement durable",
            "Ecologue", "Urbaniste", "Cartographe / Geomaticien",
            "Climatologue", "Gestionnaire d'espaces naturels",
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
        "Data Science / IA": ["Algebre", "Analyse", "Statistiques", "Probabilites", "Programmation"],
        "Informatique / Dev": ["Algorithmique", "Programmation", "Bases de donnees", "Algebre", "Analyse"],
        "Economie": ["Microeconomie", "Macroeconomie", "Statistiques", "Mathematiques appliquees", "Anglais"],
        "Gestion / Comptabilite": ["Comptabilite generale", "Controle de gestion", "Finance", "Droit des affaires", "Economie"],
        "Droit": ["Droit civil", "Droit constitutionnel", "Histoire du droit", "Introduction au droit", "Methodologie juridique"],
        "Sciences Politiques": ["Science politique", "Relations internationales", "Sociologie politique", "Histoire contemporaine", "Anglais"],
        "Sante / Medecine": ["Biologie cellulaire", "Chimie organique", "Physique", "Anatomie", "Biochimie"],
        "Lettres / Langues": ["Litterature francaise", "Anglais", "Langue vivante 2", "Linguistique", "Civilisation"],
        "Commerce / Marketing": ["Marketing", "Economie", "Anglais commercial", "Communication", "Gestion"],
        "Sciences / Ingenierie": ["Algebre", "Analyse", "Physique", "Chimie", "Informatique"],
        "Arts / Design": ["Pratique artistique", "Culture artistique", "Histoire de l'art", "Projet creatif", "Anglais"],
        "Communication / Media": ["Theories de la communication", "Ecriture journalistique", "Sociologie des medias", "Anglais", "Culture generale"],
        "Psychologie / Sciences Sociales": ["Psychologie generale", "Sociologie", "Statistiques", "Methodologie", "Anglais"],
        "Sciences de l'Education": ["Sciences de l'education", "Psychologie du developpement", "Sociologie", "Didactique", "Anglais"],
        "Environnement / Geographie": ["Geographie physique", "Ecologie", "Geomatique", "Climatologie", "Anglais"],
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
                st.markdown(f"""
<div class="step-card">
    <strong>Etape {indicateur} — {etape.get('titre', '')}</strong>
    <br><small>Duree : {etape.get('duree', '?')} &nbsp;|&nbsp; {etape.get('periode', '')}</small>
</div>
                """, unsafe_allow_html=True)

                if etape.get("description"):
                    st.markdown(etape["description"])

                # --- Cas 1 : choix deja fait pour cette etape ---
                if choix_fait:
                    st.success(
                        f"✅ Formation choisie : **{choix_fait['choix']}**"
                        + (f" — {choix_fait.get('etablissement', '')}" if choix_fait.get('etablissement') else "")
                        + (f", {choix_fait.get('ville', '')}" if choix_fait.get('ville') else "")
                    )

                # --- Cas 2 : options disponibles a choisir ---
                elif etape.get("options"):
                    options     = etape.get("options", [])
                    ville_rech  = etape.get("ville_recherche", "")

                    # Titre de la section
                    nb = len(options)
                    geo_info = f" — formations près de <strong>{ville_rech}</strong>" if ville_rech else ""
                    st.markdown(
                        f"<div class='section-options-title'>"
                        f"📚 Formations disponibles — {nb} formation{'s' if nb > 1 else ''}{geo_info} :"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    for j, opt in enumerate(options):
                        details_type = f" &nbsp;&bull;&nbsp; {opt.get('type_diplome', '')}" if opt.get('type_diplome') else ""
                        description  = opt.get("description", "")
                        desc_html    = f"<br><small style='color:#555;font-style:italic;'>{description}</small>" if description else ""
                        col_opt, col_choix = st.columns([4, 1])
                        with col_opt:
                            st.markdown(f"""
<div class="base-card">
    <span class="badge-base">Parcoursup</span>
    <strong>&nbsp;{opt.get('nom', '')}</strong>{details_type}
    <br><small>Etablissement : {opt.get('etablissement', '?')} &nbsp;|&nbsp; Ville : {opt.get('ville', '?')}</small>
    {desc_html}
</div>
                            """, unsafe_allow_html=True)
                        with col_choix:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Choisir", key=f"choix_e{num}_{j}", use_container_width=True):
                                st.session_state["choix_etapes"][str(num)] = {
                                    "etape": num,
                                    "choix": opt.get("nom", ""),
                                    "etablissement": opt.get("etablissement", ""),
                                    "ville": opt.get("ville", ""),
                                }
                                for k in list(st.session_state["choix_etapes"].keys()):
                                    if int(k) > num:
                                        del st.session_state["choix_etapes"][k]
                                pipeline = charger_pipeline()
                                choix_liste = sorted(
                                    st.session_state["choix_etapes"].values(),
                                    key=lambda x: x["etape"]
                                )
                                with st.spinner("Adaptation du parcours..."):
                                    try:
                                        suite = pipeline.generer_suite_parcours(
                                            profil, choix_liste,
                                            formation_choisie.get("nom", "")
                                        )
                                        if suite.get("etapes"):
                                            for i_new, e_new in enumerate(suite["etapes"]):
                                                e_new["numero"] = num + 1 + i_new
                                            parcours["etapes"] = etapes[:idx + 1] + suite["etapes"]
                                            st.session_state["parcours"] = parcours
                                    except Exception as e:
                                        st.error(f"Erreur : {str(e)}")
                                st.rerun()

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

    # Alternatives
    if parcours.get("alternatives"):
        st.markdown("### Plans alternatifs")
        for a in parcours["alternatives"]:
            lignes = []
            if a.get("matieres_cles"):
                matieres = ", ".join(a["matieres_cles"]) if isinstance(a["matieres_cles"], list) else a["matieres_cles"]
                lignes.append(f"<br><strong>Matieres cles :</strong> {matieres}")
            if a.get("validation"):
                lignes.append(f"<br><strong>Validation :</strong> {a['validation']}")
            if a.get("raison"):
                lignes.append(f"<br><em>{a['raison']}</em>")
            details = "".join(lignes)
            st.markdown(f"""
<div class="alt-card">
    <strong>{a.get('situation', '')}</strong>
    <br>-> {a.get('plan_b', '')}{details}
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

