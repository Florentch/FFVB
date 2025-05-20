import pandas as pd
from typing import List, Dict, Optional, Union, Tuple

from player import Player
from utils import is_team_france_avenir

class Team:
    """Utility class for team statistics management."""
    
    @staticmethod
    def create_france_avenir_global_player(players: List[Player]) -> Player:
        """Creates a "global" player representing aggregated France Avenir team statistics."""
        fa_players = [p for p in players if is_team_france_avenir(p.team)]
        fa_combined_df = pd.concat([p.df for p in fa_players], ignore_index=True) if fa_players else pd.DataFrame()
        return Player(id_="fa_team", first_name="FRANCE", last_name="AVENIR", number="", df=fa_combined_df, team="France Avenir")
    
    @staticmethod
    def create_other_teams_global_player(players: List[Player]) -> Player:
        """Creates a "global" player representing aggregated statistics from teams other than France Avenir."""
        other_players = [p for p in players if not is_team_france_avenir(p.team)]
        other_combined_df = pd.concat([p.df for p in other_players], ignore_index=True) if other_players else pd.DataFrame()
        return Player(id_="other_team", first_name="AUTRES", last_name="ÉQUIPES", number="", df=other_combined_df, team="Autres Équipes")
    
    @staticmethod
    def create_team_global_player(players: List[Player], team_name: str, id_prefix: str = "team_") -> Optional[Player]:
        """Creates a "global" player representing aggregated statistics for a specific team."""
        team_players = [p for p in players if p.team == team_name]
        if not team_players:
            return None
            
        team_combined_df = pd.concat([p.df for p in team_players], ignore_index=True)
        return Player(
            id_=f"{id_prefix}{team_name.lower().replace(' ', '_')}",
            first_name=team_name.upper(),
            last_name="",
            number="",
            df=team_combined_df,
            team=team_name
        )
    
    @staticmethod
    def get_all_teams(players: List[Player]) -> List[str]:
        """Returns a list of all teams present in the player list."""
        return sorted(list(set(p.team for p in players if p.team)))
    
    @staticmethod
    def create_all_team_global_players(players: List[Player]) -> List[Player]:
        """Creates "global" players for each team in the data."""
        teams = Team.get_all_teams(players)
        return [Team.create_team_global_player(players, team) for team in teams if team]

    @staticmethod
    def get_all_best_players(players: List[Player], set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None, min_actions: int = 10) -> Dict[str, Dict[str, Union[Dict[str, Union[str, float, int]], float, None]]]:
        """Returns the best players for each skill and average efficiency."""
        skills = ["Attack", "Block", "Serve", "Reception", "Dig", "Set"]
        result = {
            'best_players': {},
            'average_efficiency': {}
        }
        
        for skill in skills:
            best_player_data = Player.get_best_players_by_skill(
                players, skill, set_moment, match_filter, set_filter, min_actions
            )
            
            if best_player_data:
                result['best_players'][skill] = {
                    'name': best_player_data['player'].get_full_name(),
                    'team': best_player_data['player'].team,
                    'efficiency': best_player_data['efficiency'],
                    'total_actions': best_player_data['total_actions']
                }
            else:
                result['best_players'][skill] = None
            
            avg_efficiency = Player.get_average_efficiency_by_skill(
                players, skill, set_moment, match_filter, set_filter, min_actions//2
            )
            
            result['average_efficiency'][skill] = avg_efficiency
        
        return result