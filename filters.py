import streamlit as st
import pandas as pd
from datetime import datetime

def unique_preserve_order(seq):
    """Retourne une liste sans doublons tout en préservant l'ordre des éléments"""
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def create_selector(items, title, session_key, format_func=None, default_selection=None):
    """
    Crée un sélecteur générique avec options de sélection rapide
    """
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    col1, col2 = area.columns([3, 1])
    
    # Gestion du bouton "Tous"
    with col2:
        area.write(f"Options {title}")
        if area.button("Tous", key=f"btn_all_{session_key}"):
            st.session_state[session_key] = items
    
    # Gestion du sélecteur
    with col1:
        # Initialiser la variable de session si nécessaire
        if session_key not in st.session_state:
            default_selection = items[:3] if len(items) > 3 else items if default_selection is None else default_selection
            st.session_state[session_key] = default_selection
        
        # Filtrer pour ne garder que les éléments valides
        valid_selected = [item for item in st.session_state[session_key] if item in items]
        
        # Créer le sélecteur
        format_func = format_func if format_func else lambda x: x
        selected = area.multiselect(
            f"Sélection des {title}",
            options=items,
            format_func=format_func,
            default=valid_selected
        )
        
        # Mettre à jour la session
        st.session_state[session_key] = selected
    
    # Avertissement si aucune sélection
    if not selected:
        area.warning(f"⚠️ Veuillez sélectionner au moins un(e) {title.lower()} pour afficher les statistiques.")
    
    return selected

def get_match_data(players):
    """
    Récupère et trie les données de match à partir des joueurs
    """
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
                home_team = row.get('home_team', 'Équipe A')[:3]
                visiting_team = row.get('visiting_team', 'Équipe B')[:3]
                
                match_data.append({
                    'match_id': match_id,
                    'match_day': match_day,
                    'match_label': f"{home_team} vs {visiting_team} - {match_day}"
                })
    
    # Trier les matchs par date si possible
    match_df = pd.DataFrame(match_data)
    if not match_df.empty and 'match_day' in match_df.columns:
        try:
            match_df['date_for_sort'] = pd.to_datetime(match_df['match_day'], format='%d/%m/%Y', errors='coerce')
            match_df = match_df.sort_values(by='date_for_sort', ascending=False)
        except Exception as e:
            print(f"Erreur de tri des dates: {e}")
    
    return match_df

def get_match_selector(players, selected_matches=None):
    """
    Crée un sélecteur de matchs avec options rapides
    """
    # Récupération des données de match triées
    match_df = get_match_data(players)
    match_ids = list(match_df['match_id'].unique())
    match_labels = match_df.set_index('match_id')['match_label'].to_dict()
    
    # Initialiser la session si nécessaire
    if 'selected_matches' not in st.session_state:
        st.session_state.selected_matches = match_ids if selected_matches is None else selected_matches
    
    # Créer le sélecteur
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
        st.session_state.selected_matches = selected_matches
    
    return selected_matches

def player_selector(players, skill, moment, selected_matches, set_filter=None):
    """
    Affiche un sélecteur de joueurs amélioré avec options de tri par équipe
    """
    # Organiser les joueurs par équipe
    teams = {}
    for p in players:
        team_name = p.team or "Sans équipe"
        if team_name not in teams:
            teams[team_name] = []
        teams[team_name].append(p)
    
    # Dictionnaire pour accéder aux joueurs par nom
    player_dict = {f"{p.first_name} {p.last_name}": p for p in players}
    all_names = list(player_dict.keys())
    
    # Format d'affichage par équipe
    options = {
        f"{p.first_name} {p.last_name}": f"{(p.team or 'Sans équipe')[:3]} - {p.first_name} {p.last_name}"
        for p in players
    }
    
    # Créer le sélecteur de joueurs
    format_func = lambda x: options.get(x, x)
    selected_names = create_selector(all_names, "joueurs", "selected_players", format_func, 
                                     default_selection=all_names[:3] if all_names else [])
    
    if not selected_names:
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
        is_pinned = st.session_state.get('pin_selections', True)
        area = st.sidebar if is_pinned else st
        area.info(f"Aucune donnée pour les joueurs et matchs sélectionnés.")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def aggregate_team_stats(players, skill, moment, match_filter, set_filter=None):
    """
    Aggrège les statistiques de tous les joueurs d'une équipe
    """
    # Récupérer toutes les catégories possibles pour cette compétence
    categories = set()
    for p in players:
        stats = p.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)
        categories.update([k for k in stats.keys() if k != "Total"])
    
    # Initialiser le dictionnaire de statistiques d'équipe
    team_stats = {k: 0 for k in list(categories) + ["Total"]}
    
    # Agréger les statistiques de tous les joueurs
    for p in players:
        stats = p.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)
        for k, v in stats.items():
            team_stats[k] += v
    
    return team_stats

def team_selector(players, skill, moment, selected_matches, set_filter=None):
    """
    Affiche un sélecteur d'équipes avec options de sélection rapide
    """
    teams = unique_preserve_order([p.team for p in players if p.team])
    
    # Créer le sélecteur d'équipes
    selected_teams = create_selector(teams, "équipes", "selected_teams", default_selection=teams)
    
    if not selected_teams:
        return None
    
    # Filtrer les joueurs par équipe
    filtered_players = [p for p in players if p.team in selected_teams]
    
    # Aggrégation des statistiques par équipe
    data = []
    for team in selected_teams:
        team_players = [p for p in filtered_players if p.team == team]
        stats = aggregate_team_stats(team_players, skill, moment, selected_matches, set_filter)
        
        if stats["Total"] > 0:
            row = {"Équipe": team, "Nbre Total": stats["Total"]}
            
            # Ajouter les pourcentages
            for category, value in stats.items():
                if category != "Total":
                    key = category if category.startswith("% ") else f"% {category}"
                    row[key] = round(value / stats["Total"] * 100, 1)
            data.append(row)
    
    if not data:
        is_pinned = st.session_state.get('pin_selections', True)
        area = st.sidebar if is_pinned else st
        area.info(f"Aucune donnée pour les équipes et matchs sélectionnés.")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def filter_players_by_criteria(players, min_actions=5, skill=None):
    """
    Filtre les joueurs selon différents critères
    """
    if skill:
        return [p for p in players if len(p.get_action_df(skill)) > min_actions]
        
    # Filtrer sur toutes les compétences principales
    all_skills = ['Reception', 'Block', 'Serve', 'Attack', 'Dig']
    return [p for p in players if sum(len(p.get_action_df(s)) for s in all_skills) > min_actions]

def filter_players_with_data(players, match_filter=None, skill=None, min_actions=4):
    """
    Filtre les joueurs qui ont suffisamment de données pour l'analyse.
    """
    if skill is None:
        # Si aucune compétence n'est spécifiée, retourner tous les joueurs
        return players
    
    # Filtrer les joueurs par compétence et nombre minimum d'actions
    if match_filter:
        return [p for p in players if len(p.get_action_df(skill, match_filter=match_filter)) > min_actions]
    else:
        return [p for p in players if len(p.get_action_df(skill)) > min_actions]