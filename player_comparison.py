import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

from player import Player
from filters import (
    get_match_selector, create_selector, unique_preserve_order,
    filter_players_with_data
)
from utils import is_team_france_avenir  # Importation de la fonction de normalisation

def make_comparison_tab(players=None):
    """
    Crée l'onglet de comparaison des joueurs
    
    Args:
        players (list): Liste des objets Player
    """
    st.title("🔍 Comparaison de Joueurs")
    
    # Utiliser les joueurs passés en paramètre ou ceux de la session state si non fournis
    if players is None:
        players = st.session_state.get('players', [])
    
    if not isinstance(players, list) or len(players) == 0:
        st.error("Aucune donnée de joueur disponible.")
        return
    
    # Liste des compétences disponibles
    skills = ["Attack", "Block", "Serve", "Reception", "Dig", "Set"]
    
    # Interface de filtrage
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Filtres")
        
        # Sélection des matchs
        selected_matches = get_match_selector(players)
        
        # Option pour filtrer les sets
        set_filter_options = ["Tous"] + list(range(1, 6))
        set_filter = st.selectbox(
            "Filtrer par set",
            options=set_filter_options,
            format_func=lambda x: x if x == "Tous" else f"Set {x}"
        )
        set_filter = None if set_filter == "Tous" else set_filter
        
        # Options supplémentaires
        moment_filter_options = ["Tout", "0-10", "10-20", "20+"]
        moment_filter = st.selectbox("Phase du set", options=moment_filter_options)
        moment_filter = None if moment_filter == "Tout" else moment_filter
        
        # Sélection des compétences à comparer
        selected_skills = st.multiselect(
            "Compétences à comparer",
            options=skills,
            default=["Attack", "Serve", "Reception"],
            format_func=lambda x: {
                "Attack": "Attaque", "Block": "Bloc", "Serve": "Service",
                "Reception": "Réception", "Dig": "Défense", "Set": "Passe"
            }.get(x, x)
        )
        
        if not selected_skills:
            st.warning("Veuillez sélectionner au moins une compétence.")
            return
    
    # Appliquer les filtres aux joueurs si nécessaire
    # CORRECTION: Passer explicitement None pour le paramètre skill
    filtered_players = filter_players_with_data(players, selected_matches, skill=None)
    
    # Normalisation des noms d'équipe avant de créer le dictionnaire des joueurs
    # Ceci est la clé pour résoudre le problème de duplication
    for p in filtered_players:
        if p.team:
            # Normaliser "France Avenir" avec différentes variantes
            if is_team_france_avenir(p.team):
                p.team = "France Avenir"
            # Nettoyer Ajaccio_ en Ajaccio
            elif p.team == 'Ajaccio_':
                p.team = 'Ajaccio'
    
    # Créer un dictionnaire des joueurs pour accès rapide (seulement ceux avec données valides)
    player_dict = {f"{p.get_full_name()} ({p.team})": p for p in filtered_players if p.team}
    all_player_options = list(player_dict.keys())
    
    # Vérifier s'il y a des joueurs disponibles
    if not all_player_options:
        st.warning("Aucun joueur avec une équipe assignée n'est disponible pour la comparaison.")
        return
    
    # Sélection des joueurs à comparer
    with col2:
        st.subheader("Sélectionner les joueurs à comparer")
        player1_option = st.selectbox(
            "Joueur 1",
            options=all_player_options,
            index=0 if all_player_options else None,
            key="player1_comparison"
        )
        
        # Filtrer le deuxième joueur pour qu'il soit différent du premier
        remaining_options = [p for p in all_player_options if p != player1_option]
        player2_option = st.selectbox(
            "Joueur 2",
            options=remaining_options,
            index=0 if remaining_options else None,
            key="player2_comparison"
        )
        
        if not player1_option or not player2_option:
            st.warning("Veuillez sélectionner deux joueurs différents à comparer.")
            return
        
        player1 = player_dict[player1_option]
        player2 = player_dict[player2_option]
    
    # Afficher les cartes d'information des joueurs
    col1, col2 = st.columns(2)
    with col1:
        display_player_card(player1)
    with col2:
        display_player_card(player2)
    
    # Générer les données de comparaison
    comparison_data = generate_comparison_data(
        player1, player2, selected_skills, moment_filter, selected_matches, set_filter
    )
    
    if not comparison_data:
        st.warning("Pas assez de données pour comparer ces joueurs avec les filtres actuels.")
        return
    
    # Afficher les graphiques de comparaison
    st.subheader("Comparaison détaillée")
    
    # Onglets pour différentes visualisations
    tabs = st.tabs(["Radar", "Barres", "Tableau", "Face à Face"])
    
    with tabs[0]:  # Radar
        display_radar_comparison(comparison_data, player1, player2)
    
    with tabs[1]:  # Barres
        display_bar_comparison(comparison_data, player1, player2, selected_skills)
    
    with tabs[2]:  # Tableau
        display_table_comparison(comparison_data)
    
    with tabs[3]:  # Face à Face
        display_face_to_face_comparison(comparison_data, player1, player2)

