import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from player import Player
from filters import get_match_selector, filter_players_with_data, unique_preserve_order
from ui_utils import display_table_with_title, create_tab_section
from constants import SKILL_TRANSLATION, KEY_METRICS

def translate_skill(skill: str) -> str:
    """Translates skill name from internal format to display format."""
    return SKILL_TRANSLATION.get(skill, skill)

def get_skill_counts(player: Player, skills: list, set_moment: str, match_filter: list, set_filter: list) -> dict:
    """Computes the count of actions for each skill for a given player with filters applied."""
    skill_counts = {}
    for skill in skills:
        try:
            df = player.get_action_df(skill, set_moment=set_moment, match_filter=match_filter, set_filter=set_filter)
            skill_counts[skill] = len(df) if df is not None and not df.empty else 0
        except Exception:
            skill_counts[skill] = 0
    return skill_counts

def display_player_card(player: Player, selected_skills: list = None, set_moment: str = None, match_filter: list = None, set_filter: list = None) -> None:
    """Renders a player information card with basic stats and counts."""
    card_style = """
    <style>
    .player-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)

    with st.container():
        st.markdown(f"<div class='player-card'>", unsafe_allow_html=True)
        st.subheader(f"{player.get_full_name()}")
        st.markdown(f"**Équipe:** {player.team}")
        st.markdown(f"**Numéro:** {player.number}")

        if selected_skills and (match_filter is not None):
            skill_counts = get_skill_counts(player, selected_skills, set_moment, match_filter, set_filter)

            col1, col2, col3 = st.columns(3)
            col1.metric("Attaques", skill_counts.get("Attack", 0))
            col2.metric("Services", skill_counts.get("Serve", 0))
            col3.metric("Réceptions", skill_counts.get("Reception", 0))

        st.markdown("</div>", unsafe_allow_html=True)

def get_filtered_players(players: list, selected_skills: list, set_moment: str, match_filter: list, set_filter: list, min_actions: int = 0) -> list:
    """Filters players who have sufficient data for the selected skills and filters."""
    filtered_players = []
    for player in players:
        for skill in selected_skills:
            filtered_data = filter_players_with_data(
                [player],
                match_filter=match_filter,
                skill=skill,
                set_moment=set_moment,
                set_filter=set_filter,
                min_actions=min_actions
            )
            if player in filtered_data:
                filtered_players.append(player)
                break
    return filtered_players

def get_players_for_comparison(filtered_players: list) -> dict:
    """Organizes players by team and creates a mapping of display names to player objects."""
    teams = {}
    seen_names = set()
    
    for p in filtered_players:
        if p.df is None or p.df.empty or not p.team:
            continue

        if p.team not in teams:
            teams[p.team] = []
        teams[p.team].append(p)
    
    sorted_teams = sorted(teams.keys())
    player_list = []
    
    for team in sorted_teams:
        for p in sorted(teams[team], key=lambda x: (x.last_name, x.first_name)):
            full_name_team = f"{p.get_full_name()} ({p.team})"
            if full_name_team not in seen_names:
                seen_names.add(full_name_team)
                player_list.append((full_name_team, p))
    
    return {name: player for name, player in player_list}

def generate_comparison_data(player1: Player, player2: Player, skills: list, set_moment: str, match_filter: list, set_filter: list, min_actions: int = 0) -> dict:
    """Generates detailed comparison statistics between two players across multiple skills."""
    comparison_data = {}
    for skill in skills:
        try:
            # Get DataFrames with applied filters
            player1_df = player1.get_action_df(skill, set_moment=set_moment, match_filter=match_filter, set_filter=set_filter)
            player2_df = player2.get_action_df(skill, set_moment=set_moment, match_filter=match_filter, set_filter=set_filter)

            # Count valid actions
            p1_actions = len(player1_df) if player1_df is not None and not player1_df.empty else 0
            p2_actions = len(player2_df) if player2_df is not None and not player2_df.empty else 0

            # Skip if not enough data
            if p1_actions < min_actions and p2_actions < min_actions:
                continue

            # Get statistics
            stats1 = player1.get_skill_stats(skill, set_moment=set_moment, match_filter=match_filter, set_filter=set_filter) or {}
            stats2 = player2.get_skill_stats(skill, set_moment=set_moment, match_filter=match_filter, set_filter=set_filter) or {}

            # Identify common metrics (percentages + Total)
            metrics = {key for key in list(stats1.keys()) + list(stats2.keys()) if key.startswith("%") or key == "Total"}

            # Create comparison data structure
            skill_data = {
                "skill": skill,
                "player1_name": player1.get_full_name(),
                "player2_name": player2.get_full_name(),
                "player1_team": player1.team,
                "player2_team": player2.team,
                "metrics": {
                    key: {
                        "player1": stats1.get(key, 0),
                        "player2": stats2.get(key, 0),
                        "diff": stats1.get(key, 0) - stats2.get(key, 0)
                    } for key in metrics
                }
            }
            comparison_data[skill] = skill_data
        except Exception as e:
            st.error(f"Erreur lors de la génération des données pour {skill}: {e}")
    return comparison_data

def display_radar_comparison(comparison_data: dict, player1: Player, player2: Player) -> None:
    """Creates radar charts comparing players across multiple skills and metrics."""
    if not comparison_data:
        st.info("Pas assez de données pour créer un graphique radar.")
        return
    
    skills = list(comparison_data.keys())
    key_metrics = ["% Efficacité", "% Erreur"]
    
    for metric in key_metrics:
        if any(metric in data["metrics"] for data in comparison_data.values()):
            player_data = {
                "player1": {"r": [], "theta": []},
                "player2": {"r": [], "theta": []}
            }
            
            for skill in skills:
                skill_data = comparison_data[skill]
                if metric in skill_data["metrics"]:
                    for player_key in ["player1", "player2"]:
                        player_data[player_key]["theta"].append(skill)
                        player_data[player_key]["r"].append(skill_data["metrics"][metric][player_key])
            
            if player_data["player1"]["r"] and player_data["player2"]["r"]:
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=player_data["player1"]["r"],
                    theta=player_data["player1"]["theta"],
                    fill='toself',
                    name=f"{player1.get_full_name()} ({player1.team})"
                ))
                
                fig.add_trace(go.Scatterpolar(
                    r=player_data["player2"]["r"],
                    theta=player_data["player2"]["theta"],
                    fill='toself',
                    name=f"{player2.get_full_name()} ({player2.team})"
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(max(player_data["player1"]["r"] or [0]), 
                                         max(player_data["player2"]["r"] or [0])) * 1.1]
                        )
                    ),
                    title=f"Comparaison - {metric}",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)

def display_bar_comparison(comparison_data: dict, player1: Player, player2: Player, selected_skills: list) -> None:
    """Creates bar charts comparing player metrics for each selected skill."""
    if not comparison_data:
        st.info("Pas assez de données pour créer les graphiques à barres.")
        return
    
    for skill in selected_skills:
        if skill not in comparison_data:
            continue
            
        skill_data = comparison_data[skill]
        metrics = [k for k in skill_data["metrics"].keys() if k != "Total" and k.startswith("%")]
        
        if not metrics:
            continue
            
        values_player1 = [skill_data["metrics"][m]["player1"] for m in metrics]
        values_player2 = [skill_data["metrics"][m]["player2"] for m in metrics]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=metrics,
            y=values_player1,
            name=f"{player1.get_full_name()} ({player1.team})",
            marker_color='royalblue'
        ))
        
        fig.add_trace(go.Bar(
            x=metrics,
            y=values_player2,
            name=f"{player2.get_full_name()} ({player2.team})",
            marker_color='firebrick'
        ))
        
        skill_name = translate_skill(skill)
        
        fig.update_layout(
            title=f"Comparaison - {skill_name}",
            xaxis_title="Métriques",
            yaxis_title="Pourcentage (%)",
            barmode='group',
            height=400
        )
        
        total1 = skill_data["metrics"].get("Total", {}).get("player1", 0)
        total2 = skill_data["metrics"].get("Total", {}).get("player2", 0)
        st.markdown(f"**{skill_name}** - *{player1.get_full_name()}: {total1} actions, {player2.get_full_name()}: {total2} actions*")
        
        st.plotly_chart(fig, use_container_width=True)

def display_table_comparison(comparison_data: dict) -> None:
    """Displays a tabular comparison of players' metrics across skills."""
    if not comparison_data:
        st.info("Pas assez de données pour créer le tableau comparatif.")
        return
    
    table_data = []
    
    for skill, data in comparison_data.items():
        skill_name = translate_skill(skill)
        
        for metric, values in data["metrics"].items():
            if metric == "Total":
                continue
                
            table_data.append({
                "Compétence": skill_name,
                "Métrique": metric,
                f"{data['player1_name']} ({data['player1_team']})": values["player1"],
                f"{data['player2_name']} ({data['player2_team']})": values["player2"],
                "Différence": values["diff"]
            })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            column_config={
                "Différence": st.column_config.NumberColumn(
                    "Différence",
                    format="%.1f",
                    help="Différence entre les deux joueurs (Joueur 1 - Joueur 2)"
                )
            },
            use_container_width=True
        )

