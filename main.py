import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from player import Player
from datavolley import read_dv

# Chargement des données
dv_instance = read_dv.DataVolley('data/CNVB_Spain.dvw')
df = dv_instance.get_plays()
players_df = dv_instance.get_players()

# Création des objets Player
players = []
for _, row in players_df.iterrows():
    player = Player(
        id_=row['player_id'],
        first_name=row['name'],
        last_name=row['lastname'],
        number=row['player_number'],
        team=row['team'],
        df=df[df['player_id'] == row['player_id']]
    )
    players.append(player)

# ------------------------------
# Onglet Réception
# ------------------------------
def reception_comparison_tab(players):
    st.header("📥 Comparaison des Réceptions")

    # Sélection du nombre de joueurs
    nb_joueurs = st.number_input("Nombre de joueurs à comparer", min_value=1, max_value=len(players), value=3, step=1)

    # Liste des noms
    player_names = [f"{p.first_name} {p.last_name}" for p in players]

    # Multiselect pour choisir les joueurs
    selected_names = st.multiselect("Sélection des joueurs", player_names, default=player_names[:nb_joueurs])
    selected_players = [p for p in players if f"{p.first_name} {p.last_name}" in selected_names]

    # Affichage du DataFrame
    if selected_players:
        data = {
            "Nom": [f"{p.first_name} {p.last_name}" for p in selected_players],
            "Précision (%)": [p.recep_precision() for p in selected_players],
            "Parfaites": [p.recep_parfait() for p in selected_players],
            "Bonnes": [p.recep_good() for p in selected_players],
            "Mauvaises": [p.recep_bad() for p in selected_players],
            "Fails": [p.recep_fail() for p in selected_players],
            "Total": [p.recep_total() for p in selected_players],
        }
        df_comparaison = pd.DataFrame(data)
        st.dataframe(df_comparaison.set_index("Nom"), use_container_width=True)
    else:
        st.info("Sélectionne au moins un joueur pour afficher les données.")

    # Graphique
    st.subheader("📊 Graphique des Réceptions")

    if selected_players:
        fig = go.Figure()
        categories = ["Précision (%)", "Parfaites", "Bonnes", "Mauvaises", "Fails", "Total"]

        for player in selected_players:
            values = [
                player.recep_precision(),
                player.recep_parfait(),
                player.recep_good(),
                player.recep_bad(),
                player.recep_fail(),
                player.recep_total()
            ]

            fig.add_trace(go.Bar(
                x=categories,
                y=values,
                name=f"{player.first_name} {player.last_name}",
                text=values,
                textposition='auto',
                hovertemplate='%{x} : %{y}<extra>%{fullData.name}</extra>',
            ))

        fig.update_layout(
            barmode='group',
            xaxis_title="Catégories",
            yaxis_title="Valeurs",
            legend_title="Joueurs",
            template="plotly_white",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucun joueur sélectionné pour le graphique.")

    # CLASSEMENT des joueurs par % de réceptions parfaites
    st.subheader("🏆 Classement : % Réceptions Parfaites")

    if selected_players:
        classement_data = []

        for p in selected_players:
            total = p.recep_total()
            parfait = p.recep_parfait()
            pourcentage = round((parfait / total) * 100, 1) if total > 0 else 0.0
            classement_data.append({
                "Joueur": f"{p.first_name} {p.last_name}",
                "% Réceptions Parfaites": pourcentage,
                "Parfaites": parfait,
                "Total": total
            })

        df_classement = pd.DataFrame(classement_data)
        df_classement = df_classement.sort_values(by="% Réceptions Parfaites", ascending=False)

        st.table(df_classement.reset_index(drop=True))
    else:
        st.info("Aucun joueur sélectionné pour le classement.")

# ------------------------------
# Lancement de l'app
# ------------------------------
tab = st.selectbox("Choisir un onglet", ["Réception"])
if tab == "Réception":
    reception_comparison_tab(players)

