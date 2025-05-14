import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from player import Player

def create_bar_chart(df, categories, name_col="Nom", height=500):
    """
    Crée un graphique à barres groupées pour comparer des entités
    """
    fig = go.Figure()
    for _, row in df.iterrows():
        entity_name = row[name_col]
        values = []
        for cat in categories:
            # Détecter intelligemment les colonnes avec préfixe %
            percent_cat = f"% {cat}" if not cat.startswith("% ") else cat
            values.append(row.get(percent_cat, row.get(cat, 0)))
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            name=entity_name,
            textposition='auto'
        ))

    fig.update_layout(
        barmode='group', 
        xaxis_title="Catégories", 
        yaxis_title="Pourcentage (%)", 
        height=height, 
        template="plotly_white"
    )
    return fig

def create_pie_chart(labels, values, title="", hole=0.4, height=400):
    """
    Crée un graphique en camembert
    """
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=hole
        )
    ])
    fig.update_layout(
        title_text=title, 
        height=height
    )
    return fig

def create_team_pie_charts(df, categories, label="actions"):
    """
    Affiche des graphiques en camembert pour chaque équipe
    """
    st.subheader("🧩 Répartition des catégories par équipe")
    for _, row in df.iterrows():
        team = row["Équipe"]
        
        # Préparation des valeurs uniformisées
        values = []
        for cat in categories:
            percent_cat = f"% {cat}" if not cat.startswith("% ") else cat
            values.append(row.get(percent_cat, row.get(cat, 0)))
        
        pie = create_pie_chart(
            labels=categories,
            values=values,
            title=f"{team} - {int(row['Nbre Total'])} {label}"
        )
        st.plotly_chart(pie, use_container_width=True)
        
def create_evolution_chart(stats_df, target, skill_labels, target_label="% Parfaite"):
    """
    Crée un graphique d'évolution des performances au fil des matchs
    """
    fig = go.Figure()

    # Ajouter une trace pour chaque catégorie
    colors = ["green", "blue", "orange", "red", "purple", "gray"]
    for label, color in zip(skill_labels, colors):
        if label in stats_df.columns:
            fig.add_trace(go.Scatter(
                x=stats_df['match_day'],
                y=stats_df[label],
                mode='lines+markers',
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=7)
            ))

    # Ajouter la ligne d'objectif
    fig.add_shape(
        type='line',
        x0=0,
        y0=target,
        x1=1,
        y1=target,
        xref="paper",
        line=dict(color="rgba(0,100,0,0.5)", width=2, dash="dash")
    )
    
    # Ajouter les annotations
    annotations = [
        dict(
            x=0.02, y=target + 2, xref="paper",
            text=f"Objectif: {target}%", showarrow=False,
            font=dict(color="rgba(0,100,0,0.8)", size=12)
        )
    ]

    # Ajouter le nombre d'actions par match
    for i, row in stats_df.iterrows():
        annotations.append(dict(
            x=row['match_day'], y=5,
            text=f"N={row['total']}", showarrow=False,
            font=dict(size=9)
        ))

    fig.update_layout(annotations=annotations)
    return fig

def create_radar_chart(stats_df, categories):
    """
    Crée un graphique radar des performances moyennes par catégorie
    """
    if stats_df.empty:
        return None

    # Calculer les moyennes pour chaque catégorie
    means = [stats_df[col].mean() for col in categories]

    # Créer le graphique radar
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=means, theta=categories, fill='toself', name='Moyenne'))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=400
    )
    
    return fig, means

def display_radar_with_stats(stats_df, categories):
    """
    Affiche un graphique radar avec les statistiques moyennes
    """
    if stats_df.empty:
        return
        
    fig, means = create_radar_chart(stats_df, categories)
    
    # Afficher le graphique et les moyennes côte à côte
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### Moyennes")
        for cat, val in zip(categories, means):
            st.markdown(f"**{cat}**: {val:.1f}%")

        # Calcul de la stabilité basée sur l'écart-type
        if categories and categories[0] in stats_df.columns:
            stability = 100 - stats_df[categories[0]].std()
            st.markdown(f"**Stabilité**: {stability:.1f}%")