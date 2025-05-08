import os
import glob
import pandas as pd
import streamlit as st
import re

from player import Player
from datavolley import read_dv

# Fonction utilitaire pour afficher des éléments UI dans la zone appropriée (sidebar ou main)
def display_in_area(element_function, *args, **kwargs):
    """
    Affiche un élément UI dans la zone appropriée (sidebar ou main) selon le mode d'épinglage
    
    Args:
        element_function: La fonction à appeler (st.selectbox, st.multiselect, etc.)
        *args, **kwargs: Les arguments à passer à la fonction
        
    Returns:
        Le résultat de la fonction d'UI appelée
    """
    # Déterminer si on utilise la sidebar ou la zone principale
    area = st.sidebar if st.session_state.get('pin_selections', True) else st
    
    # Appeler la fonction avec l'objet approprié
    return getattr(area, element_function.__name__)(*args, **kwargs)

@st.cache_data
def load_data():
    """
    Charge les données des fichiers .dvw dans le dossier 'data'
    
    Returns:
        tuple: Liste des joueurs, DataFrame des joueurs
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

# Simplifier la fonction unique_preserve_order
def unique_preserve_order(seq):
    """Retourne une liste sans doublons tout en préservant l'ordre des éléments"""
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def get_match_selector(players, selected_matches=None):
    """
    Crée un sélecteur de matchs avec options rapides
    
    Args:
        players: Liste des objets Player
        selected_matches: Liste des matchs déjà sélectionnés
        
    Returns:
        Liste des matchs sélectionnés
    """
    # Récupération des données de match avec date
    match_data, match_ids_set = [], set()
    for p in players:
        for match_id in p.df['match_id'].dropna().unique():
            if match_id in match_ids_set:
                continue
            match_ids_set.add(match_id)
            match_rows = p.df[p.df['match_id'] == match_id]
            if len(match_rows) > 0:
                row = match_rows.iloc[0]
                match_day = row.get('match_day', '')
                match_data.append({
                    'match_id': match_id,
                    'match_day': match_day,
                    'match_label': f"{row.get('home_team', 'Équipe A')[0:3]} vs {row.get('visiting_team', 'Équipe B')[0:3]} - {match_day}"
                })

    # Trier les matchs par date si possible
    match_df = pd.DataFrame(match_data)
    if not match_df.empty and 'match_day' in match_df.columns:
        try:
            # Convertir les dates au format DD/MM/YYYY en datetime pour le tri
            match_df['date_for_sort'] = pd.to_datetime(match_df['match_day'], format='%d/%m/%Y', errors='coerce')
            match_df = match_df.sort_values(by='date_for_sort', ascending=False)
        except Exception as e:
            print(f"Erreur de tri des dates: {e}")
            pass  # Si le tri échoue, on garde l'ordre d'origine
    
    match_ids = list(match_df['match_id'].unique())
    match_labels = match_df.set_index('match_id')['match_label'].to_dict()
    
    # Initialiser la variable de session si elle n'existe pas
    if 'selected_matches' not in st.session_state:
        st.session_state.selected_matches = match_ids if selected_matches is None else selected_matches
    
    # Créer les colonnes appropriées
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    col1, col2 = area.columns([3, 1])
    
    with col2:
        area.write("Options rapides")
        if area.button("Tous", key="btn_all_matches"):
            st.session_state.selected_matches = match_ids
    
    with col1:
        selected_matches = area.multiselect(
            "Filtrer par match", 
            options=match_ids,
            format_func=lambda x: match_labels.get(x, str(x)),
            default=st.session_state.selected_matches
        )
        # Mettre à jour la session
        st.session_state.selected_matches = selected_matches
    
    return selected_matches

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
        team_name = p.team or "Sans équipe"
        if team_name not in teams:
            teams[team_name] = []
        teams[team_name].append(p)
    
    # Créer un dictionnaire pour accéder aux joueurs par nom
    player_dict = {f"{p.first_name} {p.last_name}": p for p in players}
    all_names = list(player_dict.keys())
    
    # Déterminer la zone d'affichage
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    col1, col2 = area.columns([3, 1])

    with col2:
        area.write("Options joueurs")
        if area.button("Tous", key="btn_all_players"):
            st.session_state.selected_players = all_names
            
    with col1:
        # Initialiser la variable de session si elle n'existe pas
        if 'selected_players' not in st.session_state:
            st.session_state.selected_players = all_names[0:3] if all_names else []
                
        # Filtrer la liste pour ne garder que les joueurs valides dans ce contexte
        valid_selected_players = [name for name in st.session_state.selected_players if name in all_names]
            
        # Créer un format pour afficher les joueurs par équipe
        options = {}
        for team_name, team_players in teams.items():
            for p in team_players:
                player_name = f"{p.first_name} {p.last_name}"
                options[player_name] = f"{team_name[0:3]} - {player_name}"
            
        selected_names = area.multiselect(
            "Sélection des joueurs",
            options=all_names,
            format_func=lambda x: options.get(x, x),
            default=valid_selected_players
        )
            
        # Mettre à jour la session
        st.session_state.selected_players = selected_names
    
    # Si aucun joueur n'est sélectionné, afficher un avertissement
    if not selected_names:
        area.warning("⚠️ Veuillez sélectionner au moins un joueur pour afficher les statistiques.")
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
        area.info(f"Aucune donnée pour les joueurs et matchs sélectionnés.")
        return pd.DataFrame()  # Retourner un DataFrame vide
    
    return pd.DataFrame(data)

