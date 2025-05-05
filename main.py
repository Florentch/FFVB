import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import streamlit as st
import pandas as pd
import numpy as np
import glob
import os

from player import Player
from datavolley import read_dv
from reception import reception_comparison_tab
from block import block_comparison_tab
from player_evolution import player_evolution_tab

# Configuration de la page dès le début
st.set_page_config(
    page_title="Analyse de Volleyball", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajout d'un titre et d'une description à l'application
st.title("📊 Analyse de Volleyball")
st.markdown("""
    Application d'analyse des données de volleyball extraites de fichiers DVW de 4 Matchs.
    Sélectionnez un onglet dans le menu latéral pour commencer.
""")

# Charger les données
@st.cache_data  # Cache pour améliorer les performances
def load_data():
    """
    Charge les données de tous les fichiers .dvw disponibles et crée les objets Player.
    
    Returns:
        tuple: (liste des objets Player, DataFrame de tous les joueurs)
    """
    # Lire tous les fichiers .dvw
    file_paths = glob.glob(os.path.join('data', '*.dvw'))
    
    if not file_paths:
        st.error("Aucun fichier .dvw trouvé dans le dossier 'data'.")
        return [], pd.DataFrame()
    
    all_plays = pd.DataFrame()
    all_players = pd.DataFrame()

    # Concaténer les données de tous les fichiers
    for path in file_paths:
        try:
            dv = read_dv.DataVolley(path)
            match_day = dv.__dict__['match_info']['day'][0]  # Récupération de la date du match

            df_plays = dv.get_plays()
            df_plays['match_day'] = match_day  # Ajouter la date du match

            df_players = dv.get_players()

            all_plays = pd.concat([all_plays, df_plays], ignore_index=True)
            all_players = pd.concat([all_players, df_players], ignore_index=True)
        except Exception as e:
            st.warning(f"Erreur lors du chargement du fichier {os.path.basename(path)}: {e}")

    # Supprimer les doublons de joueurs
    players_df = all_players.drop_duplicates(subset=['player_id']).reset_index(drop=True)

    # Créer les objets Player
    players = []
    for _, row in players_df.iterrows():
        player_df = all_plays[all_plays['player_id'] == row['player_id']]
        player = Player(
            id_=row['player_id'],
            first_name=row['name'],
            last_name=row['lastname'],
            number=row['player_number'],
            df=player_df,
            team=row.get('team')
        )
        players.append(player)
    
    return players, players_df

# Charger les données
with st.spinner("Chargement des données..."):
    players, players_df = load_data()

# Afficher des statistiques générales dans la barre latérale
with st.sidebar:
    st.subheader("Informations générales")
    if len(players) > 0:
        st.write(f"📊 **{len(players)}** joueurs au total")
        
        # Nombre de matchs
        match_count = len(players[0].df['match_id'].unique()) if players else 0
        st.write(f"🏐 **{match_count + 1}** matchs analysés")
    else:
        st.warning("Aucune donnée disponible.")

# Menu latéral pour la sélection de l'onglet
menu_options = ["Réception", "Block" , "Joueur", "Autre Onglet (À venir)"]  # À étendre avec d'autres onglets
selected_menu = st.sidebar.radio("Choisir un onglet", menu_options)

# Séparateur visuel
st.sidebar.markdown("---")

# En fonction de l'onglet sélectionné, afficher l'onglet correspondant
if selected_menu == "Réception":
    if len(players) > 0:
        reception_comparison_tab(players)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")
elif selected_menu == "Block":
    if len(players) > 0:
        block_comparison_tab(players)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

elif selected_menu == "Joueur":
    if len(players) > 0:
        player_evolution_tab(players)
    else:
        st.warning("Aucune donnée disponible pour l'analyse.")

else:
    st.subheader("Fonctionnalité à venir")
    st.write("Cette section est en cours de développement.")



