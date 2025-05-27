import os
import re
import glob
import pandas as pd
import streamlit as st
from typing import Tuple, List, Dict, Set

from player import Player
from datavolley import read_dv
from ui_utils import display_in_area
from filters import (
    create_selector, get_match_selector, player_selector, 
    team_selector, aggregate_team_stats, filter_players_by_criteria
)

@st.cache_data
def load_data() -> Tuple[List[Player], pd.DataFrame]:
    """Loads .dvw file data and creates Player objects."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(app_dir, 'data')
    file_paths = glob.glob(os.path.join(data_dir, '*.dvw'))
    
    if not file_paths:
        st.error("No .dvw files found in the 'data' folder.")
        return [], pd.DataFrame()

    all_plays, all_players = _load_dvw_files(file_paths)
    players, players_df = _create_player_objects(all_plays, all_players)
    _normalize_team_names(players)
    
    return players, players_df


def _load_dvw_files(file_paths: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads all DVW files and extracts play and player data."""
    all_plays, all_players = pd.DataFrame(), pd.DataFrame()

    for path in file_paths:
        try:
            dv = read_dv.DataVolley(path)
            match_day = dv.__dict__['match_info']['day'][0]

            df_plays = dv.get_plays()
            df_plays['match_day'] = match_day

            all_plays = pd.concat([all_plays, df_plays], ignore_index=True)
            all_players = pd.concat([all_players, dv.get_players()], ignore_index=True)
        except Exception as e:
            st.warning(f"Error loading file {os.path.basename(path)}: {e}")

    return all_plays.reset_index(drop=True), all_players


def _create_player_objects(all_plays: pd.DataFrame, all_players: pd.DataFrame) -> Tuple[List[Player], pd.DataFrame]:
    """Creates Player objects from loaded data."""
    players_actions = _index_actions_by_player(all_plays)
    
    players_df = all_players.drop_duplicates(subset=['player_id']).reset_index(drop=True)
    players = []
    
    for _, row in players_df.iterrows():
        player_id = row['player_id']
        indices = players_actions.get(player_id, [])
        
        player_actions = all_plays.loc[indices].copy() if indices else pd.DataFrame(columns=all_plays.columns)
        player_actions_prev, player_actions_next = _get_context_actions(indices, all_plays)
        
        player = Player(
            id_=player_id,
            first_name=row['name'].capitalize(),
            last_name=row['lastname'].capitalize(),
            number=row['player_number'],
            df=player_actions,
            df_previous_actions=player_actions_prev,
            df_next_actions=player_actions_next,
            team=_clean_team_name(row.get('team', ''))
        )
        players.append(player)
    
    return players, players_df


def _clean_team_name(team_name: str) -> str:
    """Cleans and formats a team name."""
    return re.sub(r'\d+', '', team_name).title().replace('_', '')


def _index_actions_by_player(all_plays: pd.DataFrame) -> Dict[str, List[int]]:
    """Creates an index of actions by player ID for faster access."""
    players_actions = {}
    
    for idx, row in all_plays.iterrows():
        player_id = row['player_id']
        if player_id not in players_actions:
            players_actions[player_id] = []
        players_actions[player_id].append(idx)
    
    return players_actions


def _get_context_actions(indices: List[int], all_plays: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Gets previous and next actions for the given indices."""
    player_actions_prev = pd.DataFrame(index=indices, columns=all_plays.columns)
    player_actions_next = pd.DataFrame(index=indices, columns=all_plays.columns)
    
    for idx in indices:
        if idx > 0:
            player_actions_prev.loc[idx] = all_plays.loc[idx - 1]
        
        if idx < len(all_plays) - 1:
            player_actions_next.loc[idx] = all_plays.loc[idx + 1]
    
    return player_actions_prev, player_actions_next


def _normalize_team_names(players: List[Player]) -> None:
    """Normalizes team names for consistency."""
    for p in players:
        if (p.team and is_team_france_avenir(p.team)) or p.team == "France Avenir 2024":
            p.team = "France Avenir"
        else:
            p.team = p.team.replace('�', 'é')


def is_team_france_avenir(team_name: str) -> bool:
    """Checks if a team name corresponds to France Avenir with variations."""
    if not team_name:
        return False
    team_name = team_name.lower()
    return team_name == "france avenir" or ("france" in team_name and "avenir" in team_name)

def reorder_dataframe_columns(df: pd.DataFrame, base_columns: List[str] = None) -> pd.DataFrame:
    """Réorganise les colonnes du DataFrame dans l'ordre souhaité."""
    if df.empty:
        return df

    if base_columns is None:
        base_columns = ["Name", "Team", "Total"]

    priority_columns = ["% Efficacité", "% Erreur"]

    other_percentage_columns = []

    absolute_columns = []
    
    for col in df.columns:
        if col not in base_columns + priority_columns:
            if col.startswith("% "):
                other_percentage_columns.append(col)
            else:
                absolute_columns.append(col)

    other_percentage_columns = sorted(other_percentage_columns)

    def sort_absolute_columns(cols):
        priority_order = ["Parfaite", "Positive"]
        priority_cols = [col for col in priority_order if col in cols]
        other_cols = sorted([col for col in cols if col not in priority_order])
        return priority_cols + other_cols
    
    absolute_columns = sort_absolute_columns(absolute_columns)

    final_order = base_columns + priority_columns + other_percentage_columns + absolute_columns

    final_order = [col for col in final_order if col in df.columns]
    
    return df[final_order]