def team_selector(players, skill, moment, selected_matches, set_filter=None):
    """
    Affiche un sélecteur d'équipes amélioré avec options de sélection rapide
    
    Args:
        players: Liste des objets Player
        skill: Compétence à analyser
        moment: Moment du match à filtrer
        selected_matches: Liste des matchs sélectionnés
        set_filter: Filtre optionnel sur les sets

    Returns:
        Les statistiques par équipe formatées pour affichage
    """
    # Récupérer toutes les équipes uniques
    teams = unique_preserve_order([p.team for p in players if p.team])
    
    # Déterminer la zone d'affichage
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    col1, col2 = area.columns([3, 1])

    with col2:
        area.write("Options équipes")
        if area.button("Toutes", key="btn_all_teams"):
            st.session_state.selected_teams = teams
            
    with col1:
        # Initialiser la variable de session si elle n'existe pas
        if 'selected_teams' not in st.session_state:
            st.session_state.selected_teams = teams
                
        # Filtrer la liste pour ne garder que les équipes valides
        valid_selected_teams = [team for team in st.session_state.selected_teams if team in teams]
            
        selected_teams = area.multiselect(
            "Sélection des équipes",
            options=teams,
            default=valid_selected_teams
        )
            
        # Mettre à jour la session
        st.session_state.selected_teams = selected_teams
    
    # Si aucune équipe n'est sélectionnée, afficher un avertissement
    if not selected_teams:
        area.warning("⚠️ Veuillez sélectionner au moins une équipe pour afficher les statistiques.")
        return None
    
    # Filtrer les joueurs par équipe
    filtered_players = [p for p in players if p.team in selected_teams]
    
    # Aggrégation des statistiques par équipe
    team_stats = {}
    for team in selected_teams:
        team_players = [p for p in filtered_players if p.team == team]
        team_stats[team] = aggregate_team_stats(team_players, skill, moment, selected_matches, set_filter)
    
    # Convertir en DataFrame pour l'affichage
    data = []
    for team, stats in team_stats.items():
        if stats["Total"] > 0:
            row = {"Équipe": team, "Nbre Total": stats["Total"]}
            for category in stats:
                if category != "Total":
                    row[f"% {category}"] = round(stats[category] / stats["Total"] * 100, 1)
            data.append(row)
    
    if not data:
        area.info(f"Aucune donnée pour les équipes et matchs sélectionnés.")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def aggregate_team_stats(players, skill, moment, match_filter, set_filter=None):
    """
    Aggrège les statistiques de tous les joueurs d'une équipe
    
    Args:
        players: Liste des joueurs de l'équipe
        skill: Compétence à analyser
        moment: Moment du match à filtrer
        match_filter: Liste des matchs à inclure
        set_filter: Filtre optionnel sur les sets
        
    Returns:
        Dictionnaire contenant les statistiques agrégées
    """
    # Récupérer les catégories pour cette compétence
    categories = set()
    for p in players:
        stats = p.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)
        categories.update([k for k in stats.keys() if k != "Total"])
    
    # Initialiser le dictionnaire des stats d'équipe
    team_stats = {k: 0 for k in list(categories) + ["Total"]}
    
    # Agréger les statistiques de tous les joueurs
    for p in players:
        stats = p.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)
        for k, v in stats.items():
            team_stats[k] += v
    
    return team_stats