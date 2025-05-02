from player import *

class Team :
    """
    For each team calculate global scores :(attack, block, recep, def, passe, service) stat
    """

    def __init__(self, players : list, df):
        self.players = players
        self.df = df

    def perf_recep(self):
        """
        Passer par chaque df de joueurs ? ou df de l'équipe jsp, calculer le nb de recep total et de parfaite et donner le res
        """