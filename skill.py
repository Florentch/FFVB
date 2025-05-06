import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

def skill_comparison_tab(players, skill, label="réceptions", categories=None):
    """
    Affiche l'onglet de comparaison des compétences des joueurs
    
    Args:
        players (list): Liste des objets Player
        skill (str): Type de compétence à analyser (Reception, Block, etc.)
        label (str): Libellé pour l'affichage (réceptions, blocks, etc.)
        categories (list): Liste des catégories d'évaluation pour la compétence
    """
    st.header(f"📥 Analyse des {label}")

    # Filtrer les joueurs qui ont des données pour cette compétence
    players_with_data = [p for p in players if len(p.get_action_df(skill)) > 0]

    if not players_with_data:
        st.warning(f"Aucun joueur avec des données de {label} trouvées.")
        return

    # Options d'affichage
    mode = st.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], horizontal=True)
    moment = st.selectbox("Choisir le moment dans le set", ["Tout", "Début", "Milieu", "Fin"])

    # Récupération des données de match
    match_data, match_ids_set = [], set()
    for p in players_with_data:
        for match_id in p.df['match_id'].dropna().unique():
            if match_id in match_ids_set:
                continue
            match_ids_set.add(match_id)
            match_rows = p.df[p.df['match_id'] == match_id]
            if len(match_rows) > 0:
                row = match_rows.iloc[0]
                match_data.append({
                    'match_id': match_id,
                    'match_label': f"{row.get('home_team', 'Équipe A')} vs {row.get('visiting_team', 'Équipe B')} - {row.get('match_day', '')}"
                })

    match_df = pd.DataFrame(match_data)
    match_ids = list(match_df['match_id'].unique())
    match_labels = match_df.set_index('match_id')['match_label'].to_dict()

    # Sélection des matchs à analyser
    selected_matches = st.multiselect(
        "Filtrer par match", 
        options=match_ids,
        format_func=lambda x: match_labels.get(x, str(x)),
        default=match_ids
    )

    # Affichage selon le mode sélectionné
    if mode == "Par Joueurs":
        display_player_stats(players_with_data, selected_matches, moment, skill, label, categories)
    else:
        display_team_stats(players_with_data, selected_matches, moment, skill, label, categories)

def display_player_stats(players, selected_matches, moment, skill, label, categories):
    """
    Affiche les statistiques par joueur
    
    Args:
        players (list): Liste des joueurs à analyser
        selected_matches (list): Liste des matchs sélectionnés
        moment (str): Moment du match à analyser (Tout, Début, Milieu, Fin)
        skill (str): Type de compétence
        label (str): Libellé pour l'affichage
        categories (list): Liste des catégories d'évaluation
    """
    # Sélection des joueurs
    names = [f"{p.first_name} {p.last_name}" for p in players]
    selected_names = st.multiselect(
        "Sélection des joueurs", 
        names, 
        default=names[:min(3, len(names))]
    )
    selected_players = [p for p in players if f"{p.first_name} {p.last_name}" in selected_names]

    if not selected_players or not selected_matches:
        st.info("Sélectionnez des joueurs et au moins un match pour afficher les données.")
        return

    # Récupération des statistiques par joueur
    data = []
    for p in selected_players:
        stats = p.get_skill_stats(skill, moment, match_filter=selected_matches)
        if stats["Total"] > 0:
            row = {"Nom": f"{p.first_name} {p.last_name}"}
            row.update(stats)
            data.append(row)

    if not data:
        st.info(f"Aucune donnée de {label} pour les joueurs et matchs sélectionnés.")
        return

    # Affichage du tableau de données
    df = pd.DataFrame(data).set_index("Nom")
    st.dataframe(df, use_container_width=True)

    # Création du graphique à barres
    fig = go.Figure()
    for p in selected_players:
        stats = p.get_skill_stats(skill, moment, match_filter=selected_matches)
        if stats["Total"] > 0:
            fig.add_trace(go.Bar(
                x=categories + ["Total"],
                y=[stats.get(cat, 0) for cat in categories] + [stats["Total"]],
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

    # Classement des joueurs
    # Déterminer la métrique de classement automatiquement (première catégorie en %)
    main_metric = f"% {categories[0]}" if categories else None

    if main_metric and all(main_metric in d for d in data):
        classement = sorted(data, key=lambda x: -x.get(main_metric, 0))
        st.subheader(f"🏆 Classement : {main_metric}")
        columns_to_show = ["Nom", main_metric, categories[0], "Total"]
    else:
        classement = data
        st.subheader("🏆 Classement indisponible")
        columns_to_show = ["Nom", "Total"]

    st.table(pd.DataFrame(classement)[columns_to_show])


def display_team_stats(players, selected_matches, moment, skill, label, categories):
    """
    Affiche les statistiques par équipe
    
    Args:
        players (list): Liste des joueurs à analyser
        selected_matches (list): Liste des matchs sélectionnés
        moment (str): Moment du match à analyser (Tout, Début, Milieu, Fin)
        skill (str): Type de compétence
        label (str): Libellé pour l'affichage
        categories (list): Liste des catégories d'évaluation
    """
    st.subheader("📊 Statistiques moyennes par équipe")

    if not selected_matches:
        st.info("Sélectionnez au moins un match pour afficher les données.")
        return

    # Aggrégation des statistiques par équipe
    equipe_stats = defaultdict(lambda: {k: 0 for k in categories + ["Total"]})

    for p in players:
        if not p.team:
            continue
        stats = p.get_skill_stats(skill, moment, match_filter=selected_matches)
        if stats["Total"] > 0:
            for k in categories + ["Total"]:
                equipe_stats[p.team][k] += stats.get(k, 0)

    # Préparation des données pour le tableau
    table_data = []
    for team, stats in equipe_stats.items():
        total = stats["Total"]
        if total == 0:
            continue
        row = {"Équipe": team, "Nbre Total": total}
        for k in categories:
            row[f"% {k}"] = round(stats[k] / total * 100, 1)
        table_data.append(row)

    if not table_data:
        st.info("Aucune donnée disponible pour les matchs sélectionnés.")
        return

    # Affichage du tableau
    df_eq = pd.DataFrame(table_data).set_index("Équipe")
    st.dataframe(df_eq, use_container_width=True)

    # Création des graphiques en camembert par équipe
    st.subheader("🧩 Répartition des catégories par équipe")
    for team in df_eq.index:
        row = df_eq.loc[team]
        pie = go.Figure(data=[
            go.Pie(
                labels=categories,
                values=[row[f"% {cat}"] for cat in categories],
                hole=0.4
            )
        ])
        pie.update_layout(
            title_text=f"{team} - {int(row['Nbre Total'])} {label}", 
            height=400
        )
        st.plotly_chart(pie, use_container_width=True)