def display_face_to_face_comparison(comparison_data: dict, player1: Player, player2: Player) -> None:
    """Creates a side-by-side comparison view highlighting key metrics between players."""
    if not comparison_data:
        st.info("Pas assez de données pour créer la visualisation face à face.")
        return
    
    player1_name = f"{player1.get_full_name()} ({player1.team})"
    player2_name = f"{player2.get_full_name()} ({player2.team})"
    
    for skill, data in comparison_data.items():
        skill_name = translate_skill(skill)
        
        st.markdown(f"### Comparaison - {skill_name}")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        player_cols = [col1, col3]
        player_names = [player1_name, player2_name]
        player_keys = ["player1", "player2"]
        
        for idx, (col, name, key) in enumerate(zip(player_cols, player_names, player_keys)):
            with col:
                st.markdown(f"#### {name}")
                for metric in KEY_METRICS:
                    if metric in data["metrics"]:
                        value = data["metrics"][metric][key]
                        if metric == "Total":
                            st.metric(metric, int(value))
                        else:
                            st.metric(metric, f"{value:.1f}%")
        
        with col2:
            st.markdown("#### VS")
            for metric in KEY_METRICS:
                if metric in data["metrics"]:
                    diff = data["metrics"][metric]["diff"]
                    
                    if metric == "Total":
                        st.metric("Différence", f"{int(diff)}")
                    else:
                        formatted_diff = f"{diff:.1f}%"
                        
                        delta_value = -diff if metric == "% Erreur" else diff
                        st.metric("Différence", formatted_diff, delta=f"{delta_value:.1f}")
        
        st.markdown("---")

