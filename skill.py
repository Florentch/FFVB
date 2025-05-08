import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
from utils import player_selector, team_selector, get_match_selector


def skill_comparison_tab(players, skill, label="réceptions", categories=None):
    """
    Affiche l'onglet de comparaison des compétences des joueurs
    
    Cette fonction:
    1. Filtre les joueurs avec suffisamment de données
    2. Configure les filtres et options d'affichage
    3. Délègue l'affichage aux fonctions spécialisées selon le mode choisi
    
    Args:
        players (list): Liste des objets Player
        skill (str): Type de compétence à analyser (Reception, Block, etc.)
        label (str): Libellé pour l'affichage (réceptions, blocks, etc.)
        categories (list): Liste des catégories d'évaluation pour la compétence
    """
    st.header(f"📥 Analyse des {label}")

    # Filtrer les joueurs qui ont des données pour cette compétence
    players_with_data = [p for p in players if len(p.get_action_df(skill)) > 4]

    if not players_with_data:
        st.warning(f"Aucun joueur avec des données de {label} trouvées.")
        return

    # Utilisation des filtres de la session si disponibles
    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)
    
    # Déterminer la zone d'affichage (sidebar ou principale)
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    
    # Options d'affichage en haut
    if not is_pinned:
        # Si on est dans la zone principale, utilisez des colonnes pour l'affichage
        col1, col2 = st.columns(2)
        with col1:
            mode = st.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], horizontal=True, label_visibility="visible")
        with col2:
            if 'selected_moment' not in st.session_state:
                st.session_state.selected_moment = moment
    else:
        # Si on est dans la sidebar, affichage vertical
        mode = st.sidebar.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], horizontal=True, label_visibility="visible")

    # Sélection des matchs
    selected_matches = get_match_selector(players_with_data)
    
    if not selected_matches:
        st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return

    # Affichage selon le mode sélectionné
    if mode == "Par Joueurs":
        df = player_selector(players_with_data, skill, moment, selected_matches, set_filter)
        if df is None or df.empty:
            # Un message d'avertissement est déjà affiché dans player_selector
            return
        display_player_stats(players_with_data, selected_matches, moment, set_filter, skill, label, categories, df)
    else:
        df = team_selector(players_with_data, skill, moment, selected_matches, set_filter)
        if df is None or df.empty:
            # Un message d'avertissement est déjà affiché dans team_selector
            return
        display_team_stats(df, skill, label, categories)


def display_player_stats(players, selected_matches, moment, set_filter, skill, label, categories, df):
    """
    Affiche les statistiques par joueur
    
    Args:
        players (list): Liste des joueurs à analyser
        selected_matches (list): Liste des matchs sélectionnés
        moment (str): Moment du match à analyser (Tout, Début, Milieu, Fin)
        set_filter (list): Filtre sur les sets
        skill (str): Type de compétence
        label (str): Libellé pour l'affichage
        categories (list): Liste des catégories d'évaluation
        df (DataFrame): DataFrame contenant les statistiques préparées par player_selector
    """
    # Affichage du tableau de données
    st.dataframe(df.set_index("Nom"), use_container_width=True)

    # Création du graphique à barres
    fig = go.Figure()
    for _, row in df.iterrows():
        player_name = row["Nom"]
        fig.add_trace(go.Bar(
            x=categories + ["Total"],
            y=[row.get(cat, 0) for cat in categories] + [row["Total"]],
            name=player_name,
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

    data = df.to_dict('records')
    
    if main_metric and all(main_metric in d for d in data):
        classement = sorted(data, key=lambda x: -x.get(main_metric, 0))
        st.subheader(f"🏆 Classement : {main_metric}")
        columns_to_show = ["Nom", "Équipe", main_metric, categories[0], "Total"]
    else:
        classement = data
        st.subheader("🏆 Classement indisponible")
        columns_to_show = ["Nom", "Équipe", "Total"]

    st.table(pd.DataFrame(classement)[columns_to_show])


def display_team_stats(df, skill, label, categories):
    """
    Affiche les statistiques par équipe
    
    Args:
        df (DataFrame): DataFrame contenant les statistiques préparées par team_selector
        skill (str): Type de compétence
        label (str): Libellé pour l'affichage
        categories (list): Liste des catégories d'évaluation
    """
    st.subheader("📊 Statistiques moyennes par équipe")

    # Affichage du tableau
    st.dataframe(df.set_index("Équipe"), use_container_width=True)

    # Création des graphiques en camembert par équipe
    st.subheader("🧩 Répartition des catégories par équipe")
    for _, row in df.iterrows():
        team = row["Équipe"]
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