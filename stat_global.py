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
                
            # Pour les passes, utiliser % Jouable comme première colonne
            first_label = "% Jouable" if skill == "Set" else skill_labels[0]
            last_label = skill_labels[-2]  # ex. "% Fautes"
                
            col_total = f"n {skill}"
            col_first = f"{skill}_{first_label}"
            col_last = f"{skill}_{last_label}"
            
            stats[col_total] = int(total)
            stats[col_first] = skill_stats.get(first_label, np.nan) if total >= MIN_ACTIONS else np.nan
            stats[col_last] = skill_stats.get(last_label, np.nan) if total >= MIN_ACTIONS else np.nan
        return stats
    
    # Ajouter d'abord les statistiques d'équipe France Avenir et autres équipes
    rows.append(get_player_stats(fa_team_player, "ÉQUIPE FRANCE AVENIR"))
    rows.append(get_player_stats(other_team_player, "AUTRES ÉQUIPES"))
    
    # Ajouter les statistiques des joueurs individuels de France Avenir
    for p in fa_players:
        rows.append(get_player_stats(p, f"{p.number} – {p.last_name} {p.first_name}"))
    
    return pd.DataFrame(rows).set_index("Joueur")


def style_global_df(df, team_rows=2):
    """
    Applique un style au DataFrame des statistiques globales.
    """
    # Constantes de couleur pour une meilleure lisibilité
    BG_TEAM = 'lightyellow'
    BG_BEST = 'lightgreen'
    BG_WORST = 'salmon'
    COLOR_BEST = 'darkgreen'
    COLOR_WORST = 'darkred'
    COLOR_NEUTRAL = 'black'
    
    labels_map = Player.get_skill_labels(with_percent=True)

    def highlight(col):
        """
        Applique un style de surlignage aux valeurs minimales et maximales d'une colonne.
        """
        name = col.name
        # Ignorer les colonnes non-numériques ou de total d'actions
        if col.dtype.kind not in 'biufc' or name.startswith('n '):
            # Pour les colonnes non-statistiques, on surligne quand même les lignes d'équipe
            return [f'background-color: {BG_TEAM}'] * team_rows + [''] * (len(col) - team_rows)
        
        # Déterminer si c'est une colonne d'évaluation négative (dernière)
        skill, label = name.split('_', 1) if '_' in name else (None, name)
        
        # Pour les passes, vérifier si c'est la colonne % Jouable ou % Erreur
        if skill == "Set":
            is_last = label == "% Erreur" or label == "% Fautes"
        else:
            is_last = skill in labels_map and label == labels_map[skill][-2]
        
        # Surligner toujours les lignes d'équipe en jaune
        result = [f'background-color: {BG_TEAM}'] * team_rows
        
        # Pour toutes les valeurs (équipes incluses), trouver min/max
        all_values = col.dropna()
        
        if all_values.empty:
            return [''] * len(col)
        
        min_val, max_val = all_values.min(), all_values.max()
        
        # Appliquer le style à toutes les lignes
        for i, v in enumerate(col):
            if i < team_rows:
                # Lignes d'équipe - fond jaune avec couleur d'évaluation en superposition
                if pd.isna(v):
                    result[i] = f'background-color: {BG_TEAM}'
                else:
                    # Ajouter un style d'évaluation par dessus le fond jaune
                    if is_last:  # Pour les colonnes d'erreur, inverser les couleurs
                        color = COLOR_BEST if v == min_val else COLOR_WORST if v == max_val else COLOR_NEUTRAL
                    else:  # Pour les colonnes positives
                        color = COLOR_BEST if v == max_val else COLOR_WORST if v == min_val else COLOR_NEUTRAL
                    result[i] = f'background-color: {BG_TEAM}; color: {color}'
            else:
                # Lignes des joueurs
                if pd.isna(v):
                    result.append('')
                else:
                    # Inverser les couleurs pour les évaluations négatives
                    if is_last:
                        result.append(f'background-color: {BG_BEST}' if v == min_val else
                                    f'background-color: {BG_WORST}' if v == max_val else '')
                    else:
                        result.append(f'background-color: {BG_BEST}' if v == max_val else
                                    f'background-color: {BG_WORST}' if v == min_val else '')
        return result

    # Format à 1 décimale pour les valeurs numériques
    formatter = {col: '{:.1f}' for col in df.select_dtypes(include=['float']).columns}
    
    return df.style.apply(highlight, axis=0).format(formatter, na_rep='-')


def global_stats_tab(players):
    """
    Affiche l'onglet Statistique globale pour l'équipe France Avenir.
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

    # Afficher d'abord les statistiques des équipes (toujours visible)
    team_df = df.iloc[:2]  # Première ligne = France Avenir, Deuxième ligne = Autres équipes
    team_styled = style_global_df(team_df, team_rows=2)
    st.dataframe(team_styled, use_container_width=True)
    
    # Puis afficher les données des joueurs individuels de France Avenir
    player_df = df.iloc[2:]  # Ignorer les 2 premières lignes (équipes)
    if not player_df.empty:
        player_styled = style_global_df(player_df, team_rows=0)
        st.dataframe(player_styled, use_container_width=True, height=500)