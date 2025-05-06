import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

SKILL = "Reception"  # Changer ici pour utiliser ce fichier pour une autre compétence

def reception_comparison_tab(players):
    st.header("📥 Analyse des Réceptions")

    players_with_skill = [p for p in players if not p.get_action_df(SKILL).empty]

    if not players_with_skill:
        st.warning(f"Aucun joueur avec des données de {SKILL.lower()} n'a été trouvé.")
        return

    mode = st.radio("Mode de comparaison", ["Par Joueurs", "Par Équipes"], horizontal=True)
    moment = st.selectbox("Choisir le moment dans le set", ["Tout", "Début", "Milieu", "Fin"])

    match_ids, match_labels = get_match_options(players_with_skill)
    
    selected_matches = st.multiselect(
        "Filtrer par match", 
        options=match_ids, 
        format_func=lambda x: match_labels.get(x, str(x)),
        default=match_ids
    )

    if mode == "Par Joueurs":
        display_player_stats(players_with_skill, selected_matches, moment)
    else:
        display_team_stats(players_with_skill, selected_matches, moment)


def get_match_options(players):
    match_data = []
    seen = set()

    for p in players:
        for match_id in p.df[p.df['skill'] == SKILL]['match_id'].dropna().unique():
            if match_id in seen:
                continue
            seen.add(match_id)
            match_row = p.df[p.df['match_id'] == match_id].iloc[0]
            match_data.append({
                'match_id': match_id,
                'match_label': f"{match_row.get('home_team', 'A')} vs {match_row.get('visiting_team', 'B')} - {match_row.get('match_day', '')}"
            })

    match_df = pd.DataFrame(match_data)
    return list(match_df['match_id']), match_df.set_index('match_id')['match_label'].to_dict()


def display_player_stats(players, selected_matches, moment):
    names = [f"{p.first_name} {p.last_name}" for p in players]
    default = names[:min(3, len(names))]

    selected = st.multiselect("Sélection des joueurs", names, default=default)
    selected_players = [p for p in players if f"{p.first_name} {p.last_name}" in selected]

    if not selected_players or not selected_matches:
        st.info("Sélectionnez au moins un joueur et un match.")
        return

    data = []
    for p in selected_players:
        stats = p.get_skill_stats(SKILL, moment, selected_matches)
        if stats["Total"] > 0:
            row = {"Nom": f"{p.first_name} {p.last_name}", **stats}
            data.append(row)

    if not data:
        st.info("Aucune donnée disponible pour les sélections actuelles.")
        return

    df = pd.DataFrame(data).set_index("Nom")
    st.dataframe(df, use_container_width=True)

    create_player_bar_chart(selected_players, selected_matches, moment)
    display_player_ranking(data)


def create_player_bar_chart(players, match_filter, moment):
    fig = go.Figure()

    for p in players:
        stats = p.get_skill_stats(SKILL, moment, match_filter)
        if stats["Total"] > 0:
            keys = [k for k in stats if not k.startswith('%') and k != 'Total']
            fig.add_trace(go.Bar(
                x=[f"% {k}" for k in keys] + ['Total'],
                y=[stats.get(f"% {k}", 0) for k in keys] + [stats['Total']],
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
    st.subheader("🏆 Classement : % Réceptions Parfaites")
    ranking = sorted(data, key=lambda x: -x.get("% Parfaites", 0))
    st.table(pd.DataFrame(ranking)[["Nom", "% Parfaites", "Parfaites", "Total"]])


def display_team_stats(players, selected_matches, moment):
    st.subheader("📊 Statistiques moyennes par équipe")

    if not selected_matches:
        st.info("Sélectionnez au moins un match.")
        return

    team_stats = defaultdict(lambda: defaultdict(int))

    for p in players:
        if not p.team:
            continue
        stats = p.get_skill_stats(SKILL, moment, selected_matches)
        if stats["Total"] > 0:
            for k, v in stats.items():
                team_stats[p.team][k] += v

    if not team_stats:
        st.info("Aucune donnée pour les équipes sélectionnées.")
        return

    rows = []
    for team, stats in team_stats.items():
        total = stats["Total"]
        if total == 0:
            continue
        row = {
            "Équipe": team,
            **{f"% {k}": round(stats[k] / total * 100, 1) for k in stats if k not in ("Total") and not k.startswith('%')},
            "Nbre Total Réceptions": total
        }
        rows.append(row)

    df = pd.DataFrame(rows).set_index("Équipe")
    st.dataframe(df, use_container_width=True)

    st.subheader("🧩 Répartition des réceptions par équipe")
    for team in df.index:
        row = df.loc[team]
        pie = go.Figure(data=[go.Pie(
            labels=[k[2:] for k in row.index if k.startswith('%')],
            values=[v for k, v in row.items() if k.startswith('%')],
            hole=0.4
        )])
        pie.update_layout(title_text=f"{team} - {row['Nbre Total Réceptions']} réceptions", height=400)
        st.plotly_chart(pie, use_container_width=True)
