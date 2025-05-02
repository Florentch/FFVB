import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==================== DONNÉES SIMULÉES ====================
np.random.seed(42)

equipe_A = "Dragons"
equipe_B = "Phoenix"
joueurs_A = [f"Joueur A{i+1}" for i in range(6)]
joueurs_B = [f"Joueur B{i+1}" for i in range(6)]
tous_joueurs = joueurs_A + joueurs_B
equipes = [equipe_A] * 6 + [equipe_B] * 6

data = {
    'nom': tous_joueurs,
    'equipe': equipes,
    'service_acc': np.random.randint(30, 95, size=12),
    'service_ace': np.random.randint(0, 20, size=12),
    'service_fault': np.random.randint(5, 30, size=12),
    'attaque_pts': np.random.randint(20, 150, size=12),
    'attaque_acc': np.random.randint(30, 95, size=12),
    'attaque_err': np.random.randint(5, 40, size=12),
    'recep_parfaite': np.random.randint(10, 80, size=12),
    'recep_err': np.random.randint(5, 30, size=12),
    'recep_tot': np.random.randint(50, 200, size=12),
}

data['service_total'] = data['service_ace'] + data['service_fault'] + np.random.randint(30, 100, size=12)
data['recep_acc'] = np.round((data['recep_parfaite'] / data['recep_tot']) * 100, 1)
data['efficacite_globale'] = np.round((data['service_acc'] + data['attaque_acc'] + data['recep_acc']) / 3, 1)

df = pd.DataFrame(data)

# ==================== FONCTIONS DE VUE ====================

def vue_globale():
    st.subheader("Vue Globale des Statistiques")
    fig = px.bar(df, x='nom', y='efficacite_globale', color='equipe', 
                 title="Efficacité Globale des Joueurs",
                 labels={'efficacite_globale': 'Efficacité (%)'})
    st.plotly_chart(fig)
    st.dataframe(df[[
        'nom', 'equipe', 'service_acc', 'service_ace', 'attaque_pts',
        'attaque_acc', 'recep_acc', 'efficacite_globale'
    ]])

def vue_comparaison(skill):
    st.subheader(f"Comparaison par Compétence : {skill.capitalize()}")
    joueurs_selectionnes = st.multiselect("Sélectionner jusqu'à 6 joueurs", tous_joueurs, default=tous_joueurs[:2], max_selections=6)

    if not joueurs_selectionnes:
        st.warning("Sélectionnez au moins un joueur.")
        return

    df_sel = df[df['nom'].isin(joueurs_selectionnes)]

    if skill == 'service':
        y_cols = ['service_acc', 'service_ace', 'service_fault', 'service_total']
    elif skill == 'attaque':
        y_cols = ['attaque_acc', 'attaque_pts', 'attaque_err']
    else:
        y_cols = ['recep_acc', 'recep_parfaite', 'recep_err', 'recep_tot']

    df_melt = df_sel.melt(id_vars=['nom'], value_vars=y_cols, var_name='Statistique', value_name='Valeur')
    fig = px.bar(df_melt, x='Statistique', y='Valeur', color='nom', barmode='group')
    st.plotly_chart(fig)

# ==================== INTERFACE ====================
st.title("Statistiques Volleyball")
onglet = st.sidebar.radio("Vue", ["Vue Globale", "Comparaison Service", "Comparaison Attaque", "Comparaison Réception"])

if onglet == "Vue Globale":
    vue_globale()
elif onglet == "Comparaison Service":
    vue_comparaison('service')
elif onglet == "Comparaison Attaque":
    vue_comparaison('attaque')
else:
    vue_comparaison('reception')