def display_comparison_tabs(comparison_data: dict, player1: Player, player2: Player, selected_skills: list) -> None:
    """Creates a tabbed interface for different comparison visualizations."""
    tabs_data = {
        "Radar": lambda: display_radar_comparison(comparison_data, player1, player2),
        "Barres": lambda: display_bar_comparison(comparison_data, player1, player2, selected_skills),
        "Tableau": lambda: display_table_comparison(comparison_data),
        "Face à Face": lambda: display_face_to_face_comparison(comparison_data, player1, player2)
    }
    
    create_tab_section(tabs_data)

def init_session_state() -> None:
    """Initializes the session state variables for comparison filters and selections."""
    if 'comparison_set_filter' not in st.session_state:
        st.session_state.comparison_set_filter = [str(i) for i in range(1, 6)]
    
    if 'comparison_moment_filter' not in st.session_state:
        st.session_state.comparison_moment_filter = "Tout"
    
    if 'comparison_selected_skills' not in st.session_state:
        st.session_state.comparison_selected_skills = ["Attack", "Serve", "Reception"]
    
    if 'comparison_player1_option' not in st.session_state:
        st.session_state.comparison_player1_option = None
    
    if 'comparison_player2_option' not in st.session_state:
        st.session_state.comparison_player2_option = None

