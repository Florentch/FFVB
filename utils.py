import os
import glob
import pandas as pd
import streamlit as st
import re

from player import Player
from datavolley import read_dv

@st.cache_data
def load_data():
    # Modification pour gérer correctement les chemins sur Streamlit Cloud
    # Utiliser un chemin absolu basé sur le répertoire de l'application
    app_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(app_dir, 'data')
    file_paths = glob.glob(os.path.join(data_dir, '*.dvw'))
    
    # Ajouter un log pour déboguer
    st.write(f"Recherche dans: {data_dir}")
    st.write(f"Fichiers trouvés: {len(file_paths)}")
    
    if not file_paths:
        st.error(f"Aucun fichier .dvw trouvé dans le dossier '{data_dir}'.")
        return [], pd.DataFrame()

    all_plays, all_players = pd.DataFrame(), pd.DataFrame()

    for path in file_paths:
        try:
            st.write(f"Traitement du fichier: {os.path.basename(path)}")
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

    return players, players_df

def unique_preserve_order(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

SKILL_TABS = {
    "Réception": {"skill": "Reception", "label": "réceptions"},
    "Block": {"skill": "Block", "label": "blocks"},
    "Service": {"skill": "Serve", "label": "service"},
    "Défense": {"skill": "Dig", "label": "défense"},
    "Attaque": {"skill": "Attack", "label": "attaque"},
}

def player_selector(players, skill, moment, selected_matches, set_filter=None):
    """
    Affiche un sélecteur de joueurs amélioré avec options de tri par équipe
    et option de sélection rapide (tous/aucun).
    
    Args:
        players: Liste des objets Player
        skill: Compétence à analyser
        moment: Moment du match à filtrer
        selected_matches: Liste des matchs sélectionnés
        set_filter: Filtre optionnel sur les sets

    Returns:
        Les statistiques formatées pour affichage
    """
    # Organiser les joueurs par équipe
    teams = {}
    for p in players:
        if p.team:
            if p.team not in teams:
                teams[p.team] = []
            teams[p.team].append(p)
        else:
            if "Sans équipe" not in teams:
                teams["Sans équipe"] = []
            teams["Sans équipe"].append(p)
    
    # Créer un dictionnaire pour accéder aux joueurs par nom
    player_dict = {f"{p.first_name} {p.last_name}": p for p in players}
    all_names = list(player_dict.keys())
    
    # MODIFICATION: Utiliser directement st.sidebar ou st au lieu de fixed_area
    if st.session_state.get('pin_selections', True):
        # En mode épinglé, utiliser la sidebar
        col1, col2 = st.sidebar.columns([3, 1])
        
        with col2:
            st.write("Options joueurs")
            if st.button("Tous", key="btn_all_players"):
                st.session_state.selected_players = all_names
            if st.button("Aucun", key="btn_no_players"):
                st.session_state.selected_players = []
        
        with col1:
            # Initialiser la variable de session si elle n'existe pas
            if 'selected_players' not in st.session_state:
                st.session_state.selected_players = [all_names[0]] if all_names else []
                
            # CORRECTION: Filtrer la liste pour ne garder que les joueurs valides dans ce contexte
            valid_selected_players = [name for name in st.session_state.selected_players if name in all_names]
            
            # Créer un format pour afficher les joueurs par équipe
            options = {}
            for team_name, team_players in teams.items():
                for p in team_players:
                    player_name = f"{p.first_name} {p.last_name}"
                    options[player_name] = f"{team_name} - {player_name}"
            
            selected_names = st.multiselect(
                "Sélection des joueurs",
                options=all_names,
                format_func=lambda x: options.get(x, x),
                default=valid_selected_players  # Utiliser seulement les joueurs valides comme défaut
            )
            
            # Mettre à jour la session
            st.session_state.selected_players = selected_names
    else:
        # En mode non épinglé, utiliser la zone principale
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.write("Options joueurs")
            if st.button("Tous", key="btn_all_players"):
                st.session_state.selected_players = all_names
            if st.button("Aucun", key="btn_no_players"):
                st.session_state.selected_players = []
        
        with col1:
            # Initialiser la variable de session si elle n'existe pas
            if 'selected_players' not in st.session_state:
                st.session_state.selected_players = []
                
            # CORRECTION: Filtrer la liste pour ne garder que les joueurs valides dans ce contexte
            valid_selected_players = [name for name in st.session_state.selected_players if name in all_names]
            
            # Créer un format pour afficher les joueurs par équipe
            options = {}
            for team_name, team_players in teams.items():
                for p in team_players:
                    player_name = f"{p.first_name} {p.last_name}"
                    options[player_name] = f"{team_name} - {player_name}"
            
            selected_names = st.multiselect(
                "Sélection des joueurs",
                options=all_names,
                format_func=lambda x: options.get(x, x),
                default=valid_selected_players  # Utiliser seulement les joueurs valides comme défaut
            )
            
            # Mettre à jour la session
            st.session_state.selected_players = selected_names
    
    # Si aucun joueur n'est sélectionné, afficher un avertissement
    if not selected_names:
        if st.session_state.get('pin_selections', True):
            st.sidebar.warning("⚠️ Veuillez sélectionner au moins un joueur pour afficher les statistiques.")
        else:
            st.warning("⚠️ Veuillez sélectionner au moins un joueur pour afficher les statistiques.")
        return None
    
    if not selected_matches:
        if st.session_state.get('pin_selections', True):
            st.sidebar.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        else:
            st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return None
    
    # Récupération des statistiques par joueur
    data = []
    for name in selected_names:
        p = player_dict[name]
        stats = p.get_skill_stats(skill, moment, match_filter=selected_matches, set_filter=set_filter)
        if stats["Total"] > 0:
            row = {"Nom": name, "Équipe": p.team or "Sans équipe"}
            row.update(stats)
            data.append(row)
    
    if not data:
        if st.session_state.get('pin_selections', True):
            st.sidebar.info(f"Aucune donnée pour les joueurs et matchs sélectionnés.")
        else:
            st.info(f"Aucune donnée pour les joueurs et matchs sélectionnés.")
        return pd.DataFrame()  # Retourner un DataFrame vide au lieu de None
    
    return pd.DataFrame(data)