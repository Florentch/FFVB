import pandas as pd 
import numpy as np

class Player : 
    """
    class Player : 
        Can be identified with unique id, an other informations seen on the init
        Calculate for each actions (attack, block, recep, def, passe, service) stat on %win %lost 
        
    """

    def __init__(self, id_, first_name, last_name, number, df, post = None, team = None):
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.post = post
        self.team = team

        self.df = df
        self.df_attack = df[df['skill'] == 'Attack']
        self.df_reception = df[df['skill'] == 'Reception']
        self.df_set = df[df['skill'] == 'Set']
        self.df_block = df[df['skill'] == 'Block']
        self.df_dig = df[df['skill'] == 'Dig']
        self.df_serve = df[df['skill'] == 'Serve']

    def recep_parfait(self):
        return len(self.df_reception[self.df_reception['evaluation_code'] == '#'])
    
    def recep_good(self):
        return len(self.df_reception[self.df_reception['evaluation_code'].isin(['/', '+'])])

    def recep_bad(self):
        return len(self.df_reception[self.df_reception['evaluation_code'].isin(['!', '-', '='])])

    def recep_fail(self):
        return len(self.df_reception[self.df_reception['evaluation_code'] == '='])
    
    def recep_total(self):
        return len(self.df_reception)

    def recep_precision(self):
        try:
            return round(((self.recep_parfait() + self.recep_good()) / self.recep_total()) * 100, 1)
        except ZeroDivisionError:
            return 0.0







    def perfect(self) -> int:
        n = len(self.df[self.df['evaluation_code'] == '#'])
        tot = len(self.df)
        print(f"perfect number : {n} and total actions : {tot}")
        return  n/ tot


