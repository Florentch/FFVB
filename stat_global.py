import pandas as pd
import streamlit as st
from player import Player
import numpy as np

from config import MIN_ACTIONS, SKILL_EVAL_MAPPINGS
from utils import is_team_france_avenir
from team import Team


def build_global_stats_df(players):
    """
    Construit un DataFrame contenant les statistiques globales des joueurs.
    
    Pour chaque joueur et chaque compétence, affiche:
    - Le nombre total d'actions
    - Le pourcentage de la première évaluation (généralement positive)
    - Le pourcentage de la dernière évaluation (généralement négative)
    
    Inclut également des lignes pour les statistiques globales de l'équipe France Avenir
    et des autres équipes.
    """
    rows = []
    labels_map = Player.get_skill_labels(with_percent=True)
    
    # Créer les joueurs globaux pour France Avenir et les autres équipes
    fa_team_player = Team.create_france_avenir_global_player(players)
    other_team_player = Team.create_other_teams_global_player(players)
    
    # Filtrer uniquement les joueurs de France Avenir
    fa_players = [p for p in players if is_team_france_avenir(p.team)]
    
    # Fonction helper pour obtenir les statistiques d'un joueur ou d'une équipe
    def get_player_stats(player, player_name):
        stats = {"Joueur": player_name}
        for skill in SKILL_EVAL_MAPPINGS:
            skill_stats = player.get_skill_stats(skill)
            total = skill_stats.get("Total", 0)
            skill_labels = labels_map.get(skill, [])
            if not skill_labels:
                continue
            first_label = skill_labels[0]    # ex. "% Parfaite"
            last_label = skill_labels[-1]    # ex. "% Fautes"
            col_total = f"n {skill}"
            col_first = f"{skill}_{first_label}"
            col_last = f"{skill}_{last_label}"
            stats[col_total] = int(total)
            stats[col_first] = skill_stats.get(first_label, np.nan) if total >= MIN_ACTIONS else np.nan
            stats[col_last] = skill_stats.get(last_label, np.nan) if total >= MIN_ACTIONS else np.nan
        return stats
    
    # Ajouter d'abord les statistiques d'équipe France Avenir
    rows.append(get_player_stats(fa_team_player, "ÉQUIPE FRANCE AVENIR"))
    
    # Ajouter ensuite les statistiques des autres équipes
    rows.append(get_player_stats(other_team_player, "AUTRES ÉQUIPES"))
    
    # Ajouter les statistiques des joueurs individuels de France Avenir
    for p in fa_players:
        rows.append(get_player_stats(p, f"{p.number} – {p.last_name} {p.first_name}"))
    
    df = pd.DataFrame(rows).set_index("Joueur")
    return df


def style_global_df(df, team_rows=2):
    """
    Applique un style au DataFrame des statistiques globales.
    
    Pour chaque colonne de pourcentage:
    - Surligne en vert la valeur maximale (ou minimale pour les évaluations négatives)
    - Surligne en rouge la valeur minimale (ou maximale pour les évaluations négatives)
    - Surligne en jaune les lignes des statistiques globales des équipes
    
    Args:
        df: DataFrame à styliser
        team_rows: Nombre de lignes d'équipe à surligner en jaune (par défaut 2)
    """
    labels_map = Player.get_skill_labels(with_percent=True)

    def highlight(col):
        """
        Applique un style de surlignage aux valeurs minimales et maximales d'une colonne.
        Pour les colonnes d'évaluation négative (dernière), les couleurs sont inversées.
        Les premières lignes (statistiques d'équipe) sont toujours surlignées en jaune.
        """
        name = col.name
        # Ignorer les colonnes non-numériques ou de total d'actions
        if col.dtype.kind not in 'biufc' or name.startswith('n '):
            # Pour les colonnes non-statistiques, on surligne quand même les lignes d'équipe
            return ['background-color: lightyellow'] * team_rows + [''] * (len(col) - team_rows)
        
        # Déterminer si c'est une colonne d'évaluation négative (dernière)
        skill, label = name.split('_', 1) if '_' in name else (None, name)
        is_last = skill in labels_map and label == labels_map[skill][-1]
        
        # Surligner toujours les lignes d'équipe en jaune
        result = ['background-color: lightyellow'] * team_rows
        
        # Pour toutes les valeurs (équipes incluses), trouver min/max
        all_values = col.dropna()
        
        if all_values.empty:
            return [''] * len(col)
        
        min_val, max_val = all_values.min(), all_values.max()
        
        # Appliquer le style à toutes les lignes, y compris les équipes
        for i, v in enumerate(col):
            if i < team_rows:
                # Lignes d'équipe - fond jaune avec couleur d'évaluation en superposition
                if pd.isna(v):
                    result[i] = 'background-color: lightyellow'
                else:
                    # Ajouter un style d'évaluation par dessus le fond jaune
                    if is_last:
                        result[i] = 'background-color: lightyellow; color: ' + ('darkgreen' if v == min_val else 
                                     'darkred' if v == max_val else 'black')
                    else:
                        result[i] = 'background-color: lightyellow; color: ' + ('darkgreen' if v == max_val else 
                                     'darkred' if v == min_val else 'black')
            else:
                # Lignes des joueurs
                if pd.isna(v):
                    result.append('')
                else:
                    # Inverser les couleurs pour les évaluations négatives
                    if is_last:
                        result.append('background-color: lightgreen' if v == min_val else
                                    'background-color: salmon' if v == max_val else '')
                    else:
                        result.append('background-color: lightgreen' if v == max_val else
                                    'background-color: salmon' if v == min_val else '')
        return result

    # Format à 1 décimale pour les valeurs numériques
    formatter = {col: '{:.1f}' for col in df.select_dtypes(include=['float']).columns}
    
    return df.style.apply(highlight, axis=0).format(formatter, na_rep='-')


def global_stats_tab(players):
    """
    Affiche l'onglet Statistique globale pour l'équipe France Avenir, avec pour chaque skill :
    le nombre d'actions, la première et la dernière évaluation (%), avec couleurs inversées pour la dernière.
    Inclut des lignes surlignées en jaune pour les statistiques globales des équipes.
    """
    st.subheader("Statistique globale – Équipe France Avenir")
    st.markdown(f"- Seuil minimal d'actions pour inclusion : {MIN_ACTIONS} ({MIN_ACTIONS} actions)")
    st.markdown("- ""-"" signifie que le joueur n'a pas atteint le seuil minimal d'actions.")
    st.markdown("- Les deux premières lignes (surlignées en jaune) représentent les statistiques globales pour l'équipe France Avenir et les autres équipes.")
    st.markdown("- Le vert indique les meilleures valeurs et le rouge les moins bonnes (couleurs inversées pour les taux d'erreur).")

    df = build_global_stats_df(players)
    if df.empty:
        st.warning("Aucun joueur de France Avenir avec suffisamment d'actions pour afficher des statistiques.")
        return

    # Afficher d'abord les statistiques des équipes séparément (toujours visible)
    team_df = df.iloc[:2]  # Première ligne = France Avenir, Deuxième ligne = Autres équipes
    team_styled = style_global_df(team_df, team_rows=2)
    st.dataframe(team_styled, use_container_width=True)
    
    # Puis afficher les données des joueurs individuels de France Avenir
    player_df = df.iloc[2:]  # Ignorer les 2 premières lignes (équipes)
    if not player_df.empty:
        player_styled = style_global_df(player_df, team_rows=0)
        st.dataframe(player_styled, use_container_width=True, height=500)