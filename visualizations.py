import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional, Union, Tuple

from player import Player

def create_bar_chart(df: pd.DataFrame, categories: List[str], name_col: str = "Name", height: int = 500) -> go.Figure:
    """Creates a grouped bar chart to compare entities"""
    fig = go.Figure()
    for _, row in df.iterrows():
        entity_name = row[name_col]
        values = []
        for cat in categories:
            # Intelligently detect columns with % prefix
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
        xaxis_title="Categories", 
        yaxis_title="Percentage (%)", 
        height=height, 
        template="plotly_white"
    )
    return fig

def create_pie_chart(labels: List[str], values: List[float], title: str = "", hole: float = 0.4, height: int = 400) -> go.Figure:
    """Creates a pie chart with customizable options"""
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


def create_team_pie_charts_with_ranking(df: pd.DataFrame, categories: List[str], label: str = "actions") -> None: 
    """Displays pie charts for each team with efficiency and error rankings."""
    st.subheader("Category distribution by team")
    
    # Calculer les classements pour % Efficacité et % Erreur
    eff_ranking = _calculate_ranking(df, "% Efficacité", ascending=False)
    err_ranking = _calculate_ranking(df, "% Erreur", ascending=True)
    total_teams = len(df)
    
    for _, row in df.iterrows():
        team = row["Team"]
        
        # Préparer les valeurs standardisées
        values = []
        for cat in categories:
            percent_cat = f"% {cat}" if not cat.startswith("% ") else cat
            values.append(row.get(percent_cat, row.get(cat, 0)))
        
        # Créer le graphique en donut
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pie = create_pie_chart(
                labels=categories,
                values=values,
                title=f"{team} - {int(row['Total Count'])} {label}"
            )
            st.plotly_chart(pie, use_container_width=True)
        
        with col2:
            _display_team_ranking_info(row, team, eff_ranking, err_ranking, total_teams)

def _get_rank_color(rank: int, total_teams: int) -> tuple:
    """Retourne la couleur et couleur de fond basée sur le classement."""
    if total_teams <= 1:
        return "#2e8b57", "#f0f8ff"
    
    normalized_rank = (rank - 1) / (total_teams - 1)
    
    if normalized_rank <= 0.33:  # Top 33% - Vert
        return "#2e8b57", "#f0fff0"
    elif normalized_rank <= 0.66:  # Milieu 33% - Orange
        return "#ff8c00", "#fff8dc"
    else:  # Bottom 33% - Rouge
        return "#dc143c", "#fff0f0"

def _calculate_ranking(df: pd.DataFrame, column: str, ascending: bool = False) -> Dict[str, int]:
    """Calcule le classement des équipes pour une colonne donnée."""
    if column not in df.columns:
        return {}

    sorted_df = df.sort_values(by=column, ascending=ascending).reset_index(drop=True)
    ranking = {}
    
    for idx, row in sorted_df.iterrows():
        ranking[row["Team"]] = idx + 1
    
    return ranking

def _display_team_ranking_info(row: pd.Series, team: str, eff_ranking: Dict[str, int], err_ranking: Dict[str, int], total_teams: int) -> None:
    """Affiche les informations de classement pour une équipe avec couleurs."""
    st.markdown("<div style='text-align: center;'><h4> Classements</h4></div>", unsafe_allow_html=True)
    
    if "% Efficacité" in row.index and team in eff_ranking:
        eff_value = row["% Efficacité"]
        eff_rank = eff_ranking[team]
        color, bg_color = _get_rank_color(eff_rank, total_teams)
        
        st.markdown(
            f"<div style='text-align: center; padding: 8px; background-color: {bg_color}; border-radius: 8px; margin: 5px 0;'>"
            f"<strong>🎯 Efficacité</strong><br>"
            f"<span style='font-size: 18px; color: {color};'>{eff_value:.1f}%</span><br>"
            f"<small style='color: {color}; font-weight: bold;'>Rang: {eff_rank}/{total_teams}</small>"
            f"</div>", 
            unsafe_allow_html=True
        )
    
    if "% Erreur" in row.index and team in err_ranking:
        err_value = row["% Erreur"]
        err_rank = err_ranking[team]
        color, bg_color = _get_rank_color(err_rank, total_teams)
        
        st.markdown(
            f"<div style='text-align: center; padding: 8px; background-color: {bg_color}; border-radius: 8px; margin: 5px 0;'>"
            f"<strong>⚠️ Erreur</strong><br>"
            f"<span style='font-size: 18px; color: {color};'>{err_value:.1f}%</span><br>"
            f"<small style='color: {color}; font-weight: bold;'>Rang: {err_rank}/{total_teams}</small>"
            f"</div>", 
            unsafe_allow_html=True
        )
        
