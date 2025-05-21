import pandas as pd
import streamlit as st
import numpy as np
from typing import List, Dict, Union, Callable

from constants import MIN_ACTIONS, MAIN_TEAM, KEY_METRICS, SKILL_TRANSLATION
from config import SKILL_EVAL_MAPPINGS, STYLE_CONSTANTS
from utils import is_team_france_avenir
from team import Team
from player import Player
from ui_utils import display_table_with_title, create_expander_section, display_warning_if_empty

def get_stats_row(entity: Union[Player, Team], name: str, labels_map: Dict[str, List[str]]) -> Dict[str, Union[str, int, float]]:
    """Returns a single row of statistics for a player or team."""
    stats = {"Nom": name}
    for skill in SKILL_EVAL_MAPPINGS:
        skill_stats = entity.get_skill_stats(skill)
        total = skill_stats.get("Total", 0)
        skill_labels = labels_map.get(skill, [])
        if not skill_labels:
            continue

        # Use a consistent way to get first and last label based on skill
        first_label = "% Jouable" if skill == "Set" else skill_labels[0]
        last_label = skill_labels[-2]  # Usually the error label

        stats[f"n {skill}"] = int(total)
        stats[f"{skill}_{first_label}"] = skill_stats.get(first_label, np.nan) if total >= MIN_ACTIONS else np.nan
        stats[f"{skill}_{last_label}"] = skill_stats.get(last_label, np.nan) if total >= MIN_ACTIONS else np.nan
    return stats


def build_stats_df(players: List[Player], mode: str) -> pd.DataFrame:
    """Builds a DataFrame of stats for players (mode='players') or teams (mode='teams')."""
    labels_map = Player.get_skill_labels(with_percent=True)
    rows = []

    if mode == "players":
        fa_team_player = Team.create_france_avenir_global_player(players)
        other_team_player = Team.create_other_teams_global_player(players)
        fa_players = [p for p in players if is_team_france_avenir(p.team)]

        rows.append(get_stats_row(fa_team_player, f"ÉQUIPE {MAIN_TEAM}", labels_map))
        rows.append(get_stats_row(other_team_player, "AUTRES ÉQUIPES", labels_map))

        for p in fa_players:
            rows.append(get_stats_row(p, f"{p.number} – {p.last_name} {p.first_name}", labels_map))

        return pd.DataFrame(rows).set_index("Nom") if rows else pd.DataFrame()

    elif mode == "teams":
        team_players = Team.create_all_team_global_players(players)
        for tp in team_players:
            if tp:
                rows.append(get_stats_row(tp, tp.team, labels_map))
        return pd.DataFrame(rows).set_index("Nom") if rows else pd.DataFrame()

    else:
        raise ValueError("Invalid mode. Choose 'players' or 'teams'.")


def should_highlight_best_when_high(skill: str, label: str, labels_map: Dict[str, List[str]]) -> bool:
    """Determines whether high values are good (True) or bad (False) for a metric."""
    if "Erreur" in label or "Faute" in label or "reçu" in label or "out" in label or "Non defendu" in label:
        return False # For error metrics, low values are better
    
    return True # For most other metrics, high values are better


def style_stats_df(df: pd.DataFrame, highlight_team_rows: int = 0):
    """Applies highlight styling to the DataFrame (player or team)."""
    labels_map = Player.get_skill_labels(with_percent=True)

    def highlight(col: pd.Series) -> List[str]:
        name = col.name
        if col.dtype.kind not in 'biufc' or name.startswith('n '):
            return [f'background-color: {STYLE_CONSTANTS["BG_TEAM"]}'] * highlight_team_rows + [''] * (len(col) - highlight_team_rows)

        skill, label = name.split('_', 1) if '_' in name else (None, name)
        higher_is_better = should_highlight_best_when_high(skill, label, labels_map)

        all_values = col.dropna()
        if all_values.empty:
            return [''] * len(col)

        min_val, max_val = all_values.min(), all_values.max()
        result = []

        for i, v in enumerate(col):
            base = ''
            if i < highlight_team_rows:
                base = f'background-color: {STYLE_CONSTANTS["BG_TEAM"]}; '
            if pd.isna(v):
                result.append(base.strip())
                continue

            if higher_is_better:
                color = STYLE_CONSTANTS["COLOR_BEST"] if v == max_val else STYLE_CONSTANTS["COLOR_WORST"] if v == min_val else STYLE_CONSTANTS["COLOR_NEUTRAL"]
                bg = STYLE_CONSTANTS["BG_BEST"] if v == max_val else STYLE_CONSTANTS["BG_WORST"] if v == min_val else ""
            else:
                color = STYLE_CONSTANTS["COLOR_BEST"] if v == min_val else STYLE_CONSTANTS["COLOR_WORST"] if v == max_val else STYLE_CONSTANTS["COLOR_NEUTRAL"]
                bg = STYLE_CONSTANTS["BG_BEST"] if v == min_val else STYLE_CONSTANTS["BG_WORST"] if v == max_val else ""

            if highlight_team_rows and i < highlight_team_rows:
                result.append(f'{base}color: {color}')
            else:
                result.append(f'background-color: {bg}')
        return result

    formatter = {col: '{:.1f}' for col in df.select_dtypes(include=['float']).columns}
    return df.style.apply(highlight, axis=0).format(formatter, na_rep='-')


def display_stats_section(title: str, df: pd.DataFrame, highlight_rows: int = 0, help_text: List[str] = None):
    """Display a section with stats and optional help text."""
    st.subheader(title)
    
    if help_text:
        for text in help_text:
            st.markdown(f"- {text}")

    if display_warning_if_empty(df, f"Aucune donnée disponible pour {title.lower()}."):
        return

    styled_df = style_stats_df(df, highlight_team_rows=highlight_rows)
    height = 500 if len(df) > 10 else None
    st.dataframe(styled_df, use_container_width=True, height=height)


def global_stats_tab(players: List[Player]) -> None:
    """Displays both the CNVB and team global statistics."""
    common_help = [
        f"Seuil minimal d'actions pour inclusion : {MIN_ACTIONS} actions.",
        "\"-\" signifie que le joueur n'a pas atteint le seuil minimal."
    ]

    player_help = common_help + [
        f"Les deux premières lignes (jaunes) sont les moyennes de l'équipe {MAIN_TEAM} et des autres équipes.",
        "Le vert indique la meilleure valeur, le rouge la moins bonne (inversé pour les taux d'erreur)."
    ]
    
    df_players = build_stats_df(players, mode="players")
    
    if not df_players.empty:
        team_df = df_players.iloc[:2]
        player_df = df_players.iloc[2:]

        display_stats_section(
            f"Statistique globale – Équipe {MAIN_TEAM}", 
            team_df, 
            highlight_rows=2, 
            help_text=player_help
        )

        if not player_df.empty:
            def show_player_details():
                st.dataframe(style_stats_df(player_df), use_container_width=True, height=500)
            
            create_expander_section(
                f"Détails par joueur ({MAIN_TEAM})", 
                show_player_details,
                expanded=True
            )
    else:
        st.warning(f"Aucune donnée pour les joueurs {MAIN_TEAM}.")
    
    team_help = common_help + [
        "Chaque ligne correspond à une équipe.",
        "Meilleurs en vert, moins bons en rouge (inversé pour erreurs)."
    ]

    df_teams = build_stats_df(players, mode="teams")
    display_stats_section(
        "Statistique globale – Par équipe", 
        df_teams, 
        help_text=team_help
    )