def display_player_card(player):
    """
    Affiche une carte d'information sur le joueur
    """
    card_style = """
    <style>
    .player-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
    """
    
    st.markdown(card_style, unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f"<div class='player-card'>", unsafe_allow_html=True)
        st.subheader(f"{player.get_full_name()}")
        st.markdown(f"**Équipe:** {player.team}")
        st.markdown(f"**Numéro:** {player.number}")
        
        # Récupérer quelques statistiques générales
        total_attacks = len(player.get_action_df("Attack"))
        total_serves = len(player.get_action_df("Serve"))
        total_receptions = len(player.get_action_df("Reception"))
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Attaques", total_attacks)
        col2.metric("Services", total_serves)
        col3.metric("Réceptions", total_receptions)
        
        st.markdown("</div>", unsafe_allow_html=True)

def generate_comparison_data(player1, player2, skills, moment, match_filter, set_filter):
    """
    Génère les données de comparaison entre deux joueurs
    """
    comparison_data = {}
    
    for skill in skills:
        # Vérifier si les joueurs ont assez de données pour cette compétence
        player1_actions = len(player1.get_action_df(skill, moment, match_filter, set_filter))
        player2_actions = len(player2.get_action_df(skill, moment, match_filter, set_filter))
        
        if player1_actions < 5 and player2_actions < 5:
            # Passer cette compétence s'il n'y a pas assez de données
            continue
        
        stats1 = player1.get_skill_stats(skill, moment, match_filter, set_filter)
        stats2 = player2.get_skill_stats(skill, moment, match_filter, set_filter)
        
        # Récupérer tous les pourcentages disponibles (en excluant le Total)
        all_keys = set()
        for key in list(stats1.keys()) + list(stats2.keys()):
            if key.startswith("%") or key == "Total":
                all_keys.add(key)
        
        # Fusionner les statistiques des deux joueurs
        skill_data = {
            "skill": skill,
            "player1_name": player1.get_full_name(),
            "player2_name": player2.get_full_name(),
            "player1_team": player1.team,
            "player2_team": player2.team,
            "metrics": {}
        }
        
        for key in all_keys:
            skill_data["metrics"][key] = {
                "player1": stats1.get(key, 0),
                "player2": stats2.get(key, 0),
                "diff": stats1.get(key, 0) - stats2.get(key, 0)
            }
        
        comparison_data[skill] = skill_data
    
    return comparison_data

def display_radar_comparison(comparison_data, player1, player2):
    """
    Affiche une comparaison sous forme de graphique radar
    """
    if not comparison_data:
        st.info("Pas assez de données pour créer un graphique radar.")
        return
    
    # Organisation des statistiques par compétence pour le radar
    skills = list(comparison_data.keys())
    
    # Créer un radar chart pour chaque type de métrique importante
    key_metrics = ["% Efficacité", "% Erreur"]
    
    for metric in key_metrics:
        if any(metric in data["metrics"] for data in comparison_data.values()):
            fig = go.Figure()
            
            # Données pour joueur 1
            r_player1 = []
            theta_player1 = []
            
            # Données pour joueur 2
            r_player2 = []
            theta_player2 = []
            
            for skill in skills:
                skill_data = comparison_data[skill]
                if metric in skill_data["metrics"]:
                    theta_player1.append(skill)
                    r_player1.append(skill_data["metrics"][metric]["player1"])
                    
                    theta_player2.append(skill)
                    r_player2.append(skill_data["metrics"][metric]["player2"])
            
            if r_player1 and r_player2:
                fig.add_trace(go.Scatterpolar(
                    r=r_player1,
                    theta=theta_player1,
                    fill='toself',
                    name=f"{player1.get_full_name()} ({player1.team})"
                ))
                
                fig.add_trace(go.Scatterpolar(
                    r=r_player2,
                    theta=theta_player2,
                    fill='toself',
                    name=f"{player2.get_full_name()} ({player2.team})"
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(max(r_player1 or [0]), max(r_player2 or [0])) * 1.1]
                        )
                    ),
                    title=f"Comparaison - {metric}",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)

