import streamlit as st
import pandas as pd
from datetime import datetime


def unique_preserve_order(seq: list) -> list:
    """Returns a list without duplicates while preserving the order of elements"""
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def create_selector(items: list, title: str, session_key: str, format_func: callable = None, default_selection: list = None) -> list:
    """Creates a generic selector with quick select options"""
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    col1, col2 = area.columns([3, 1])
    
    # "All" button handling
    with col2:
        area.write(f"Options {title}")
        if area.button("All", key=f"btn_all_{session_key}"):
            st.session_state[session_key] = items
    
    # Selector handling
    with col1:
        # Initialize session variable if needed
        if session_key not in st.session_state:
            default_items = items[:3] if len(items) > 3 else items
            st.session_state[session_key] = default_selection if default_selection is not None else default_items
        
        # Filter to keep only valid elements
        valid_selected = [item for item in st.session_state[session_key] if item in items]
        
        # Create the selector
        selected = area.multiselect(
            f"Select {title}",
            options=items,
            format_func=format_func or (lambda x: x),
            default=valid_selected
        )
        
        # Update session
        st.session_state[session_key] = selected
    
    # Warning if no selection
    if not selected:
        area.warning(f"⚠️ Please select at least one {title.lower()} to display statistics.")
    
    return selected

def get_match_data(players: list) -> pd.DataFrame:
    """Retrieves and sorts match data from players"""
    match_data, match_ids_set = [], set()
    
    for p in players:
        for match_id in p.df['match_id'].dropna().unique():
            if match_id in match_ids_set:
                continue
                
            match_ids_set.add(match_id)
            match_rows = p.df[p.df['match_id'] == match_id]
            
            if match_rows.empty:
                continue
                
            row = match_rows.iloc[0]
            match_day = row.get('match_day', '')
            home_team = row.get('home_team', 'Team A')[:3]
            visiting_team = row.get('visiting_team', 'Team B')[:3]
            
            match_data.append({
                'match_id': match_id,
                'match_day': match_day,
                'match_label': f"{home_team} vs {visiting_team} - {match_day}"
            })
    
    # Sort matches by date if possible
    match_df = pd.DataFrame(match_data)
    if not match_df.empty and 'match_day' in match_df.columns:
        try:
            match_df['date_for_sort'] = pd.to_datetime(match_df['match_day'], format='%d/%m/%Y', errors='coerce')
            match_df = match_df.sort_values(by='date_for_sort', ascending=False)
        except Exception:
            pass
    
    return match_df

def get_match_selector(players: list, selected_matches: list = None) -> list:
    """Creates a match selector with quick options"""
    # Retrieve sorted match data
    match_df = get_match_data(players)
    match_ids = list(match_df['match_id'].unique())
    match_labels = match_df.set_index('match_id')['match_label'].to_dict()
    
    # Initialize session if needed
    if 'selected_matches' not in st.session_state:
        st.session_state.selected_matches = match_ids if selected_matches is None else selected_matches
    
    # Create the selector
    is_pinned = st.session_state.get('pin_selections', True)
    area = st.sidebar if is_pinned else st
    col1, col2 = area.columns([3, 1])
    
    with col2:
        area.write("Quick options")
        if area.button("All", key="btn_all_matches"):
            st.session_state.selected_matches = match_ids
    
    with col1:
        selected_matches = area.multiselect(
            "Filter by match", 
            options=match_ids,
            format_func=lambda x: match_labels.get(x, str(x)),
            default=st.session_state.selected_matches
        )
        st.session_state.selected_matches = selected_matches
    
    return selected_matches

