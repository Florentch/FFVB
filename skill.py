import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

from utils import player_selector, team_selector, get_match_selector, display_in_area
from visualizations import create_bar_chart, create_pie_chart, create_team_pie_charts


# Dans skill.py, remplacer la fonction skill_comparison_tab
def skill_comparison_tab(players, skill, label="réceptions", categories=None):
    """
    Affiche l'onglet de comparaison des compétences des joueurs
    """
    st.header(f"📥 Analyse des {label}")

    # Filtrer les joueurs qui ont des données pour cette compétence
    players_with_data = filter_players_with_data(players, skill)
    if not players_with_data:
        st.warning(f"Aucun joueur avec des données de {label} trouvées.")
        return

    # Configuration de l'interface et récupération des sélections
    mode = setup_comparison_mode_selector()
    selected_matches = get_match_selector(players_with_data)
    
    if not selected_matches:
        st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return

    # Récupération des filtres de session
    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)

    # Affichage selon le mode sélectionné
    show_comparison_by_mode(
        mode, players_with_data, selected_matches, 
        moment, set_filter, skill, label, categories
    )

# Nouvelle fonction pour dispatcher selon le mode
def show_comparison_by_mode(mode, players, selected_matches, moment, set_filter, skill, label, categories):
    """
    Affiche la comparaison selon le mode sélectionné
    """
    if mode == "Par Joueurs":
        show_player_comparison(players, selected_matches, moment, set_filter, skill, label, categories)
    else:
        show_team_comparison(players, selected_matches, moment, set_filter, skill, label, categories)


def filter_players_with_data(players, skill):
    """
    Filtre les joueurs qui ont suffisamment de données pour l'analyse
    """
    return [p for p in players if len(p.get_action_df(skill)) > 4]


def setup_comparison_mode_selector():
    """
    Configure le sélecteur de mode de comparaison
    """
    # Déterminer la zone d'affichage (sidebar ou principale)
    is_pinned = st.session_state.get('pin_selections', True)
    
    if not is_pinned:
        # Si on est dans la zone principale, utilisez des colonnes pour l'affichage
        col1, col2 = st.columns(2)
        with col1:
            mode = st.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], 
                           horizontal=True, label_visibility="visible")
    else:
        # Si on est dans la sidebar, affichage vertical
        mode = st.sidebar.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], 
                               horizontal=True, label_visibility="visible")
    
    return mode


def show_player_comparison(players_with_data, selected_matches, moment, set_filter, skill, label, categories):
    """
    Gère l'affichage de la comparaison par joueurs
    """
    df = player_selector(players_with_data, skill, moment, selected_matches, set_filter)
    if df is None or df.empty:
        # Un message d'avertissement est déjà affiché dans player_selector
        return
        
    display_player_stats(players_with_data, selected_matches, moment, set_filter, skill, label, categories, df)


def show_team_comparison(players_with_data, selected_matches, moment, set_filter, skill, label, categories):
    """
    Gère l'affichage de la comparaison par équipes
    """
    df = team_selector(players_with_data, skill, moment, selected_matches, set_filter)
    if df is None or df.empty:
        # Un message d'avertissement est déjà affiché dans team_selector
        return
        
    display_team_stats(df, skill, label, categories)


def display_player_stats(players, selected_matches, moment, set_filter, skill, label, categories, df):
    """
    Affiche les statistiques par joueur
    """
    # Affichage du tableau de données
    st.dataframe(df.set_index("Nom"), use_container_width=True)
    
    # Création du graphique
    fig = create_player_bar_chart(df, categories)
    st.plotly_chart(fig, use_container_width=True)
    
    # Affichage du classement des joueurs
    display_player_ranking(df, categories)


def create_player_bar_chart(df, categories):
    """
    Crée un graphique à barres pour la comparaison de joueurs
    """
    return create_bar_chart(df, categories)


def display_player_ranking(df, categories):
    """
    Affiche le classement des joueurs selon la métrique principale
    """
    # Déterminer la métrique de classement (première catégorie en %)
    main_metric = "% Efficacité"

    data = df.to_dict('records')
    
    if main_metric and all(main_metric in d for d in data):
        classement = sorted(data, key=lambda x: -x.get(main_metric, 0))
        st.subheader(f"🏆 Classement : {main_metric}")
        columns_to_show = ["Nom", "Équipe", main_metric, categories[0], categories[5], "Total"]
    else:
        classement = data
        st.subheader("🏆 Classement indisponible")
        columns_to_show = ["Nom", "Équipe", "Total"]

    st.table(pd.DataFrame(classement)[columns_to_show])


def display_team_stats(df, skill, label, categories):
    """
    Affiche les statistiques par équipe
    """
    st.subheader("📊 Statistiques moyennes par équipe")

    # Prétraitement du DataFrame pour supprimer les préfixes % en double
    display_df = df.copy()
    # Correction des colonnes avec % en double
    for col in display_df.columns:
        if col.startswith('% % '):
            new_col = col.replace('% % ', '% ')
            display_df.rename(columns={col: new_col}, inplace=True)

    # Affichage du tableau
    st.dataframe(display_df.set_index("Équipe"), use_container_width=True)

    # Affichage des graphiques en camembert
    display_team_pie_charts(df, categories, label)


# Remplacer la fonction display_team_pie_charts
def display_team_pie_charts(df, categories, label):
    """
    Affiche les graphiques en camembert pour chaque équipe
    
    Args:
        df (DataFrame): Données des équipes
        categories (list): Catégories à afficher
        label (str): Libellé pour l'affichage
    """
    create_team_pie_charts(df, categories, label)