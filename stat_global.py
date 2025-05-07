import pandas as pd
import streamlit as st
from player import Player
import numpy as np

MIN_ACTIONS = 5


def build_global_stats_df(players):
    """
    Retourne un DataFrame indexé par joueur (numéro - nom prénom). Pour chaque skill,
    affiche le nombre d'actions (Total), la première et la dernière évaluation en pourcentage.
    """
    rows = []
    labels_map = Player.get_skill_labels(with_percent=True)
    for p in players:
        if p.team != "France Avenir":
            continue
        base = {"Joueur": f"{p.number} – {p.last_name} {p.first_name}"}
        for skill in Player.SKILL_EVAL_MAPPINGS:
            stats = p.get_skill_stats(skill)
            total = stats.get("Total", 0)
            skill_labels = labels_map.get(skill, [])
            if not skill_labels:
                continue
            first_label = skill_labels[0]    # ex. "% Parfaite"
            last_label = skill_labels[-1]    # ex. "% Fautes"
            col_total = f"n {skill}"
            col_first = f"{skill}_{first_label}"
            col_last = f"{skill}_{last_label}"
            base[col_total] = int(total)
            base[col_first] = stats.get(first_label, np.nan) if total >= MIN_ACTIONS else np.nan
            base[col_last] = stats.get(last_label, np.nan) if total >= MIN_ACTIONS else np.nan
        rows.append(base)
    df = pd.DataFrame(rows).set_index("Joueur")
    return df


def style_global_df(df):
    """
    Applique un style: pour chaque colonne, surligne en vert le max et en rouge le min,
    sauf pour la dernière évaluation de chaque skill où c'est inversé. Les colonnes _n
    (nombre d'actions) ne sont pas stylées.
    """
    labels_map = Player.get_skill_labels(with_percent=True)

    def highlight(col):
        name = col.name
        if col.dtype.kind not in 'biufc' or name.startswith('n '):
            return [''] * len(col)
        skill, label = name.split('_', 1) if '_' in name else (None, name)
        is_last = skill in labels_map and label == labels_map[skill][-1]
        valid = col.dropna()
        if valid.empty:
            return [''] * len(col)
        min_val, max_val = valid.min(), valid.max()
        result = []
        for v in col:
            if pd.isna(v):
                result.append('')
            else:
                if is_last:
                    result.append('background-color: lightgreen' if v == min_val else
                                  'background-color: salmon' if v == max_val else '')
                else:
                    result.append('background-color: lightgreen' if v == max_val else
                                  'background-color: salmon' if v == min_val else '')
        return result

    return df.style.apply(highlight, axis=0)


def global_stats_tab(players):
    """
    Affiche l'onglet Statistique globale pour l'équipe France Avenir, avec pour chaque skill :
    le nombre d'actions, la première et la dernière évaluation (%), avec couleurs inversées pour la dernière.
    """
    st.subheader("Statistique globale – Équipe France Avenir")
    st.markdown(f"- Seuil minimal d'actions pour inclusion : {MIN_ACTIONS} ({MIN_ACTIONS} actions)")
    st.markdown("- ""-"" signifie que le joueur n'a pas atteint le seuil minimal d'actions.")

    df = build_global_stats_df(players)
    if df.empty:
        st.warning("Aucun joueur de France Avenir avec suffisamment d'actions pour afficher des statistiques.")
        return

    styled = style_global_df(df).format(na_rep='-')
    st.dataframe(styled, use_container_width=True)