def create_evolution_chart(stats_df: pd.DataFrame, target: float, skill_labels: List[str], error_threshold: float = 15, target_label: str = "% Perfect") -> go.Figure:
    """Creates a chart showing performance evolution over matches"""
    fig = go.Figure()

    # Add a trace for each category
    for label in skill_labels:
        if label in stats_df.columns:
            if "Efficacité" in label:
                color = "green"
            elif "Erreur" in label:
                color = "red"
            else:
                color = "blue"
                
            fig.add_trace(go.Scatter(
                x=stats_df['match_day'],
                y=stats_df[label],
                mode='lines+markers',
                name=label,
                line=dict(color=color, width=2),
                marker=dict(size=7)
            ))

    # Add efficiency target line (green)
    fig.add_shape(
        type='line',
        x0=0,
        y0=target,
        x1=1,
        y1=target,
        xref="paper",
        line=dict(color="green", width=2, dash="dash")
    )
    
    # Add error threshold line (red)
    fig.add_shape(
        type='line',
        x0=0,
        y0=error_threshold,
        x1=1,
        y1=error_threshold,
        xref="paper",
        line=dict(color="red", width=2, dash="dash")
    )
    
    # Add annotations
    annotations = [
        dict(
            x=0.02, y=target + 2, xref="paper",
            text=f"Obj. Efficacité: {target}%", showarrow=False,
            font=dict(color="green", size=12)
        ),
        dict(
            x=0.02, y=error_threshold - 2, xref="paper",
            text=f"Obj. Erreur: {error_threshold}%", showarrow=False,
            font=dict(color="red", size=12)
        )
    ]

    # Add action count per match
    for i, row in stats_df.iterrows():
        annotations.append(dict(
            x=row['match_day'], y=5,
            text=f"N={row['total']}", showarrow=False,
            font=dict(size=9)
        ))

    fig.update_layout(annotations=annotations)
    return fig

def create_radar_chart(stats_df: pd.DataFrame, categories: List[str], eff_threshold: float = 25, error_threshold: float = 15) -> Tuple[Optional[go.Figure], List[float]]: 
    """Creates a radar chart of average performance by category with objective lines"""
    if stats_df.empty:
        return None, []

    # Calculate means for each category
    means = [stats_df[col].mean() for col in categories if col in stats_df.columns]
    
    # Prepare objectives for each category
    objectives = []
    for cat in categories:
        if "Efficacité" in cat:
            objectives.append(eff_threshold)
        elif "Erreur" in cat:
            objectives.append(error_threshold)
        else:
            objectives.append(50)  # Default neutral value for other metrics

    # Create radar chart
    fig = go.Figure()
    
    # Add actual performance
    fig.add_trace(go.Scatterpolar(
        r=means, 
        theta=categories, 
        fill='toself', 
        name='Performance Moyenne',
        line=dict(color='blue')
    ))
    
    # Add objectives
    fig.add_trace(go.Scatterpolar(
        r=objectives, 
        theta=categories, 
        fill=None, 
        name='Objectifs',
        line=dict(color='red', dash='dash', width=3),
        marker=dict(size=8, color='red')
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=400
    )
    
    return fig, means

def display_radar_with_stats(stats_df: pd.DataFrame, categories: List[str], eff_threshold: float = 25, error_threshold: float = 15) -> None:
    """Displays a radar chart with average statistics and objectives"""
    if stats_df.empty:
        return
    
    # Filter categories to only show % Efficacité and % Erreur
    filtered_categories = [cat for cat in categories if "Efficacité" in cat or "Erreur" in cat]
    
    if not filtered_categories:
        return
        
    fig, means = create_radar_chart(stats_df, filtered_categories, eff_threshold, error_threshold)
    
    if fig is None:
        return
    
    # Display chart and stats side by side
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### Moyennes vs Objectifs")
        for i, cat in enumerate(filtered_categories):
            if i < len(means):
                val = means[i]
                if "Efficacité" in cat:
                    obj = eff_threshold
                    delta = val - obj
                elif "Erreur" in cat:
                    obj = error_threshold
                    delta = obj - val  # For errors, lower is better
                
                st.markdown(f"**{cat}**: {val:.1f}%")
                st.markdown(f"*Objectif: {obj}% (Δ{delta:+.1f}%)*")

        # Calculate stability based on standard deviation of first available metric
        if filtered_categories and filtered_categories[0] in stats_df.columns:
            stability = 100 - stats_df[filtered_categories[0]].std()
            st.markdown(f"**Stabilité**: {stability:.1f}%")