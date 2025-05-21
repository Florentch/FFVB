import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional, Union, Tuple

from utils import player_selector, team_selector, get_match_selector, display_in_area
from visualizations import create_bar_chart, create_pie_chart, create_team_pie_charts
from config import SKILL_DISPLAY_METRICS
from constants import MIN_ACTIONS, KEY_METRICS
from player import Player
from filters import filter_players_by_criteria
from ui_utils import display_warning_if_empty


def skill_comparison_tab(players: List[Player], skill: str, label: str = "réceptions", categories: Optional[List[str]] = None) -> None:
    """Main function to create a tab for analyzing specific volleyball skills across players and teams."""
    st.header(f"📥 Analyse des {label}")

    specific_categories = categories or SKILL_DISPLAY_METRICS.get(skill, KEY_METRICS[:2])
    
    players_with_data = filter_players_by_criteria(players, MIN_ACTIONS, skill)
    if display_warning_if_empty(players_with_data, f"Aucun joueur avec des données de {label} trouvées."):
        return

    mode = setup_comparison_mode_selector()
    selected_matches = get_match_selector(players_with_data)
    
    if not selected_matches:
        st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return

    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)

    show_comparison_by_mode(
        mode, players_with_data, selected_matches, 
        moment, set_filter, skill, label, specific_categories
    )


def show_comparison_by_mode(mode: str, players: List[Player], selected_matches: List[str], moment: str, set_filter: Optional[Union[int, List[int]]], skill: str, label: str, categories: List[str]) -> None:
    """Displays either player or team comparisons based on selected mode."""
    if mode == "Par Joueurs":
        show_player_comparison(players, selected_matches, moment, set_filter, skill, label, categories)
    else:
        show_team_comparison(players, selected_matches, moment, set_filter, skill, label, categories)


def setup_comparison_mode_selector() -> str:
    """Creates UI selector for comparison mode (players vs teams)."""
    is_pinned = st.session_state.get('pin_selections', True)
    
    area_func = st.sidebar if is_pinned else st
    mode = area_func.radio(
        "Mode de comparaison", 
        ["Par Joueurs", "Par Équipes"], 
        horizontal=True, 
        label_visibility="visible"
    )
    
    return mode


def show_player_comparison(players_with_data: List[Player], selected_matches: List[str], moment: str, set_filter: Optional[Union[int, List[int]]], skill: str, label: str, categories: List[str]) -> None:
    """Creates comparison view for players' performance in a specific skill."""
    df = player_selector(players_with_data, skill, moment, selected_matches, set_filter)
    if df is None or df.empty:
        return
        
    display_player_stats(players_with_data, selected_matches, moment, set_filter, skill, label, categories, df)


def show_team_comparison(players_with_data: List[Player], selected_matches: List[str], moment: str, set_filter: Optional[Union[int, List[int]]], skill: str, label: str, categories: List[str]) -> None:
    """Creates comparison view for teams' performance in a specific skill."""
    df = team_selector(players_with_data, skill, moment, selected_matches, set_filter)
    if df is None or df.empty:
        return
        
    display_team_stats(df, skill, label, categories)


def display_player_stats(players: List[Player], selected_matches: List[str], moment: str, set_filter: Optional[Union[int, List[int]]], skill: str, label: str, categories: List[str], df: pd.DataFrame) -> None:
    """Displays detailed statistics and visualizations for individual players' performance."""
    st.dataframe(df.set_index("Name"), use_container_width=True)
    
    fig = create_bar_chart(df, categories)
    st.plotly_chart(fig, use_container_width=True)
    
    display_player_ranking(df, categories, skill)


def display_player_ranking(df: pd.DataFrame, categories: List[str], skill: str) -> None:
    """Displays a ranking table of players based on their performance in a specific skill."""
    main_metric = "% Efficacité"
    data = df.to_dict('records')
    
    if main_metric and all(main_metric in d for d in data):
        classement = sorted(data, key=lambda x: -x.get(main_metric, 0))
        st.subheader(f"🏆 Classement : {main_metric}")
        
        specific_metrics = SKILL_DISPLAY_METRICS.get(skill, KEY_METRICS[:2])
        
        columns_to_show = ["Name", "Team", main_metric]
        
        for metric in specific_metrics:
            if metric != main_metric:
                columns_to_show.append(metric)
        
        columns_to_show.append("Total")
    else:
        classement = data
        st.subheader("🏆 Classement indisponible")
        columns_to_show = ["Name", "Team", "Total"]

    columns_to_show = [col for col in columns_to_show if col in pd.DataFrame(classement).columns or col == "Team" or col == "Name"]
    
    st.table(pd.DataFrame(classement)[columns_to_show])


def display_team_stats(df: pd.DataFrame, skill: str, label: str, categories: List[str]) -> None:
    """Displays detailed statistics and visualizations for teams' performance."""
    st.subheader("📊 Statistiques moyennes par équipe")

    display_df = df.copy()
    for col in display_df.columns:
        if col.startswith('% % '):
            new_col = col.replace('% % ', '% ')
            display_df.rename(columns={col: new_col}, inplace=True)

    st.dataframe(display_df.set_index("Team"), use_container_width=True)

    create_team_pie_charts(df, categories, label)