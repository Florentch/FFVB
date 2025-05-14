import os
import glob
import pandas as pd
import streamlit as st
import re
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
    """
    Charge les données des fichiers .dvw dans le dossier 'data' et crée les objets Player.
    """
    # Utiliser un chemin absolu basé sur le répertoire de l'application
    app_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(app_dir, 'data2')
    file_paths = glob.glob(os.path.join(data_dir, '*.dvw'))
    
    if not file_paths:
        st.error("Aucun fichier .dvw trouvé dans le dossier 'data'.")
        return [], pd.DataFrame()

    # Chargement des fichiers DVW
    all_plays, all_players = _load_dvw_files(file_paths)
    
    # Création des objets Player
    players, players_df = _create_player_objects(all_plays, all_players)
    
    # Normalisation des noms d'équipe
    _normalize_team_names(players)
    
    return players, players_df


def _load_dvw_files(file_paths: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge tous les fichiers DVW et extrait les données de jeu et de joueurs.
    """
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
            st.warning(f"Erreur lors du chargement du fichier {os.path.basename(path)}: {e}")

    # Réindexer all_plays pour avoir un index séquentiel
    all_plays = all_plays.reset_index(drop=True)
    
    return all_plays, all_players


def _create_player_objects(all_plays: pd.DataFrame, all_players: pd.DataFrame) -> Tuple[List[Player], pd.DataFrame]:
    """
    Crée les objets Player à partir des données chargées.
    """
    # Créer un dictionnaire pour stocker les actions par joueur
    players_actions = _index_actions_by_player(all_plays)
    
    # Créer les objets Player
    players_df = all_players.drop_duplicates(subset=['player_id']).reset_index(drop=True)
    players = []
    
    for _, row in players_df.iterrows():
        player_id = row['player_id']
        
        # Récupérer les indices des actions du joueur
        indices = players_actions.get(player_id, [])
        
        # Récupérer les actions du joueur et contextes (avant/après)
        player_actions = all_plays.loc[indices].copy() if indices else pd.DataFrame(columns=all_plays.columns)
        player_actions_prev, player_actions_next = _get_context_actions(indices, all_plays)
        
        # Créer l'objet Player
        player = Player(
            id_=player_id,
            first_name=row['name'],
            last_name=row['lastname'],
            number=row['player_number'],
            df=player_actions,
            df_prev=player_actions_prev,
            df_next=player_actions_next,
            team=re.sub(r'\d+', '', row.get('team', '')).lower().title()
        )
        players.append(player)
    
    return players, players_df


def _index_actions_by_player(all_plays: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Indexe les actions par joueur pour un accès rapide.
    """
    players_actions = {}
    
    for idx, row in all_plays.iterrows():
        player_id = row['player_id']
        if player_id not in players_actions:
            players_actions[player_id] = []
        
        # Stocker l'index de l'action dans all_plays
        players_actions[player_id].append(idx)
    
    return players_actions


def _get_context_actions(indices: List[int], all_plays: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Récupère les actions précédentes et suivantes pour les indices fournis.
    """
    # Créer les DataFrames pour les actions précédentes et suivantes
    player_actions_prev = pd.DataFrame(index=indices, columns=all_plays.columns)
    player_actions_next = pd.DataFrame(index=indices, columns=all_plays.columns)
    
    # Pour chaque indice d'action du joueur, récupérer l'action précédente et suivante
    for idx in indices:
        if idx > 0:  # S'il y a une action précédente
            player_actions_prev.loc[idx] = all_plays.loc[idx - 1]
        
        if idx < len(all_plays) - 1:  # S'il y a une action suivante
            player_actions_next.loc[idx] = all_plays.loc[idx + 1]
    
    return player_actions_prev, player_actions_next


def _normalize_team_names(players: List[Player]) -> None:
    """
    Normalise les noms d'équipe pour assurer la cohérence.
    """
    for p in players:
        if (p.team and is_team_france_avenir(p.team)) or p.team == "France Avenir 2024":
            p.team = "France Avenir"
        elif p.team == 'Ajaccio_':
            p.team = 'Ajaccio'


def is_team_france_avenir(team_name: str) -> bool:
    """
    Vérifie si un nom d'équipe correspond à France Avenir avec diverses variations.
    """
    if not team_name:
        return False
    team_name = team_name.lower()
    return team_name == "france avenir" or ("france" in team_name and "avenir" in team_name)