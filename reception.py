import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict

def reception_comparison_tab(players):
    """
    Affiche l'onglet de comparaison des statistiques de réception des joueurs et équipes.
    
    Args:
        players (list): Liste des objets Player à analyser
    """
    st.header("📥 Analyse des Réceptions")

    # Filtrer les joueurs qui ont au moins une réception
    players_with_reception = [p for p in players if len(p.df_reception) > 0]
    
    if not players_with_reception:
        st.warning("Aucun joueur avec des données de réception n'a été trouvé.")
        return

    # Interface utilisateur - Configuration initiale
    mode = st.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], horizontal=True)
    moment = st.selectbox("Choisir le moment dans le set", ["Tout", "Début", "Milieu", "Fin"])

    # Récupération des matchs disponibles
    match_data = []
    match_ids_set = set()  # Pour éviter les doublons
    
    for p in players_with_reception:
        for match_id in p.df_reception['match_id'].dropna().unique():
            if match_id in match_ids_set:
                continue
                
            match_ids_set.add(match_id)
            match_rows = p.df[p.df['match_id'] == match_id]
            
            if len(match_rows) > 0:
                match_row = match_rows.iloc[0]
                home_team = match_row.get('home_team', 'Équipe A')
                visiting_team = match_row.get('visiting_team', 'Équipe B')
                match_day = match_row.get('match_day', '')
                
                match_data.append({
                    'match_id': match_id,
                    'match_label': f"{home_team} vs {visiting_team} - {match_day}"
                })

    # Créer DataFrame de matchs et options pour le sélecteur
    match_df = pd.DataFrame(match_data)
    match_ids = list(match_df['match_id'].unique())
    match_labels = match_df.set_index('match_id')['match_label'].to_dict()

    # Sélection des matchs
    selected_matches = st.multiselect(
        "Filtrer par match", 
        options=match_ids, 
        format_func=lambda x: match_labels.get(x, str(x)),
        default=match_ids
    )

    # Mode Par Joueurs
    if mode == "Par Joueurs":
        display_player_stats(players_with_reception, selected_matches, moment)
    
    # Mode Par Équipes
    elif mode == "Par Équipes":
        display_team_stats(players_with_reception, selected_matches, moment)


def display_player_stats(players, selected_matches, moment):
    """
    Affiche les statistiques individuelles des joueurs.
    
    Args:
        players (list): Liste des joueurs avec des réceptions
        selected_matches (list): Matchs sélectionnés
        moment (str): Moment du set
    """
    # Sélection des joueurs
    player_names = [f"{p.first_name} {p.last_name}" for p in players]
    default_selection = player_names[:min(3, len(player_names))]
    
    selected_names = st.multiselect(
        "Sélection des joueurs", 
        player_names,
        default=default_selection
    )
    
    selected_players = [p for p in players if f"{p.first_name} {p.last_name}" in selected_names]

    # Vérifier conditions pour affichage
    if not selected_players:
        st.info("Sélectionnez au moins un joueur pour afficher les données.")
        return
        
    if not selected_matches:
        st.info("Sélectionnez au moins un match pour afficher les données.")
        return

    # Collecter les statistiques des joueurs
    data = []
    for p in selected_players:
        stats = p.get_reception_stats(moment, match_filter=selected_matches)
        if stats["Total"] > 0:
            row = {"Nom": f"{p.first_name} {p.last_name}"}
            row.update(stats)
            data.append(row)

    # Afficher les résultats
    if not data:
        st.info("Aucune donnée de réception pour les joueurs et matchs sélectionnés.")
        return
        
    # Tableau de statistiques
    df = pd.DataFrame(data).set_index("Nom")
    st.dataframe(df, use_container_width=True)

    # Graphique en barres
    create_player_bar_chart(selected_players, selected_matches, moment)
    
    # Classement
    display_player_ranking(data)


