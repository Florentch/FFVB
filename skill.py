import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
from utils import player_selector  # Nouvelle importation


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
    players_with_data = [p for p in players if len(p.get_action_df(skill)) > 4]

    if not players_with_data:
        st.warning(f"Aucun joueur avec des données de {label} trouvées.")
        return

    # Utilisation des filtres de la session si disponibles
    moment = st.session_state.get('selected_moment', "Tout")
    set_filter = st.session_state.get('selected_sets', None)
    
    # Options d'affichage en haut
    # MODIFICATION: Utiliser directement st.sidebar ou st, sans utiliser with
    fixed_area = st.sidebar if st.session_state.get('pin_selections', True) else st
    
    # MODIFICATION: Utiliser la bonne syntaxe pour créer des éléments dans la sidebar ou la zone principale
    if not st.session_state.get('pin_selections', True):
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

    # Récupération des données de match avec date
    match_data, match_ids_set = [], set()
    for p in players_with_data:
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
                    'match_label': f"{row.get('home_team', 'Équipe A')} vs {row.get('visiting_team', 'Équipe B')} - {match_day}"
                })

    # Trier les matchs par date si possible
    match_df = pd.DataFrame(match_data)
    if not match_df.empty and 'match_day' in match_df.columns:
        try:
            # Convertir les dates au format DD/MM/YYYY en datetime pour le tri
            match_df['date_for_sort'] = pd.to_datetime(match_df['match_day'], format='%d/%m/%Y', errors='coerce')
            match_df = match_df.sort_values(by='date_for_sort', ascending=False)
        except Exception as e:
            print(f"Erreur de tri des dates: {e}")  # Pour le débogage
            pass  # Si le tri échoue, on garde l'ordre d'origine
    
    match_ids = list(match_df['match_id'].unique())
    match_labels = match_df.set_index('match_id')['match_label'].to_dict()

    # Sélection des matchs avec options rapides - maintenant dans la zone épinglable
    # MODIFICATION: Ne pas utiliser with fixed_area, mais choisir la zone directement
    if st.session_state.get('pin_selections', True):
        # Initialiser la variable de session si elle n'existe pas
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = match_ids
        
        # Utiliser des colonnes dans la sidebar également pour plus de compacité
        col1, col2 = st.sidebar.columns([3, 1])
        
        with col2:
            st.write("Options rapides")
            if st.button("Tous", key="btn_all_matches"):
                st.session_state.selected_matches = match_ids
            if st.button("Aucun", key="btn_no_match"):
                st.session_state.selected_matches = []
        
        with col1:
            selected_matches = st.multiselect(
                "Filtrer par match", 
                options=match_ids,
                format_func=lambda x: match_labels.get(x, str(x)),
                default=st.session_state.selected_matches
            )
            # Mettre à jour la session
            st.session_state.selected_matches = selected_matches

        # Zone pour la sélection des joueurs
        if mode == "Par Joueurs":
            # Utiliser player_selector - celui-ci sera modifié pour utiliser la zone fixe
            df = player_selector(players_with_data, skill, moment, selected_matches, set_filter)
            if df is None or df.empty:
                # Déjà affiché dans player_selector, pas besoin de répéter l'avertissement
                return
    else:
        # Initialiser la variable de session si elle n'existe pas
        if 'selected_matches' not in st.session_state:
            st.session_state.selected_matches = match_ids
        
        # Utiliser des colonnes dans la zone principale 
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.write("Options rapides")
            if st.button("Tous", key="btn_all_matches"):
                st.session_state.selected_matches = match_ids
            if st.button("Aucun", key="btn_no_match"):
                st.session_state.selected_matches = []
        
        with col1:
            selected_matches = st.multiselect(
                "Filtrer par match", 
                options=match_ids,
                format_func=lambda x: match_labels.get(x, str(x)),
                default=st.session_state.selected_matches
            )
            # Mettre à jour la session
            st.session_state.selected_matches = selected_matches

        # Zone pour la sélection des joueurs
        if mode == "Par Joueurs":
            # Utiliser player_selector - celui-ci sera modifié pour utiliser la zone fixe
            df = player_selector(players_with_data, skill, moment, selected_matches, set_filter)
            if df is None or df.empty:
                # Déjà affiché dans player_selector, pas besoin de répéter l'avertissement
                return
    
    # Affichage selon le mode sélectionné
    if mode == "Par Joueurs":
        display_player_stats(players_with_data, selected_matches, moment, set_filter, skill, label, categories, df)
    else:
        display_team_stats(players_with_data, selected_matches, moment, set_filter, skill, label, categories)


def display_player_stats(players, selected_matches, moment, set_filter, skill, label, categories, df=None):
    """
    Affiche les statistiques par joueur
    
    Args:
        players (list): Liste des joueurs à analyser
        selected_matches (list): Liste des matchs sélectionnés
        moment (str): Moment du match à analyser (Tout, Début, Milieu, Fin)
        skill (str): Type de compétence
        label (str): Libellé pour l'affichage
        categories (list): Liste des catégories d'évaluation
        df (DataFrame, optional): DataFrame déjà préparé par player_selector
    """
    if not selected_matches:
        st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return
        
    # Si df n'est pas fourni, utiliser player_selector
    if df is None:
        df = player_selector(players, skill, moment, selected_matches, set_filter)
    
    if df is None:
        st.warning("⚠️ Veuillez sélectionner au moins un joueur pour afficher les statistiques.")
        return
    
    if df.empty:
        st.info(f"Aucune donnée de {label} pour les joueurs et matchs sélectionnés.")
        return
    
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


def display_team_stats(players, selected_matches, moment, set_filter, skill, label, categories):
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
        st.warning("⚠️ Veuillez sélectionner au moins un match pour afficher les statistiques.")
        return

    # Aggrégation des statistiques par équipe
    equipe_stats = defaultdict(lambda: {k: 0 for k in categories + ["Total"]})

    for p in players:
        if not p.team:
            continue
        stats = p.get_skill_stats(skill, moment, match_filter=selected_matches, set_filter = set_filter)
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