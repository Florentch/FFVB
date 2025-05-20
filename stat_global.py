import pandas as pd
import streamlit as st
from player import Player
import numpy as np
from typing import List, Dict, Optional, Union, Tuple

from config import MIN_ACTIONS, SKILL_EVAL_MAPPINGS
from utils import is_team_france_avenir
from team import Team


def build_global_stats_df(players: List[Player]) -> pd.DataFrame:
    """Builds a DataFrame containing global player statistics."""
    rows = []
    labels_map = Player.get_skill_labels(with_percent=True)
    
    # Create global players for France Avenir and other teams
    fa_team_player = Team.create_france_avenir_global_player(players)
    other_team_player = Team.create_other_teams_global_player(players)
    
    # Filter for France Avenir players only
    fa_players = [p for p in players if is_team_france_avenir(p.team)]
    
    def get_player_stats(player: Player, player_name: str) -> Dict[str, Union[str, int, float]]:
        stats = {"Joueur": player_name}
        for skill in SKILL_EVAL_MAPPINGS:
            skill_stats = player.get_skill_stats(skill)
            total = skill_stats.get("Total", 0)
            skill_labels = labels_map.get(skill, [])
            if not skill_labels:
                continue
                
            # For passes, use % Jouable as first column
            first_label = "% Jouable" if skill == "Set" else skill_labels[0]
            last_label = skill_labels[-2]  # e.g. "% Fautes"
                
            col_total = f"n {skill}"
            col_first = f"{skill}_{first_label}"
            col_last = f"{skill}_{last_label}"
            
            stats[col_total] = int(total)
            stats[col_first] = skill_stats.get(first_label, np.nan) if total >= MIN_ACTIONS else np.nan
            stats[col_last] = skill_stats.get(last_label, np.nan) if total >= MIN_ACTIONS else np.nan
        return stats
    
    # Add team statistics first - France Avenir and other teams
    rows.append(get_player_stats(fa_team_player, "ÉQUIPE FRANCE AVENIR"))
    rows.append(get_player_stats(other_team_player, "AUTRES ÉQUIPES"))
    
    # Add individual player statistics for France Avenir
    for p in fa_players:
        rows.append(get_player_stats(p, f"{p.number} – {p.last_name} {p.first_name}"))
    
    return pd.DataFrame(rows).set_index("Joueur")


def style_global_df(df: pd.DataFrame, team_rows: int = 2):
    """Applies styling to the global statistics DataFrame."""
    # Color constants for better readability
    BG_TEAM = 'lightyellow'
    BG_BEST = 'lightgreen'
    BG_WORST = 'salmon'
    COLOR_BEST = 'darkgreen'
    COLOR_WORST = 'darkred'
    COLOR_NEUTRAL = 'black'
    
    labels_map = Player.get_skill_labels(with_percent=True)

    def highlight(col: pd.Series) -> List[str]:
        """Highlights minimum and maximum values in a column."""
        name = col.name
        # Skip non-numeric columns or action total columns
        if col.dtype.kind not in 'biufc' or name.startswith('n '):
            # Still highlight team rows for non-statistical columns
            return [f'background-color: {BG_TEAM}'] * team_rows + [''] * (len(col) - team_rows)
        
        # Determine if this is a negative evaluation column (last one)
        skill, label = name.split('_', 1) if '_' in name else (None, name)
        
        # For passes, check if it's % Jouable or % Erreur column
        if skill == "Set":
            is_last = label == "% Erreur" or label == "% Fautes"
        else:
            is_last = skill in labels_map and label == labels_map[skill][-2]
        
        # Always highlight team rows in yellow
        result = [f'background-color: {BG_TEAM}'] * team_rows
        
        # For all values (including teams), find min/max
        all_values = col.dropna()
        
        if all_values.empty:
            return [''] * len(col)
        
        min_val, max_val = all_values.min(), all_values.max()
        
        # Apply style to all rows
        for i, v in enumerate(col):
            if i < team_rows:
                # Team rows - yellow background with evaluation color overlay
                if pd.isna(v):
                    result[i] = f'background-color: {BG_TEAM}'
                else:
                    # Add evaluation style on top of yellow background
                    if is_last:  # For error columns, invert colors
                        color = COLOR_BEST if v == min_val else COLOR_WORST if v == max_val else COLOR_NEUTRAL
                    else:  # For positive columns
                        color = COLOR_BEST if v == max_val else COLOR_WORST if v == min_val else COLOR_NEUTRAL
                    result[i] = f'background-color: {BG_TEAM}; color: {color}'
            else:
                # Player rows
                if pd.isna(v):
                    result.append('')
                else:
                    # Invert colors for negative evaluations
                    if is_last:
                        result.append(f'background-color: {BG_BEST}' if v == min_val else
                                    f'background-color: {BG_WORST}' if v == max_val else '')
                    else:
                        result.append(f'background-color: {BG_BEST}' if v == max_val else
                                    f'background-color: {BG_WORST}' if v == min_val else '')
        return result

    # Format with 1 decimal for numeric values
    formatter = {col: '{:.1f}' for col in df.select_dtypes(include=['float']).columns}
    
    return df.style.apply(highlight, axis=0).format(formatter, na_rep='-')


def global_stats_tab(players: List[Player]) -> None:
    """Displays the Global Statistics tab for France Avenir team."""
    st.subheader("Statistique globale – Équipe France Avenir")
    st.markdown(f"- Seuil minimal d'actions pour inclusion : {MIN_ACTIONS} ({MIN_ACTIONS} actions)")
    st.markdown("- ""-"" signifie que le joueur n'a pas atteint le seuil minimal d'actions.")
    st.markdown("- Les deux premières lignes (surlignées en jaune) représentent les statistiques globales pour l'équipe France Avenir et les autres équipes.")
    st.markdown("- Le vert indique les meilleures valeurs et le rouge les moins bonnes (couleurs inversées pour les taux d'erreur).")

    df = build_global_stats_df(players)
    if df.empty:
        st.warning("Aucun joueur de France Avenir avec suffisamment d'actions pour afficher des statistiques.")
        return

    # Display team statistics first (always visible)
    team_df = df.iloc[:2]  # First row = France Avenir, Second row = Other teams
    team_styled = style_global_df(team_df, team_rows=2)
    st.dataframe(team_styled, use_container_width=True)
    
    # Then display individual player data for France Avenir
    player_df = df.iloc[2:]  # Skip first 2 rows (teams)
    if not player_df.empty:
        player_styled = style_global_df(player_df, team_rows=0)
        st.dataframe(player_styled, use_container_width=True, height=500)