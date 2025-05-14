import pandas as pd
from player import Player
from utils import is_team_france_avenir

class Team:
    """
    Classe utilitaire pour la gestion des statistiques d'équipe.
    
    Cette classe fournit des méthodes pour créer des "joueurs globaux" représentant 
    les statistiques agrégées d'une équipe entière ou de plusieurs équipes.
    """
    
    @staticmethod
    def create_france_avenir_global_player(players):
        """
        Crée un joueur "global" représentant les statistiques agrégées de l'équipe France Avenir.
        """
        fa_players = [p for p in players if is_team_france_avenir(p.team)]
        fa_combined_df = pd.concat([p.df for p in fa_players], ignore_index=True) if fa_players else pd.DataFrame()
        return Player(id_="fa_team", first_name="FRANCE", last_name="AVENIR", number="", df=fa_combined_df, team="France Avenir")
    
    @staticmethod
    def create_other_teams_global_player(players):
        """
        Crée un joueur "global" représentant les statistiques agrégées des équipes autres que France Avenir.
        """
        other_players = [p for p in players if not is_team_france_avenir(p.team)]
        other_combined_df = pd.concat([p.df for p in other_players], ignore_index=True) if other_players else pd.DataFrame()
        return Player(id_="other_team", first_name="AUTRES", last_name="ÉQUIPES", number="", df=other_combined_df, team="Autres Équipes")
    
    @staticmethod
    def create_team_global_player(players, team_name, id_prefix="team_"):
        """
        Crée un joueur "global" représentant les statistiques agrégées d'une équipe spécifique.
        """
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
    def get_all_teams(players):
        """
        Récupère la liste de toutes les équipes présentes dans la liste des joueurs.
        """
        return sorted(list(set(p.team for p in players if p.team)))
    
    @staticmethod
    def create_all_team_global_players(players):
        """
        Crée des joueurs "globaux" pour chaque équipe présente dans les données.
        """
        teams = Team.get_all_teams(players)
        return [Team.create_team_global_player(players, team) for team in teams if team]