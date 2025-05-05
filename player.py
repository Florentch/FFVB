# player.py
import pandas as pd
import numpy as np

class Player:
    """
    Classe Player : représente un joueur et permet de calculer des statistiques spécifiques
    à partir des données de jeu extraites de fichiers DataVolley.
    """

    def __init__(self, id_, first_name, last_name, number, df, post=None, team=None):
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.post = post
        self.team = team
        self.df = df

        # DataFrames filtrés pour les différents types d'action
        self.df_reception = df[df['skill'] == 'Reception']

    # ======================
    # MÉTHODES - RÉCEPTION
    # ======================

    def get_reception_df(self, moment="Tout", match_filter=None):
        """
        Filtre le DataFrame des réceptions selon le moment du match et les identifiants de matchs.
        
        Args:
            moment (str): "Tout", "Début", "Milieu" ou "Fin"
            match_filter (list): Liste d'identifiants de matchs à inclure
            
        Returns:
            DataFrame: DataFrame filtré des réceptions
        """
        # Créer une copie pour éviter de modifier l'original
        df = self.df_reception.copy()
        
        # Appliquer le filtre de match si spécifié
        if match_filter is not None and len(match_filter) > 0:
            # Convertir en liste si ce n'est pas déjà le cas
            if not isinstance(match_filter, list):
                match_filter = [match_filter]
            
            # Filtrer le DataFrame
            df = df[df['match_id'].isin(match_filter)]

        # Appliquer le filtre de moment de jeu
        if moment == "Début":
            df = df[
                (df['home_team_score'] <= 10) & (df['visiting_team_score'] <= 10)
            ]
        elif moment == "Milieu":
            df = df[
                ((df['home_team_score'] > 10) & (df['home_team_score'] < 20)) &
                ((df['visiting_team_score'] > 10) & (df['visiting_team_score'] < 20))
            ]
        elif moment == "Fin":
            df = df[
                (df['home_team_score'] >= 20) | (df['visiting_team_score'] >= 20)
            ]

        return df

    def get_reception_stats(self, moment="Tout", match_filter=None):
        """
        Calcule les statistiques de réception pour ce joueur.
        
        Args:
            moment (str): "Tout", "Début", "Milieu" ou "Fin"
            match_filter (list): Liste d'identifiants de matchs à inclure
            
        Returns:
            dict: Dictionnaire des statistiques de réception
        """
        df = self.get_reception_df(moment, match_filter)
        total = len(df)
        
        # Si aucune réception, retourner des statistiques à zéro
        if total == 0:
            return {
                "% Parfaites": 0.0,
                "Parfaites": 0,
                "Bonnes": 0,
                "Mauvaises": 0,
                "Ratées": 0,
                "Total": 0
            }

        stats = {
            "% Parfaites": round(((parfaites / total) * 100), 1) if total else 0.0,
            "Parfaites": len(df[df['evaluation_code'] == '#']),
            "Bonnes": len(df[df['evaluation_code'].isin(['/', '+'])]),
            "Mauvaises": len(df[df['evaluation_code'].isin(['!', '-'])]),
            "Ratées": len(df[df['evaluation_code'] == '=']),
            "Total": total
        }
        return stats