import streamlit as st
import pandas as pd
from datetime import datetime

from player import Player
from config import SKILL_EVAL_MAPPINGS, DEFAULT_THRESHOLDS, SET_MOMENTS, SKILL_DISPLAY_METRICS
from utils import display_in_area, is_team_france_avenir, reorder_dataframe_columns
from visualizations import create_evolution_chart as viz_create_evolution_chart
from visualizations import display_radar_with_stats
from filters import get_display_name_from_mapping, get_all_codes_from_column

## player_evolution.py

def player_evolution_tab(players: list) -> None:
    """Displays the player performance evolution tab."""
    st.header("Évolution des Performances")

    players_with_data = [p for p in players if len(p.df) > 0 if is_team_france_avenir(p.team)]

    if not players_with_data:
        st.warning("Aucun joueur du CNVB 24-25 avec des données n'a été trouvé.")
        return

    skill = display_in_area(st.radio, 
                            "Action à analyser", 
                            ["Reception", "Block", "Dig", "Serve", "Attack"],
                            horizontal=True, 
                            label_visibility="visible")
    
    moment = display_in_area(st.selectbox, 
                             "Choisir le moment dans le set", 
                             SET_MOMENTS)

    set_options = ["Tous les sets"] + [str(i) for i in range(1, 6)]
    selected_set = display_in_area(st.selectbox, 
                                   "Filtrer par set", 
                                   set_options)

    # Filtre de type d'attaque uniquement pour le skill Attack
    attack_type = None
    if skill == "Attack":
        from config import ATTACK_TYPE
        all_attack_types = get_all_attack_types_for_skill(players_with_data, skill)
        all_attack_types_display = [get_display_name_from_dict(code, ATTACK_TYPE) for code in all_attack_types]
        attack_display_to_code = {get_display_name_from_dict(code, ATTACK_TYPE): code for code in all_attack_types}
        
        selected_attack_display = display_in_area(st.selectbox,
                                                  "Type d'attaque",
                                                  ["Tous"] + all_attack_types_display)
        
        attack_type = attack_display_to_code.get(selected_attack_display, selected_attack_display) if selected_attack_display != "Tous" else None

    player_names = [f"{p.first_name} {p.last_name}" for p in players_with_data]
    selected_name = display_in_area(st.selectbox, 
                                    "Sélection du joueur CNVB", 
                                    player_names)
    
    selected_player = next((p for p in players_with_data if f"{p.first_name} {p.last_name}" == selected_name), None)

    if selected_player:
        # Convert set selection to filter format
        set_filter = None if selected_set == "Tous les sets" else [selected_set]
        display_player_evolution(selected_player, moment, skill, set_filter, attack_type)


def display_player_evolution(player: Player, moment: str, skill: str, set_filter: list = None, attack_type: str = None) -> None:
    """
    Displays a player's performance evolution for a given skill.
    
    1. Retrieves match data for the chosen skill
    2. Allows selection of matches to analyze
    3. Displays evolution charts and statistics
    """    
    df_skill = player.get_action_df(skill, moment, set_filter=set_filter)
    
    # Filtrer par type d'attaque si spécifié
    if attack_type and skill == "Attack":
        df_skill = df_skill[df_skill['attack_code'] == attack_type]
    
    match_ids = df_skill['match_id'].dropna().unique()

    if not match_ids.size:
        st.warning(f"Aucun match avec des actions '{skill}' trouvé pour {player.first_name} {player.last_name}.")
        return

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
                match_date = datetime(2000, 1, 1)  # Default date in case of error
            match_data.append({
                'match_id': match_id,
                'match_label': f"{home_team} vs {visiting_team}",
                'match_day': match_day,
                'match_date': match_date
            })

    # Sort matches by date
    match_data.sort(key=lambda x: x['match_date'])
    matches_df = pd.DataFrame(match_data)
    match_options = matches_df['match_id'].tolist()
    match_labels = {m_id: f"{row['match_label']} - {row['match_day']}" for m_id, row in zip(matches_df['match_id'], matches_df.to_dict('records'))}

    selected_matches = display_in_area(st.multiselect,
                                      "Sélectionner les matchs à analyser",
                                      options=match_options,
                                      format_func=lambda x: match_labels.get(x, str(x)),
                                      default=match_options)

    if not selected_matches:
        st.info("Veuillez sélectionner au moins un match pour voir l'évolution.")
        return

    filtered_matches = matches_df[matches_df['match_id'].isin(selected_matches)].sort_values('match_date')
    
    stats_by_match = []
    for _, row in filtered_matches.iterrows():
        match_id = row['match_id']
        match_stats = get_skill_stats_with_attack_filter(player, skill, moment, [match_id], set_filter, attack_type)
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

    with st.expander("Voir les données brutes"):
        # Réorganiser les colonnes avec les colonnes de base spécifiques à l'évolution
        display_df = stats_df.drop(columns=['match_id'], errors='ignore')
        display_df = reorder_dataframe_columns(display_df, base_columns=["match_label", "match_day", "total"])
        st.dataframe(display_df)

    target_label = SKILL_DISPLAY_METRICS.get(skill, ["% Efficacité"])[0]
    target_default = DEFAULT_THRESHOLDS.get(skill, 25)

    create_evolution_chart(stats_df, target_default, skill)
    display_global_stats(player, skill, moment, selected_matches, target_default, target_label, stats_df, set_filter, attack_type)