def player_selector(players: list, skill: str, moment: str, selected_matches: list, set_filter: list = None) -> pd.DataFrame:
    """Displays an enhanced player selector with team sorting options"""
    # Organize players by team
    teams = {}
    for p in players:
        team_name = p.team or "No Team"
        if team_name not in teams:
            teams[team_name] = []
        teams[team_name].append(p)
    
    # Dictionary to access players by name
    player_dict = {f"{p.first_name} {p.last_name}": p for p in players}
    all_names = list(player_dict.keys())
    
    # Display format by team
    options = {
        f"{p.first_name} {p.last_name}": f"{(p.team or 'No Team')[:3]} - {p.first_name} {p.last_name}"
        for p in players
    }
    
    # Create player selector
    format_func = lambda x: options.get(x, x)
    selected_names = create_selector(
        all_names, "players", "selected_players", format_func, 
        default_selection=all_names[:3] if all_names else []
    )
    
    if not selected_names:
        return None
    
    # Get statistics by player
    data = []
    for name in selected_names:
        p = player_dict[name]
        stats = p.get_skill_stats(skill, moment, match_filter=selected_matches, set_filter=set_filter)
        if stats["Total"] > 0:
            row = {"Name": name, "Team": p.team or "No Team"}
            row.update(stats)
            data.append(row)
    
    if not data:
        is_pinned = st.session_state.get('pin_selections', True)
        area = st.sidebar if is_pinned else st
        area.info(f"No data for selected players and matches.")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def aggregate_team_stats(players: list, skill: str, moment: str, match_filter: list, set_filter: list = None) -> dict:
    """Aggregates statistics for all players in a team"""
    # Get all possible categories for this skill
    categories = set()
    for p in players:
        stats = p.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)
        categories.update([k for k in stats.keys() if k != "Total"])
    
    # Initialize team statistics dictionary
    team_stats = {k: 0 for k in list(categories) + ["Total"]}
    
    # Aggregate statistics for all players
    for p in players:
        stats = p.get_skill_stats(skill, moment, match_filter=match_filter, set_filter=set_filter)
        for k, v in stats.items():
            team_stats[k] += v
    
    return team_stats

def team_selector(players: list, skill: str, moment: str, selected_matches: list, set_filter: list = None) -> pd.DataFrame:
    """Displays a team selector with quick selection options"""
    teams = unique_preserve_order([p.team for p in players if p.team])
    
    # Create team selector
    selected_teams = create_selector(teams, "teams", "selected_teams", default_selection=teams)
    
    if not selected_teams:
        return None
    
    # Filter players by team
    filtered_players = [p for p in players if p.team in selected_teams]
    
    # Aggregate statistics by team
    data = []
    for team in selected_teams:
        team_players = [p for p in filtered_players if p.team == team]
        stats = aggregate_team_stats(team_players, skill, moment, selected_matches, set_filter)
        
        if stats["Total"] > 0:
            row = {"Team": team, "Total Count": stats["Total"]}
            
            # Add percentages
            for category, value in stats.items():
                if category != "Total":
                    key = category if category.startswith("% ") else f"% {category}"
                    row[key] = round(value / stats["Total"] * 100, 1)
            data.append(row)
    
    if not data:
        is_pinned = st.session_state.get('pin_selections', True)
        area = st.sidebar if is_pinned else st
        area.info(f"No data for selected teams and matches.")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def filter_players_by_criteria(players: list, min_actions: int = 5, skill: str = None) -> list:
    """Filters players based on various criteria"""        
    if skill:
        return [p for p in players if len(p.get_action_df(skill)) > min_actions]
        
    all_skills = ['Reception', 'Block', 'Serve', 'Attack', 'Dig']
    return [p for p in players if sum(len(p.get_action_df(s)) for s in all_skills) > min_actions]

def filter_players_with_data(players: list, match_filter: list = None, skill: str = None, set_moment: str = None, moment: str = None, set_filter: list = None, min_actions: int = 4) -> list:
    """Filters players with sufficient data for analysis."""
    if skill is None:
        return players
    
    effective_moment = set_moment or moment
    
    return [
        p for p in players 
        if p.get_action_df(skill, set_moment=effective_moment, match_filter=match_filter, set_filter=set_filter) is not None
        and len(p.get_action_df(skill, set_moment=effective_moment, match_filter=match_filter, set_filter=set_filter)) > min_actions
    ]