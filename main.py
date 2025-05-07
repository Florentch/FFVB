import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
from utils import load_data, SKILL_TABS, unique_preserve_order
from skill import skill_comparison_tab
from player_evolution import player_evolution_tab
from player import Player
from stat_global import global_stats_tab

# Configuration de la page
st.set_page_config(
    page_title="Analyse de Volleyball", 
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 0%;
        max-width: 25%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Analyse de Volleyball")
st.markdown("""
    Application d'analyse des données de volleyball extraites des fichiers dvw de la saison 24-25 de l'équipe France Avenir """)

with st.spinner("Chargement des données..."):
    players, players_df = load_data()

# Sidebar général
with st.sidebar:
    st.subheader("Informations générales")
    if players:
        st.write(f"📊 **{len(players)}** joueurs au total")
        match_count = len(players[0].df['match_id'].unique()) if players[0].df is not None else 0
        st.write(f"🏐 **{match_count}** matchs analysés")
    else:
        st.warning("Aucune donnée disponible.")


# Menu latéral avec catégories
with st.sidebar:
    st.markdown("---")
    st.subheader("Navigation")
    
    # Variable pour stocker la sélection active
    if 'active_section' not in st.session_state:
        st.session_state.active_section = "Actions"
        st.session_state.active_item = list(SKILL_TABS.keys())[0] if SKILL_TABS else None
    
    # Catégorie Actions (Skills)
    if st.sidebar.button("📈 Actions", key="btn_actions", 
                        use_container_width=True, 
                        type="primary" if st.session_state.active_section == "Actions" else "secondary"):
        st.session_state.active_section = "Actions"
        st.session_state.active_item = list(SKILL_TABS.keys())[0] if SKILL_TABS else None
    
    if st.session_state.active_section == "Actions":
        skill_options = list(SKILL_TABS.keys())
        selected_skill = st.radio("Sélection d'action", skill_options, key="skill_radio", label_visibility="collapsed")
        st.session_state.active_item = selected_skill
    
    # Catégorie Statistiques Joueur
    if st.sidebar.button("👤 Stats Joueur", key="btn_player", 
                        use_container_width=True,
                        type="primary" if st.session_state.active_section == "Stats Joueur" else "secondary"):
        st.session_state.active_section = "Stats Joueur"
        st.session_state.active_item = "Joueur"
    
    # Catégorie Statistiques Globales
    if st.sidebar.button("🌐 Stats Globales", key="btn_global", 
                        use_container_width=True,
                        type="primary" if st.session_state.active_section == "Stats Globales" else "secondary"):
        st.session_state.active_section = "Stats Globales"
        st.session_state.active_item = "Statistique globale"
        
    # Zone pour les filtres généraux qui restent fixes
    if 'active_section' in st.session_state and st.session_state.active_section == "Actions":
        st.markdown("---")
        st.subheader("Filtres")
        with st.container():
            # Ce container sera fixe lors du défilement
            st.session_state.selected_moment = st.selectbox("Moment du set", ["Tout", "Début", "Milieu", "Fin"], key="moment_filter")
            
            # Récupérer les sets disponibles
            if players:
                available_sets = sorted(set.union(*(set(p.df['set_number'].dropna().unique()) for p in players if p.df is not None)))
                st.session_state.selected_sets = st.multiselect("Sets", options=available_sets, default=available_sets, key="sets_filter")
            
            # Option pour épingler les sélections de joueurs et de matchs
            st.checkbox("Épingler les sélections", value=True, help="Garde les sélections de joueurs et de matchs visibles lors du défilement", key="pin_selections")

# Définir le menu sélectionné en fonction de la sélection active
selected_menu = st.session_state.active_item

# Affichage selon l'onglet sélectionné
if selected_menu in SKILL_TABS:
    config = SKILL_TABS[selected_menu]
    skill = config["skill"]
    label = config["label"]

    if players:
        categories = unique_preserve_order(Player.SKILL_EVAL_MAPPINGS.get(skill, {}).values())
        skill_comparison_tab(players, skill=skill, label=label, categories=categories)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

elif selected_menu == "Joueur":
    if players:
        player_evolution_tab(players)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

elif selected_menu == "Statistique globale":
    global_stats_tab(players)