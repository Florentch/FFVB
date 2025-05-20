import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
from utils import load_data
from filters import unique_preserve_order
from skill import skill_comparison_tab
from player_evolution import player_evolution_tab
from player_comparison import make_comparison_tab 
from set_skill import set_tab
from stat_global import global_stats_tab
from config import SKILL_EVAL_MAPPINGS, SKILL_TABS, SET_MOMENTS


# Configuration de la page
st.set_page_config(
    page_title="Analyse CNVB Saison 2024-2025", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS pour ajuster la largeur de la sidebar
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 0%;
        max-width: 25%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Analyse de Volleyball")

# Chargement des données
with st.spinner("Chargement des données..."):
    players, players_df = load_data()
    
    if 'players' not in st.session_state:
        st.session_state['players'] = players
        st.session_state['players_df'] = players_df

# Initialisation des états de session
if 'active_section' not in st.session_state:
    st.session_state.active_section = "Stats Globales"
    st.session_state.active_item = "Statistique globale"

if 'pin_selections' not in st.session_state:
    st.session_state.pin_selections = True

# Sidebar général
with st.sidebar:
    st.subheader("Informations générales")
    
    if players:
        st.write(f"📊 **{len(players)}** joueurs au total")
        
        all_match_ids = set()
        for player in players:
            if player.df is not None:
                all_match_ids.update(player.df['match_id'].unique())
        match_count = len(all_match_ids)
        st.write(f"🏐 **{match_count + 1}** matchs analysés")
    else:
        st.warning("Aucune donnée disponible.")

    # Navigation
    st.markdown("---")
    st.subheader("Navigation")
    
    nav_sections = {
        "Stats Globales": "🌐 Stats Globales",
        "Actions": "📈 Actions",
        "Stats Joueur": "👤 Stats Joueur"
    }
    
    for section_id, section_label in nav_sections.items():
        button_type = "primary" if st.session_state.active_section == section_id else "secondary"
        if st.sidebar.button(section_label, key=f"btn_{section_id.lower().replace(' ', '_')}", 
                           use_container_width=True, type=button_type):
            st.session_state.active_section = section_id
            
            # Définir l'élément actif par défaut pour chaque section
            if section_id == "Stats Globales":
                st.session_state.active_item = "Statistique globale"
            elif section_id == "Actions":
                st.session_state.active_item = list(SKILL_TABS.keys())[0] if SKILL_TABS else None
            elif section_id == "Stats Joueur":
                st.session_state.active_item = "Joueur"
    
    # Sous-menu pour la section Actions
    if st.session_state.active_section == "Actions":
        skill_options = list(SKILL_TABS.keys())
        selected_skill = st.radio("Sélection d'action", skill_options, key="skill_radio", label_visibility="collapsed")
        st.session_state.active_item = selected_skill
        
        st.markdown("---")
        st.subheader("Filtres")
        
        with st.container():
            st.session_state.selected_moment = st.selectbox("Moment du set", SET_MOMENTS, key="moment_filter")
            
            if players:
                available_sets = sorted(set.union(*(set(p.df['set_number'].dropna().unique()) for p in players if p.df is not None)))
                st.session_state.selected_sets = st.multiselect("Sets", options=available_sets, default=available_sets, key="sets_filter")
            
            st.checkbox("Épingler les sélections", value=True, help="Garde les sélections de joueurs et de matchs visibles lors du défilement", key="pin_selections")
    
    # Sous-menu pour la section Stats Joueur
    elif st.session_state.active_section == "Stats Joueur":
        player_options = ["Joueur", "Comparaison"]
        selected_player_view = st.radio("Vue", player_options, key="player_view_radio", label_visibility="collapsed")
        st.session_state.active_item = selected_player_view

# Définir le menu sélectionné en fonction de la sélection active
selected_menu = st.session_state.active_item

# Affichage selon l'onglet sélectionné
if selected_menu == "Statistique globale":
    global_stats_tab(st.session_state['players'])

elif selected_menu in SKILL_TABS:
    config = SKILL_TABS[selected_menu]
    skill = config["skill"]
    label = config["label"]

    if selected_menu == "Passe":
        if st.session_state['players']:
            set_tab(st.session_state['players'])
        else:
            st.warning("Aucune donnée disponible pour l'analyse des passes.")
    elif st.session_state['players']:
        categories = unique_preserve_order(SKILL_EVAL_MAPPINGS.get(skill, {}).values())
        skill_comparison_tab(st.session_state['players'], skill=skill, label=label, categories=categories)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

elif selected_menu == "Joueur":
    if st.session_state['players']:
        player_evolution_tab(st.session_state['players'])
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

elif selected_menu == "Comparaison":
    if st.session_state['players']:
        make_comparison_tab(st.session_state['players'])
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")