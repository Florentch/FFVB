import os
import glob
import pandas as pd
import streamlit as st
import re

from player import Player
from datavolley import read_dv
from ui_utils import display_in_area
from filters import (
    create_selector, get_match_selector, player_selector, 
    team_selector, aggregate_team_stats, filter_players_by_criteria
)

@st.cache_data
def load_data():
    """
    Charge les données des fichiers .dvw dans le dossier 'data'
    """
    # Utiliser un chemin absolu basé sur le répertoire de l'application
    app_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(app_dir, 'data')
    file_paths = glob.glob(os.path.join(data_dir, '*.dvw'))
    
    if not file_paths:
        st.error(f"Aucun fichier .dvw trouvé dans le dossier 'data'.")
        return [], pd.DataFrame()

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

    players_df = all_players.drop_duplicates(subset=['player_id']).reset_index(drop=True)

    players = [
        Player(
            id_=row['player_id'],
            first_name=row['name'],
            last_name=row['lastname'],
            number=row['player_number'],
            df=all_plays[all_plays['player_id'] == row['player_id']],
            team = re.sub(r'\d+', '', row.get('team', '')).lower().title()
        )
        for _, row in players_df.iterrows()
    ]

    # Normalisation du nom d'équipe "France Avenir"
    for p in players:
        if (p.team and "france" in p.team.lower() and "avenir" in p.team.lower()) or p.team == "France Avenir 2024":
            p.team = "France Avenir"

    return players, players_df

def is_team_france_avenir(team_name):
    """
    Vérifie si un nom d'équipe correspond à France Avenir avec diverses variations
    """
    if not team_name:
        return False
    team_name = team_name.lower()
    return team_name == "france avenir" or ("france" in team_name and "avenir" in team_name) or team_name == "france avenir 2024"