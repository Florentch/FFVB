import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Union, Tuple

from utils import player_selector, get_match_selector
from constants import MIN_SET
from config import SET_TYPE, ATTACK_TYPE
from ui_utils import display_table_with_title, display_warning_if_empty
from filters import (unique_preserve_order, create_selector, get_all_codes_from_column, 
    get_display_name_from_mapping, get_all_attack_codes_from_next_actions, create_type_filter_selector)
from player import Player


def set_tab(players: List[Player]) -> None:
    """Displays the pass analysis tab."""
    st.header("Analyse des passes")
    
    passeurs = [p for p in players if len(p.get_action_df("Set")) > MIN_SET]
    
    if display_warning_if_empty(passeurs, f"Aucun joueur avec suffisamment de passes (min. {MIN_SET}) n'a été trouvé."):
        return
    
    selected_matches = get_match_selector(passeurs)
    
    if display_warning_if_empty(selected_matches, "⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques."):
        return
    
    selected_passeurs = select_passeurs(passeurs)
    
    if display_warning_if_empty(selected_passeurs, "⚠️ Veuillez sélectionner au moins un passeur pour afficher les statistiques."):
        return
    
    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)
    
    all_set_types_codes = get_all_types_from_column(selected_passeurs, "Set", "set_code", selected_matches)
    all_attack_types_codes = get_all_attack_types(selected_passeurs, selected_matches)
    
    all_set_types_display = [get_display_name(code, SET_TYPE) for code in all_set_types_codes]
    all_attack_types_display = [get_display_name(code, ATTACK_TYPE) for code in all_attack_types_codes]
    
    set_display_to_code = {get_display_name(code, SET_TYPE): code for code in all_set_types_codes}
    attack_display_to_code = {get_display_name(code, ATTACK_TYPE): code for code in all_attack_types_codes}
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_set_type, selected_set_type_display = create_type_selector(
            "set_type", 
            "Type de passe",
            all_set_types_display,
            set_display_to_code
        )
    
    with col2:
        selected_attack_type, selected_attack_type_display = create_type_selector(
            "attack_type", 
            "Type d'attaque",
            all_attack_types_display,
            attack_display_to_code
        )
    
    display_set_stats(
        selected_passeurs, 
        selected_matches, 
        moment, 
        set_filter, 
        selected_set_type, 
        selected_attack_type,
        selected_set_type_display if selected_set_type_display != "Tous" else None,
        selected_attack_type_display if selected_attack_type_display != "Tous" else None
    )


def select_passeurs(passeurs: List[Player]) -> List[Player]:
    """Creates a setter selector."""
    passeur_dict = {f"{p.first_name} {p.last_name}": p for p in passeurs}
    all_names = list(passeur_dict.keys())
    
    options = {
        f"{p.first_name} {p.last_name}": f"{(p.team or 'Sans équipe')[:3]} - {p.first_name} {p.last_name}"
        for p in passeurs
    }
    
    format_func = lambda x: options.get(x, x)
    selected_names = create_selector(all_names, "passeurs", "selected_passeurs", format_func, 
                                    default_selection=all_names if all_names else [])
    
    return [passeur_dict[name] for name in selected_names]

def get_display_name(code: str, type_dict: dict) -> str:
    """Converts a code to an explicit name using the provided dictionary."""
    return get_display_name_from_mapping(code, type_dict)


def get_all_types_from_column(players: list, action_type: str, column_name: str, match_filter: list = None) -> list:
    """Retrieves all available types from a given column."""
    return get_all_codes_from_column(players, action_type, column_name, match_filter)


def get_all_attack_types(players: list, match_filter: list = None) -> list:
    """Retrieves all available attack types."""
    return get_all_attack_codes_from_next_actions(players, match_filter)


def create_type_selector(type_key: str, label: str, display_options: list, display_to_code_map: dict): 
    """Creates a generic type selector (set or attack)."""
    return create_type_filter_selector(type_key, label, display_options, display_to_code_map)


def calculate_stats_row(passeur: Player, stats: Dict[str, Union[int, float]]) -> Optional[Dict[str, Union[str, int, float]]]: 
    """Calculates statistics for a setter."""
    if stats["Total"] <= 0:
        return None
        
    jouable_keys = ["Parfaite", "Bonne", "Ok", "Mauvaise", "Nulle"]
    jouable_count = sum(stats.get(key, 0) for key in jouable_keys)
    percent_jouable = round((jouable_count / stats["Total"]) * 100, 1)
    
    faute_count = stats.get("Faute", 0)
    percent_faute = round((faute_count / stats["Total"]) * 100, 1)
    
    return {
        "Nom": passeur.get_display_name(),
        "Total": stats["Total"],
        "Jouable": jouable_count,
        "Faute": faute_count,
        "% Jouable": percent_jouable,
        "% Faute": percent_faute,
        "% FSO": stats.get("% FSO", 0),
        "% SO": stats.get("% SO", 0)
    }


def display_set_stats(passeurs: List[Player], selected_matches: List[str], moment: str, set_filter: Optional[str], 
                     set_type: str = "Tous", attack_type: str = "Tous", 
                     set_type_display: Optional[str] = None, attack_type_display: Optional[str] = None) -> None: 
    """Displays basic statistics of setters with additional filters."""
    data = []
    
    for passeur in passeurs:
        stats = passeur.get_skill_stats_with_filters(
            "Set", 
            moment, 
            selected_matches, 
            set_filter, 
            set_type, 
            attack_type
        )
        
        row = calculate_stats_row(passeur, stats)
        if row:
            data.append(row)
    
    title = "Statistiques "
    filter_parts = []
    
    if set_type != "Tous":
        set_name = set_type_display if set_type_display else f"Type de passe: {set_type}"
        filter_parts.append(f"Type de passe: {set_name}")
    if attack_type != "Tous":
        attack_name = attack_type_display if attack_type_display else f"Type d'attaque: {attack_type}"
        filter_parts.append(f"Type d'attaque: {attack_name}")
    
    title += f"filtrées ({', '.join(filter_parts)})" if filter_parts else "globales"
    
    if data:
        df = pd.DataFrame(data)
        display_table_with_title(title, df.set_index("Nom"), use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")