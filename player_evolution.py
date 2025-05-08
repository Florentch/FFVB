import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from player import Player
from config import SKILL_EVAL_MAPPINGS, DEFAULT_THRESHOLDS, SET_MOMENTS
from utils import display_in_area, is_team_france_avenir
from visualizations import create_evolution_chart as viz_create_evolution_chart
from visualizations import display_radar_with_stats

def player_evolution_tab(players):
    """
    Affiche l'onglet d'évolution des performances des joueurs au fil des matchs
    """
    st.header("📈 Évolution des Performances")

    # Filtrer pour ne garder que les joueurs France Avenir avec des données
    players_with_data = [p for p in players if len(p.df) > 0 if is_team_france_avenir(p.team)]

    if not players_with_data:
        st.warning("Aucun joueur du CNVB 24-25 avec des données n'a été trouvé.")
        return

    # Utilisation de display_in_area pour afficher les éléments UI dans la zone appropriée
    skill = display_in_area(st.radio, 
                            "Action à analyser", 
                            ["Reception", "Block", "Dig", "Serve", "Attack"],
                            horizontal=True, 
                            label_visibility="visible")
    
    moment = display_in_area(st.selectbox, 
                             "Choisir le moment dans le set", 
                             SET_MOMENTS)

    player_names = [f"{p.first_name} {p.last_name}" for p in players_with_data]
    selected_name = display_in_area(st.selectbox, 
                                    "Sélection du joueur CNVB", 
                                    player_names)
    
    selected_player = next((p for p in players_with_data if f"{p.first_name} {p.last_name}" == selected_name), None)

    if selected_player:
        display_player_evolution(selected_player, moment, skill)


def display_player_evolution(player, moment, skill):
    """
    Affiche l'évolution des performances d'un joueur pour une compétence donnée.
    
    Cette fonction:
    1. Récupère les données des matchs pour la compétence choisie
    2. Permet de sélectionner les matchs à analyser
    3. Affiche les graphiques d'évolution et les statistiques
    """
    # Récupérer les données de la compétence pour le joueur et le moment
    df_skill = player.get_action_df(skill, moment)
    match_ids = df_skill['match_id'].dropna().unique()

    if not match_ids.size:
        st.warning(f"Aucun match avec des actions '{skill}' trouvé pour {player.first_name} {player.last_name}.")
        return

    # Préparer les données de match pour l'affichage
    match_data = []
    for match_id in match_ids:
        match_rows = player.df[player.df['match_id'] == match_id]
        if len(match_rows) > 0:
            match_row = match_rows.iloc[0]
            match_day = match_row.get('match_day', '')
            home_team = match_row.get('home_team', 'Équipe A')
            visiting_team = match_row.get('visiting_team', 'Équipe B')
            try:
                match_date = datetime.strptime(match_day, '%d/%m/%Y')
            except (ValueError, TypeError):
                match_date = datetime(2000, 1, 1)  # Date par défaut en cas d'erreur
            match_data.append({
                'match_id': match_id,
                'match_label': f"{home_team} vs {visiting_team}",
                'match_day': match_day,
                'match_date': match_date
            })

    # Trier les matchs par date
    match_data.sort(key=lambda x: x['match_date'])
    matches_df = pd.DataFrame(match_data)
    match_options = matches_df['match_id'].tolist()
    match_labels = {m_id: f"{row['match_label']} - {row['match_day']}" for m_id, row in zip(matches_df['match_id'], matches_df.to_dict('records'))}

    # Sélection des matchs via la fonction utilitaire
    selected_matches = display_in_area(st.multiselect,
                                      "Sélectionner les matchs à analyser",
                                      options=match_options,
                                      format_func=lambda x: match_labels.get(x, str(x)),
                                      default=match_options)

    if not selected_matches:
        st.info("Veuillez sélectionner au moins un match pour voir l'évolution.")
        return

    # Filtrer et trier les matchs sélectionnés
    filtered_matches = matches_df[matches_df['match_id'].isin(selected_matches)].sort_values('match_date')
    
    # Récupérer les statistiques pour chaque match
    stats_by_match = []
    for _, row in filtered_matches.iterrows():
        match_id = row['match_id']
        match_stats = player.get_skill_stats(skill, moment, match_filter=[match_id])
        if match_stats["Total"] > 0:
            entry = {
                'match_id': match_id,
                'match_label': row['match_label'],
                'match_day': row['match_day'],
                'total': match_stats["Total"]
            }
            entry.update({k: v for k, v in match_stats.items() if k != "Total"})
            stats_by_match.append(entry)

    if not stats_by_match:
        st.warning("Aucune statistique disponible pour les matchs sélectionnés.")
        return

    stats_df = pd.DataFrame(stats_by_match)

    # Afficher les données brutes dans un expandeur
    with st.expander("Voir les données brutes"):
        st.dataframe(stats_df)

    # Récupérer la première catégorie pour la compétence sélectionnée
    first_category = list(dict.fromkeys(SKILL_EVAL_MAPPINGS[skill].values()))[0]
    target_label = f"% {first_category}"

    # Objectif par défaut depuis la config
    target_default = DEFAULT_THRESHOLDS.get(skill, 25)  # 25% par défaut si non précisé
    
    # Slider pour définir l'objectif
    target = display_in_area(st.slider, 
                            f"Objectif {target_label}", 
                            min_value=0, 
                            max_value=100, 
                            value=target_default, 
                            step=5)

    # Création des graphiques d'analyse
    create_evolution_chart(stats_df, target, skill)

    # Affichage des statistiques globales
    display_global_stats(player, skill, moment, selected_matches, target, target_label)

    # Analyse détaillée avec graphique radar
    st.subheader("🔍 Analyse détaillée")
    create_radar_chart(stats_df, skill)


def display_global_stats(player, skill, moment, selected_matches, target, target_label):
    """
    Affiche les statistiques globales pour les matchs sélectionnés
    """
    st.subheader("📊 Statistiques globales")
    global_stats = player.get_skill_stats(skill, moment, match_filter=selected_matches)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(target_label, f"{global_stats[target_label]}%")
    with col2:
        st.metric(target_label.split("% ")[-1], global_stats.get(target_label.split("% ")[-1], 0))
    with col3:
        st.metric("Total", global_stats["Total"])
    with col4:
        delta = global_stats[target_label] - target
        st.metric("Vs. Objectif", f"{delta}%", delta_color="normal" if delta >= 0 else "inverse")


def create_evolution_chart(stats_df, target, skill):
    """
    Crée un graphique d'évolution des performances au fil des matchs
    """
    skill_labels = Player.get_skill_labels()[skill]
    fig = viz_create_evolution_chart(stats_df, target, skill_labels)
    st.plotly_chart(fig, use_container_width=True)


def create_radar_chart(stats_df, skill):
    """
    Crée un graphique radar des performances moyennes par catégorie
    """
    # Filtrer pour ne garder que les colonnes de pourcentage
    categories = [col for col in stats_df.columns if col.startswith('%')]
    display_radar_with_stats(stats_df, categories)