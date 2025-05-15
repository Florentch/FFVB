import streamlit as st
import pandas as pd
from utils import player_selector, get_match_selector
from constants import MIN_SET
from config import SET_TYPE, ATTACK_TYPE
from ui_utils import display_table_with_title, display_warning_if_empty
from filters import unique_preserve_order, create_selector


def set_tab(players):
    """
    Affiche l'onglet d'analyse des passes
    """
    st.header("🏐 Analyse des passes")
    
    # Filtrer les joueurs qui ont fait plus de MIN_SET passes
    passeurs = [p for p in players if len(p.get_action_df("Set")) > MIN_SET]
    
    if display_warning_if_empty(passeurs, f"Aucun joueur avec suffisamment de passes (min. {MIN_SET}) n'a été trouvé."):
        return
    
    # Configuration de l'interface et récupération des sélections
    selected_matches = get_match_selector(passeurs)
    
    if display_warning_if_empty(selected_matches, "⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques."):
        return
    
    # Ajout du sélecteur de joueurs
    selected_passeurs = select_passeurs(passeurs)
    
    if display_warning_if_empty(selected_passeurs, "⚠️ Veuillez sélectionner au moins un passeur pour afficher les statistiques."):
        return
    
    # Récupération des filtres de session
    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)
    
    # Extraire les types de passes et d'attaques disponibles
    all_set_types_codes = get_all_types_from_column(selected_passeurs, "Set", "set_code", selected_matches)
    all_attack_types_codes = get_all_attack_types(selected_passeurs, selected_matches)
    
    # Convertir les codes en noms explicites
    all_set_types_display = [get_display_name(code, SET_TYPE) for code in all_set_types_codes]
    all_attack_types_display = [get_display_name(code, ATTACK_TYPE) for code in all_attack_types_codes]
    
    # Créer les dictionnaires de mapping pour la conversion nom -> code
    set_display_to_code = {get_display_name(code, SET_TYPE): code for code in all_set_types_codes}
    attack_display_to_code = {get_display_name(code, ATTACK_TYPE): code for code in all_attack_types_codes}
    
    # Créer les filtres pour les types de passes et d'attaques
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
    
    # Affichage des statistiques de base avec les nouveaux filtres
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


def select_passeurs(passeurs):
    """
    Crée un sélecteur de passeurs
    """
    # Créer un dictionnaire pour associer les noms complets aux objets joueurs
    passeur_dict = {f"{p.first_name} {p.last_name}": p for p in passeurs}
    all_names = list(passeur_dict.keys())
    
    # Format d'affichage avec équipe
    options = {
        f"{p.first_name} {p.last_name}": f"{(p.team or 'Sans équipe')[:3]} - {p.first_name} {p.last_name}"
        for p in passeurs
    }
    
    # Créer le sélecteur de joueurs
    format_func = lambda x: options.get(x, x)
    selected_names = create_selector(all_names, "passeurs", "selected_passeurs", format_func, 
                                    default_selection=all_names if all_names else [])
    
    # Convertir les noms sélectionnés en objets joueurs
    return [passeur_dict[name] for name in selected_names]


def create_type_selector(type_key, label, display_options, display_to_code_map):
    """
    Crée un sélecteur de type générique (set ou attack)
    """
    # Initialiser la session si nécessaire
    if f'selected_{type_key}_display' not in st.session_state:
        st.session_state[f'selected_{type_key}_display'] = "Tous"
        st.session_state[f'selected_{type_key}'] = "Tous"
        
    selected_display = st.selectbox(
        label,
        ["Tous"] + display_options,
        index=0,
        key=f"{type_key}_selector"
    )
    
    # Convertir l'affichage en code pour traitement interne
    if selected_display == "Tous":
        selected_code = "Tous"
    else:
        selected_code = display_to_code_map.get(selected_display, selected_display)
    
    st.session_state[f'selected_{type_key}_display'] = selected_display
    st.session_state[f'selected_{type_key}'] = selected_code
    
    return selected_code, selected_display


def get_display_name(code, type_dict):
    """
    Convertit un code en nom explicite en utilisant le dictionnaire fourni.
    Si le code n'est pas trouvé, renvoie le code original.
    """
    return type_dict.get(code, code)


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


def display_set_stats(passeurs, selected_matches, moment, set_filter, set_type="Tous", 
                     attack_type="Tous", set_type_display=None, attack_type_display=None):
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
    
    # Construction du titre avec description des filtres
    title = "Statistiques "
    filter_parts = []
    
    if set_type != "Tous":
        set_name = set_type_display if set_type_display else f"Type de passe: {set_type}"
        filter_parts.append(f"Type de passe: {set_name}")
    if attack_type != "Tous":
        attack_name = attack_type_display if attack_type_display else f"Type d'attaque: {attack_type}"
        filter_parts.append(f"Type d'attaque: {attack_name}")
    
    if filter_parts:
        title += f"filtrées ({', '.join(filter_parts)})"
    else:
        title += "globales"
    
    # Création et affichage du DataFrame
    if data:
        df = pd.DataFrame(data)
        display_table_with_title(title, df.set_index("Nom"), use_container_width=True)
    else:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")