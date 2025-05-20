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

def create_team_pie_charts(df: pd.DataFrame, categories: List[str], label: str = "actions") -> None: 
    """Displays pie charts for each team"""
    st.subheader("🧩 Category distribution by team")
    for _, row in df.iterrows():
        team = row["Team"]
        
        # Prepare standardized values
        values = []
        for cat in categories:
            percent_cat = f"% {cat}" if not cat.startswith("% ") else cat
            values.append(row.get(percent_cat, row.get(cat, 0)))
        
        pie = create_pie_chart(
            labels=categories,
            values=values,
            title=f"{team} - {int(row['Total Count'])} {label}"
        )
        st.plotly_chart(pie, use_container_width=True)
        
def create_evolution_chart(stats_df: pd.DataFrame, target: float, skill_labels: List[str], target_label: str = "% Perfect") -> go.Figure:
    """Creates a chart showing performance evolution over matches"""
    fig = go.Figure()

    # Add a trace for each category
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

    # Add target line
    fig.add_shape(
        type='line',
        x0=0,
        y0=target,
        x1=1,
        y1=target,
        xref="paper",
        line=dict(color="rgba(0,100,0,0.5)", width=2, dash="dash")
    )
    
    # Add annotations
    annotations = [
        dict(
            x=0.02, y=target + 2, xref="paper",
            text=f"Target: {target}%", showarrow=False,
            font=dict(color="rgba(0,100,0,0.8)", size=12)
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

def create_radar_chart(stats_df: pd.DataFrame, categories: List[str]) -> Tuple[Optional[go.Figure], List[float]]: 
    """Creates a radar chart of average performance by category"""
    if stats_df.empty:
        return None

    # Calculate means for each category
    means = [stats_df[col].mean() for col in categories]

    # Create radar chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=means, theta=categories, fill='toself', name='Average'))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=400
    )
    
    return fig, means

def display_radar_with_stats(stats_df: pd.DataFrame, categories: List[str]) -> None:
    """Displays a radar chart with average statistics"""
    if stats_df.empty:
        return
        
    fig, means = create_radar_chart(stats_df, categories)
    
    # Display chart and means side by side
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### Averages")
        for cat, val in zip(categories, means):
            st.markdown(f"**{cat}**: {val:.1f}%")

        # Calculate stability based on standard deviation
        if categories and categories[0] in stats_df.columns:
            stability = 100 - stats_df[categories[0]].std()
            st.markdown(f"**Stability**: {stability:.1f}%")