def make_comparison_tab(players: list) -> None:
    """Main function to create the player comparison interface with all controls and visualizations."""
    st.title("🔍 Comparaison de Joueurs")

    if not isinstance(players, list) or len(players) == 0:
        st.error("Aucune donnée de joueur disponible.")
        return

    # Initialize session state
    init_session_state()

    # Available skills
    skills = ["Attack", "Block", "Serve", "Reception", "Dig", "Set"]

    # Layout for filters and player selection
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Filtres")

        # Match selection
        selected_matches = get_match_selector(players)
        if not selected_matches:
            st.warning("⚠️ Veuillez sélectionner au moins un match.")
            return

        # Set filters
        available_sets = [str(i) for i in range(1, 6)]  # Sets 1 to 5
        set_filter = st.multiselect(
            "Filtrer par set", 
            options=available_sets, 
            default=st.session_state.comparison_set_filter,
            format_func=lambda x: f"Set {x}",
            key="comparison_set_filter_select"
        )
        st.session_state.comparison_set_filter = set_filter
        
        # Use None if no sets selected
        if not set_filter:
            set_filter = None
            st.info("Aucun set sélectionné, utilisation de tous les sets.")

        # Set moment filter
        moment_filter_options = ["Tout", "0-10", "10-20", "20+"]
        moment_filter = st.selectbox(
            "Phase du set", 
            moment_filter_options,
            index=moment_filter_options.index(st.session_state.comparison_moment_filter),
            key="comparison_moment_filter_select"
        )
        st.session_state.comparison_moment_filter = moment_filter
        
        set_moment = None if moment_filter == "Tout" else moment_filter

        # Skill selection
        selected_skills = st.multiselect(
            "Compétences à comparer", 
            options=skills, 
            default=st.session_state.comparison_selected_skills,
            format_func=translate_skill,
            key="comparison_skills_select"
        )
        st.session_state.comparison_selected_skills = selected_skills
        
        if not selected_skills:
            st.warning("Veuillez sélectionner au moins une compétence.")
            return

    # Filter players based on selected criteria
    filtered_players = get_filtered_players(players, selected_skills, set_moment, selected_matches, set_filter)
    
    if not filtered_players:
        st.warning("Aucun joueur avec données valides pour les filtres sélectionnés.")
        return

    # Prepare player options for comparison
    player_dict = get_players_for_comparison(filtered_players)
    all_player_options = list(player_dict.keys())
    
    if not all_player_options:
        st.warning("Aucun joueur disponible avec les filtres sélectionnés.")
        return

    # Handle previously selected players that may not be available anymore
    if st.session_state.comparison_player1_option not in all_player_options:
        st.session_state.comparison_player1_option = all_player_options[0] if all_player_options else None
    
    remaining_options = [p for p in all_player_options if p != st.session_state.comparison_player1_option]
    if st.session_state.comparison_player2_option not in remaining_options:
        st.session_state.comparison_player2_option = remaining_options[0] if remaining_options else None

    # Display player selectors
    with col2:
        st.subheader("Sélectionner les joueurs")
        player1_option = st.selectbox(
            "Joueur 1", 
            options=all_player_options,
            index=all_player_options.index(st.session_state.comparison_player1_option) if st.session_state.comparison_player1_option in all_player_options else 0,
            key="player1_comparison"
        )
        st.session_state.comparison_player1_option = player1_option
        
        # Update remaining options to avoid selecting the same player twice
        remaining_options = [p for p in all_player_options if p != player1_option]
        
        player2_option = st.selectbox(
            "Joueur 2", 
            options=remaining_options,
            index=remaining_options.index(st.session_state.comparison_player2_option) if st.session_state.comparison_player2_option in remaining_options else 0,
            key="player2_comparison"
        )
        st.session_state.comparison_player2_option = player2_option

        if not player1_option or not player2_option:
            st.warning("Veuillez sélectionner deux joueurs.")
            return

        player1 = player_dict[player1_option]
        player2 = player_dict[player2_option]

    # Display player cards
    col1, col2 = st.columns(2)
    with col1:
        display_player_card(player1, selected_skills, set_moment, selected_matches, set_filter)
    with col2:
        display_player_card(player2, selected_skills, set_moment, selected_matches, set_filter)

    # Generate and display comparison data
    comparison_data = generate_comparison_data(player1, player2, selected_skills, set_moment, selected_matches, set_filter)
    
    if not comparison_data:
        st.warning("Pas assez de données pour cette comparaison avec les filtres sélectionnés.")
        return

    st.subheader("Comparaison détaillée")
    display_comparison_tabs(comparison_data, player1, player2, selected_skills)