def display_global_stats(player: Player, skill: str, moment: str, selected_matches: list, target: int, target_label: str, stats_df: pd.DataFrame, set_filter: list = None, attack_type: str = None) -> None:
    """Displays global statistics for selected matches."""
    st.subheader("Statistiques globales")
    global_stats = get_skill_stats_with_attack_filter(player, skill, moment, selected_matches, set_filter, attack_type)
    error_threshold = DEFAULT_THRESHOLDS.get(f"{skill}_Error", 15)
    
    # Calculate stability based on first efficiency metric if available
    stability = None
    efficiency_col = next((col for col in stats_df.columns if "Efficacité" in col), None)
    if efficiency_col and len(stats_df) > 1:
        stability = 100 - stats_df[efficiency_col].std()
    
    # First row: Efficiency, Efficiency vs Objective, Total
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(target_label, f"{global_stats[target_label]:.2f}%")
    
    with col2:
        delta_eff = global_stats[target_label] - target
        if delta_eff >= 0:
            st.metric("Vs. Obj. Eff.", f"{delta_eff:.2f}%", delta=f"{delta_eff:.2f}%", delta_color="normal")
        else:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff4b4b;">
                <div style="color: #262730; font-size: 0.875rem; font-weight: 600;">Vs. Obj. Eff.</div>
                <div style="color: #ff4b4b; font-size: 1.875rem; font-weight: 600;">{delta_eff:.2f}%</div>
                <div style="color: #ff4b4b; font-size: 0.875rem;">↓ {abs(delta_eff):.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.metric("Total", global_stats["Total"])
    
    # Second row: Error Rate, Error vs Objective, Stability
    col4, col5, col6 = st.columns(3)
    
    with col4:
        error_rate = global_stats.get("% Erreur", 0)
        st.metric("% Erreur", f"{error_rate:.2f}%")
    
    with col5:
        delta_err = error_threshold - error_rate
        if error_rate <= error_threshold:
            st.metric("Vs. Obj. Err.", f"{delta_err:.2f}%", delta=f"{delta_err:.2f}%", delta_color="normal")
        else:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff4b4b;">
                <div style="color: #262730; font-size: 0.875rem; font-weight: 600;">Vs. Obj. Err.</div>
                <div style="color: #ff4b4b; font-size: 1.875rem; font-weight: 600;">{delta_err:.2f}%</div>
                <div style="color: #ff4b4b; font-size: 0.875rem;">↓ {abs(delta_err):.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col6:
        if stability is not None:
            st.metric("% Stabilité", f"{stability:.1f}%")
        else:
            st.metric("% Stabilité", "N/A")

def get_all_attack_types_for_skill(players: list, skill: str) -> list:
    """Récupère tous les types d'attaque disponibles pour un skill donné."""
    if skill == "Attack":
        return get_all_codes_from_column(players, skill, 'attack_code')
    return []


def get_display_name_from_dict(code: str, type_dict: dict) -> str:
    """Convertit un code en nom explicite en utilisant le dictionnaire fourni."""
    return get_display_name_from_mapping(code, type_dict)


def get_skill_stats_with_attack_filter(player: Player, skill: str, moment: str, match_filter: list = None, set_filter: list = None, attack_type: str = None) -> dict:
    """Obtient les statistiques d'un skill avec filtre optionnel sur le type d'attaque."""
    if attack_type and skill == "Attack":
        # Utiliser la méthode existante avec les filtres appropriés
        return player.get_skill_stats_with_filters(skill, moment, match_filter, set_filter, "Tous", attack_type)
    else:
        # Utiliser la méthode standard
        return player.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)


def create_evolution_chart(stats_df: pd.DataFrame, target: int, skill: str) -> None:
    """Creates a performance evolution chart over matches."""
    skill_labels = SKILL_DISPLAY_METRICS.get(skill, ["% Efficacité"])
    
    error_threshold = DEFAULT_THRESHOLDS.get(f"{skill}_Error", 15)
    
    fig = viz_create_evolution_chart(stats_df, target, skill_labels, error_threshold)
    st.plotly_chart(fig, use_container_width=True)
