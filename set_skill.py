import streamlit as st
import pandas as pd
from utils import player_selector, get_match_selector
from constants import MIN_SET


def set_tab(players):
    """
    Affiche l'onglet d'analyse des passes
    """
    st.header("🏐 Analyse des passes")
    
    # Filtrer les joueurs qui ont fait plus de MIN_SET passes
    passeurs = [p for p in players if len(p.get_action_df("Set")) > MIN_SET]
    
    if not passeurs:
        st.warning(f"Aucun joueur avec suffisamment de passes (min. {MIN_SET}) n'a été trouvé.")
        return
    
    # Configuration de l'interface et récupération des sélections
    selected_matches = get_match_selector(passeurs)
    
    if not selected_matches:
        st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return
    
    # Récupération des filtres de session
    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)
    
    # Extraire les types de passes et d'attaques disponibles
    all_set_types = get_all_set_types(passeurs, selected_matches)
    all_attack_types = get_all_attack_types(passeurs, selected_matches)
    
    # Créer les filtres pour les types de passes et d'attaques
    col1, col2 = st.columns(2)
    
    with col1:
        # Initialiser la session si nécessaire
        if 'selected_set_type' not in st.session_state:
            st.session_state['selected_set_type'] = "Tous"
            
        selected_set_type = st.selectbox(
            "Type de passe",
            ["Tous"] + all_set_types,
            index=0,
            key="set_type_selector"
        )
        st.session_state['selected_set_type'] = selected_set_type
    
    with col2:
        # Initialiser la session si nécessaire
        if 'selected_attack_type' not in st.session_state:
            st.session_state['selected_attack_type'] = "Tous"
            
        selected_attack_type = st.selectbox(
            "Type d'attaque",
            ["Tous"] + all_attack_types,
            index=0,
            key="attack_type_selector"
        )
        st.session_state['selected_attack_type'] = selected_attack_type
    
    # Affichage des statistiques de base avec les nouveaux filtres
    display_set_stats(
        passeurs, 
        selected_matches, 
        moment, 
        set_filter, 
        selected_set_type, 
        selected_attack_type
    )


def get_all_types_from_column(players, action_type, column_name, match_filter=None):
    """
    Récupère tous les types disponibles depuis une colonne donnée
    """
    types = set()
    for player in players:
        df = player.get_action_df(action_type, match_filter=match_filter)
        if column_name in df.columns:
            unique_types = df[column_name].dropna().unique()
            types.update(unique_types)
    return sorted(list(types))


def get_all_set_types(players, match_filter=None):
    """
    Récupère tous les types de passes disponibles
    """
    return get_all_types_from_column(players, "Set", "set_code", match_filter)


def get_all_attack_types(players, match_filter=None):
    """
    Récupère tous les types d'attaques disponibles
    """
    attack_types = set()
    for player in players:
        # Obtenir les actions de type "Set"
        set_df = player.get_action_df("Set", match_filter=match_filter)
        if set_df.empty or player.df_next is None:
            continue
        
        # Pour chaque passe, vérifier si l'action suivante est une attaque
        for idx in set_df.index:
            if idx in player.df_next.index:
                next_action = player.df_next.loc[idx]
                if next_action['skill'] == 'Attack' and 'attack_code' in next_action:
                    attack_code = next_action['attack_code']
                    if pd.notna(attack_code):
                        attack_types.add(attack_code)
    
    return sorted(list(attack_types))


def calculate_stats_row(passeur, stats):
    """
    Calcule les statistiques pour un passeur
    """
    # Si aucune passe dans les filtres sélectionnés, retourner None
    if stats["Total"] <= 0:
        return None
        
    # Calcul du % Jouable (sommation des passes non-fautes)
    jouable_keys = ["Parfaite", "Bonne", "Ok", "Mauvaise", "Nulle"]
    jouable_count = sum(stats.get(key, 0) for key in jouable_keys)
    percent_jouable = round((jouable_count / stats["Total"]) * 100, 1)
    
    # Calcul du % Faute
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


def display_set_stats(passeurs, selected_matches, moment, set_filter, set_type="Tous", attack_type="Tous"):
    """
    Affiche les statistiques de base des passeurs avec filtres supplémentaires
    """
    # Préparation du DataFrame avec les statistiques de passes
    data = []
    
    for passeur in passeurs:
        # Obtenir les statistiques filtrées
        stats = passeur.get_skill_stats_with_filters(
            "Set", 
            moment, 
            selected_matches, 
            set_filter, 
            set_type, 
            attack_type
        )
        
        # Calcul et ajout des statistiques du joueur
        row = calculate_stats_row(passeur, stats)
        if row:
            data.append(row)
    
    # Création et affichage du DataFrame
    if data:
        df = pd.DataFrame(data)
        
        # Construction du titre avec description des filtres
        title = "Statistiques "
        filter_parts = []
        
        if set_type != "Tous":
            filter_parts.append(f"Type de passe: {set_type}")
        if attack_type != "Tous":
            filter_parts.append(f"Type d'attaque: {attack_type}")
        
        if filter_parts:
            title += f"filtrées ({', '.join(filter_parts)})"
        else:
            title += "globales"
            
        st.subheader(title)
        st.dataframe(df.set_index("Nom"), use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")