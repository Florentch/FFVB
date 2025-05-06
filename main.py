import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
import pandas as pd
import glob
import os

from player import Player
from datavolley import read_dv
from skill import skill_comparison_tab
from player_evolution import player_evolution_tab

# Configuration de la page
st.set_page_config(
    page_title="Analyse de Volleyball", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Analyse de Volleyball")
st.markdown("""
    Application d'analyse des données de volleyball extraites de fichiers DVW de 4 Matchs.
    Sélectionnez un onglet dans le menu latéral pour commencer.
""")

@st.cache_data
def load_data():
    file_paths = glob.glob(os.path.join('data', '*.dvw'))

    if not file_paths:
        st.error("Aucun fichier .dvw trouvé dans le dossier 'data'.")
        return [], pd.DataFrame()

    all_plays, all_players = pd.DataFrame(), pd.DataFrame()

    for path in file_paths:
        try:
            dv = read_dv.DataVolley(path)
            match_day = dv.__dict__['match_info']['day'][0]

            df_plays = dv.get_plays()
            df_plays['match_day'] = match_day

            all_plays = pd.concat([all_plays, df_plays], ignore_index=True)
            all_players = pd.concat([all_players, dv.get_players()], ignore_index=True)
        except Exception as e:
            st.warning(f"Erreur lors du chargement du fichier {os.path.basename(path)}: {e}")

    players_df = all_players.drop_duplicates(subset=['player_id']).reset_index(drop=True)

    players = [
        Player(
            id_=row['player_id'],
            first_name=row['name'],
            last_name=row['lastname'],
            number=row['player_number'],
            df=all_plays[all_plays['player_id'] == row['player_id']],
            team=row.get('team')
        )
        for _, row in players_df.iterrows()
    ]

    return players, players_df

with st.spinner("Chargement des données..."):
    players, players_df = load_data()

# Sidebar général
with st.sidebar:
    st.subheader("Informations générales")
    if players:
        st.write(f"📊 **{len(players)}** joueurs au total")
        match_count = len(players[0].df['match_id'].unique()) if players[0].df is not None else 0
        st.write(f"🏐 **{match_count}** matchs analysés")
    else:
        st.warning("Aucune donnée disponible.")

# Menu latéral
menu_options = ["Réception", "Block", "Service", "Défense", "Attaque", "Joueur", "Autre Onglet (À venir)"]
selected_menu = st.sidebar.radio("Choisir un onglet", menu_options)
st.sidebar.markdown("---")

def unique_preserve_order(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

# Config des tabs "skill"
SKILL_TABS = {
    "Réception": {"skill": "Reception", "label": "réceptions"},
    "Block": {"skill": "Block", "label": "blocks"},
    "Service": {"skill": "Serve", "label": "service"},
    "Défense": {"skill": "Dig", "label": "défense"},
    "Attaque": {"skill": "Attack", "label": "attaque"},
}

# Affichage selon l'onglet sélectionné
if selected_menu in SKILL_TABS:
    config = SKILL_TABS[selected_menu]
    skill = config["skill"]
    label = config["label"]

    if players:
        categories = unique_preserve_order(Player.SKILL_EVAL_MAPPINGS.get(skill, {}).values())
        skill_comparison_tab(players, skill=skill, label=label, categories=categories)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

elif selected_menu == "Joueur":
    if players:
        player_evolution_tab(players)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

else:
    st.subheader("Fonctionnalité à venir")
    st.write("Cette section est en cours de développement.")