def display_bar_comparison(comparison_data, player1, player2, selected_skills):
    """
    Affiche des graphiques à barres comparatifs pour chaque compétence
    """
    if not comparison_data:
        st.info("Pas assez de données pour créer les graphiques à barres.")
        return
    
    for skill in selected_skills:
        if skill not in comparison_data:
            continue
            
        skill_data = comparison_data[skill]
        metrics = [k for k in skill_data["metrics"].keys() if k != "Total" and k.startswith("%")]
        
        if not metrics:
            continue
            
        # Préparation des données pour le graphique
        fig = go.Figure()
        
        # Extraction des valeurs pour les deux joueurs
        values_player1 = [skill_data["metrics"][m]["player1"] for m in metrics]
        values_player2 = [skill_data["metrics"][m]["player2"] for m in metrics]
        
        # Création du graphique à barres
        fig.add_trace(go.Bar(
            x=metrics,
            y=values_player1,
            name=f"{player1.get_full_name()} ({player1.team})",
            marker_color='royalblue'
        ))
        
        fig.add_trace(go.Bar(
            x=metrics,
            y=values_player2,
            name=f"{player2.get_full_name()} ({player2.team})",
            marker_color='firebrick'
        ))
        
        # Configuration du layout
        skill_name = {
            "Attack": "Attaque", "Block": "Bloc", "Serve": "Service",
            "Reception": "Réception", "Dig": "Défense", "Set": "Passe"
        }.get(skill, skill)
        
        fig.update_layout(
            title=f"Comparaison - {skill_name}",
            xaxis_title="Métriques",
            yaxis_title="Pourcentage (%)",
            barmode='group',
            height=400
        )
        
        # Ajout du total d'actions dans la légende
        total1 = skill_data["metrics"].get("Total", {}).get("player1", 0)
        total2 = skill_data["metrics"].get("Total", {}).get("player2", 0)
        st.markdown(f"**{skill_name}** - *{player1.get_full_name()}: {total1} actions, {player2.get_full_name()}: {total2} actions*")
        
        st.plotly_chart(fig, use_container_width=True)

def display_table_comparison(comparison_data):
    """
    Affiche un tableau comparatif détaillé des statistiques des joueurs
    """
    if not comparison_data:
        st.info("Pas assez de données pour créer le tableau comparatif.")
        return
    
    # Préparer les données pour le tableau
    table_data = []
    
    for skill, data in comparison_data.items():
        skill_name = {
            "Attack": "Attaque", "Block": "Bloc", "Serve": "Service",
            "Reception": "Réception", "Dig": "Défense", "Set": "Passe"
        }.get(skill, skill)
        
        for metric, values in data["metrics"].items():
            if metric == "Total":
                continue
                
            table_data.append({
                "Compétence": skill_name,
                "Métrique": metric,
                f"{data['player1_name']} ({data['player1_team']})": values["player1"],
                f"{data['player2_name']} ({data['player2_team']})": values["player2"],
                "Différence": values["diff"]
            })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            column_config={
                "Différence": st.column_config.NumberColumn(
                    "Différence",
                    format="%.1f",
                    help="Différence entre les deux joueurs (Joueur 1 - Joueur 2)"
                )
            },
            use_container_width=True
        )

def display_face_to_face_comparison(comparison_data, player1, player2):
    """
    Affiche une visualisation face à face des compétences
    """
    if not comparison_data:
        st.info("Pas assez de données pour créer la visualisation face à face.")
        return
    
    # Sélectionner les métriques clés pour la comparaison
    key_metrics = ["% Efficacité", "% Kill", "% Erreur", "Total"]
    
    # Organiser les données pour chaque joueur
    player1_name = f"{player1.get_full_name()} ({player1.team})"
    player2_name = f"{player2.get_full_name()} ({player2.team})"
    
    # Afficher les cartes d'information des joueurs
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        display_player_card(player1)
    with col_p2:
        display_player_card(player2)
    
    for skill, data in comparison_data.items():
        skill_name = {
            "Attack": "Attaque", "Block": "Bloc", "Serve": "Service",
            "Reception": "Réception", "Dig": "Défense", "Set": "Passe"
        }.get(skill, skill)
        
        st.markdown(f"### Comparaison - {skill_name}")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"#### {player1_name}")
            for metric in key_metrics:
                if metric in data["metrics"]:
                    value = data["metrics"][metric]["player1"]
                    if metric == "Total":
                        st.metric(metric, int(value))
                    else:
                        st.metric(metric, f"{value:.1f}%")
        
        with col2:
            st.markdown("#### VS")
            for metric in key_metrics:
                if metric in data["metrics"]:
                    diff = data["metrics"][metric]["diff"]
                    if metric == "Total":
                        # Pour le total, afficher simplement la différence sans delta
                        st.metric("Différence", f"{int(diff)}")
                    else:
                        # Formater la différence avec une seule décimale
                        formatted_diff = f"{diff:.1f}%"
                        
                        # Traiter séparément "% Erreur" (où moins est mieux)
                        if metric == "% Erreur":
                            # Pour "% Erreur", une valeur négative de diff est en fait positive
                            # (joueur1 a moins d'erreurs que joueur2)
                            # Donc nous inversons le signe pour l'affichage delta
                            delta_value = -diff
                            st.metric("Différence", formatted_diff, delta=f"{delta_value:.1f}")
                        else:
                            # Pour les autres métriques, une valeur positive de diff est positive
                            # (joueur1 est meilleur que joueur2)
                            st.metric("Différence", formatted_diff, delta=f"{diff:.1f}")
        
        with col3:
            st.markdown(f"#### {player2_name}")
            for metric in key_metrics:
                if metric in data["metrics"]:
                    value = data["metrics"][metric]["player2"]
                    if metric == "Total":
                        st.metric(metric, int(value))
                    else:
                        st.metric(metric, f"{value:.1f}%")
        
        st.markdown("---")