def create_player_bar_chart(selected_players, selected_matches, moment):
    """
    Crée et affiche un graphique en barres des statistiques des joueurs.
    """
    fig = go.Figure()
    
    for p in selected_players:
        stats = p.get_reception_stats(moment, match_filter=selected_matches)
        if stats["Total"] > 0:
            fig.add_trace(go.Bar(
                x=["% Parfaites", "Parfaites", "Bonnes", "Mauvaises", "Ratées", "Total"],
                y=[stats["% Parfaites"], stats["Parfaites"], stats["Bonnes"], 
                   stats["Mauvaises"], stats["Ratées"], stats["Total"]],
                name=f"{p.first_name} {p.last_name}",
                textposition='auto'
            ))

    fig.update_layout(
        barmode='group',
        xaxis_title="Catégories",
        yaxis_title="Valeurs",
        height=500,
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_player_ranking(data):
    """
    Affiche le classement des joueurs par pourcentage de réceptions parfaites.
    """
    classement = sorted(data, key=lambda x: -x["% Parfaites"])
    st.subheader("🏆 Classement : % Réceptions Parfaites")
    
    ranking_df = pd.DataFrame(classement)[["Nom", "% Parfaites", "Parfaites", "Total"]]
    st.table(ranking_df)


def display_team_stats(players, selected_matches, moment):
    """
    Affiche les statistiques par équipe.
    
    Args:
        players (list): Liste des joueurs avec des réceptions
        selected_matches (list): Matchs sélectionnés
        moment (str): Moment du set
    """
    st.subheader("📊 Statistiques moyennes par équipe")

    if not selected_matches:
        st.info("Sélectionnez au moins un match pour afficher les données.")
        return

    # Initialiser les statistiques d'équipe
    equipe_stats = defaultdict(lambda: {"Parfaites": 0, "Bonnes": 0, "Mauvaises": 0, "Ratées": 0, "Total": 0})

    # Collecter les statistiques par équipe
    for p in players:
        if not p.team:
            continue
            
        stats = p.get_reception_stats(moment, match_filter=selected_matches)
        if stats["Total"] > 0:
            for k in ["Parfaites", "Bonnes", "Mauvaises", "Ratées", "Total"]:
                equipe_stats[p.team][k] += stats[k]

    # Préparer les données pour affichage
    table_data = []
    for team, stats in equipe_stats.items():
        total = stats["Total"]
        if total == 0:
            continue
            
        parfait_pct = round(stats["Parfaites"] / total * 100, 1)
        bonnes_pct = round(stats["Bonnes"] / total * 100, 1)
        mauvaises_pct = round(stats["Mauvaises"] / total * 100, 1)
        ratees_pct = round(stats["Ratées"] / total * 100, 1)

        table_data.append({
            "Équipe": team,
            "% Parfaites": parfait_pct,
            "% Bonnes": bonnes_pct,
            "% Mauvaises": mauvaises_pct,
            "% Ratées": ratees_pct,
            "Nbre Total Réceptions": total  # Nom de colonne plus explicite
        })

    if not table_data:
        st.info("Aucune donnée disponible pour les matchs sélectionnés.")
        return
        
    # Afficher le tableau des statistiques d'équipe
    df_eq = pd.DataFrame(table_data).set_index("Équipe")
    st.dataframe(df_eq, use_container_width=True)

    # Graphiques circulaires par équipe
    st.subheader("🧩 Répartition des réceptions par équipe")
    for team in df_eq.index:
        row = df_eq.loc[team]
        pie = go.Figure(data=[
            go.Pie(
                labels=["Parfaites", "Bonnes", "Mauvaises", "Ratées"],
                values=[row["% Parfaites"], row["% Bonnes"], row["% Mauvaises"], row["% Ratées"]],
                hole=0.4
            )
        ])
        pie.update_layout(
            title_text=f"{team} - {row['Nbre Total Réceptions']} réceptions", 
            height=400
        )
        st.plotly_chart(pie, use_container_width=True)